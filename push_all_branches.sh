#!/usr/bin/env bash
set -euo pipefail

# Usage:
# ./push_all_branches.sh [remote-name] [remote-url-if-you-want-to-add-remote]
# Examples:
# ./push_all_branches.sh                 # uses 'origin' and expects it to exist
# ./push_all_branches.sh origin https://github.com/username/repo.git

REMOTE="${1:-origin}"
REMOTE_URL="${2:-}"

# Safety: don't run outside a git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: Not inside a git repository. cd into your repo and retry."
  exit 1
fi

ORIG_BRANCH="$(git symbolic-ref --short HEAD || echo '')"
echo "Current branch: ${ORIG_BRANCH:-(detached or unknown)}"

# Add remote if missing (requires REMOTE_URL passed as second arg)
if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  if [ -z "$REMOTE_URL" ]; then
    echo "ERROR: Remote '$REMOTE' not found and no URL provided."
    echo "Provide the remote URL as the second argument, e.g.:"
    echo "./push_all_branches.sh origin https://github.com/username/repo.git"
    exit 2
  fi
  echo "Adding remote '$REMOTE' -> $REMOTE_URL"
  git remote add "$REMOTE" "$REMOTE_URL"
fi

echo "Fetching from $REMOTE..."
git fetch "$REMOTE" --prune

# Helper: attempt safe push for a branch (pull --rebase if non-fast-forward)
safe_push_branch() {
  local branch="$1"
  echo
  echo "-----> Processing branch: $branch"
  # Ensure branch exists locally
  if ! git show-ref --verify --quiet "refs/heads/$branch"; then
    echo "  Skipping $branch (no local branch found)."
    return
  fi

  # Checkout branch (detached HEADs will be avoided by checking ref)
  git checkout "$branch"

  # If remote has the branch, try rebase to incorporate remote commits,
  # otherwise we'll just push the local branch as new remote branch.
  if git ls-remote --exit-code --heads "$REMOTE" "$branch" >/dev/null 2>&1; then
    echo "  Remote branch exists. Pulling with rebase to avoid non-fast-forward..."
    # If pull --rebase fails due to conflicts, user must resolve manually.
    if ! git pull --rebase "$REMOTE" "$branch"; then
      echo "  WARNING: git pull --rebase had conflicts on branch $branch."
      echo "  Resolve conflicts, run 'git rebase --continue' then 'git push $REMOTE $branch'."
      return
    fi
  fi

  # Push and set upstream if not already set
  if git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1; then
    # upstream exists for current branch (only if current branch has upstream)
    git push "$REMOTE" "$branch" || echo "  Push failed for $branch (see message above)."
  else
    # set upstream
    git push -u "$REMOTE" "$branch" || echo "  Push failed for $branch (see message above)."
  fi
}

# Push main or master first (if present)
for primary in main master; do
  if git show-ref --verify --quiet "refs/heads/$primary"; then
    safe_push_branch "$primary"
    break
  fi
done

# Push every local branch
ALL_BRANCHES=$(git for-each-ref --format='%(refname:short)' refs/heads/)
for b in $ALL_BRANCHES; do
  # skip main/master since already handled
  if [ "$b" = "main" ] || [ "$b" = "master" ]; then
    continue
  fi
  safe_push_branch "$b"
done

# Push tags
echo
echo "Pushing tags..."
git push --tags "$REMOTE" || echo "  Tags push failed (maybe none exist)."

# Return to original branch
if [ -n "$ORIG_BRANCH" ]; then
  git checkout "$ORIG_BRANCH"
fi

echo
echo "Done. All local branches processed. Verify remote repository to confirm."
