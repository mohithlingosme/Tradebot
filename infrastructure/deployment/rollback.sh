#!/bin/bash

# Finbot Rollback Script
# This script provides rollback functionality for Finbot deployments

set -e

# Configuration
APP_NAME="finbot"
NAMESPACE="${NAMESPACE:-default}"
ROLLBACK_TAG="${ROLLBACK_TAG:-latest}"
DEPLOYMENT_NAME="${DEPLOYMENT_NAME:-finbot-backend}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get current deployment version
get_current_version() {
    if command_exists kubectl; then
        kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "unknown"
    else
        echo "kubectl not found, cannot determine current version"
        exit 1
    fi
}

# Function to get previous deployment version
get_previous_version() {
    if command_exists kubectl; then
        # Get rollout history and find the previous revision
        kubectl rollout history deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE" --to-revision=0 2>/dev/null | grep -E "Revision [0-9]+" | tail -2 | head -1 | awk '{print $2}' || echo "unknown"
    else
        echo "kubectl not found, cannot determine previous version"
        exit 1
    fi
}

# Function to perform rollback
perform_rollback() {
    local target_version="$1"

    log_info "Rolling back $DEPLOYMENT_NAME to version: $target_version"

    if command_exists kubectl; then
        # Perform the rollback
        kubectl set image deployment/"$DEPLOYMENT_NAME" "$APP_NAME=$target_version" -n "$NAMESPACE"

        # Wait for rollout to complete
        kubectl rollout status deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE" --timeout=300s

        log_info "Rollback completed successfully"
    else
        log_error "kubectl not found, cannot perform rollback"
        exit 1
    fi
}

# Function to rollback to previous version
rollback_to_previous() {
    log_info "Rolling back to previous version..."

    if command_exists kubectl; then
        kubectl rollout undo deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE"
        kubectl rollout status deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE" --timeout=300s
        log_info "Rollback to previous version completed"
    else
        log_error "kubectl not found, cannot perform rollback"
        exit 1
    fi
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Finbot Rollback Script

OPTIONS:
    -h, --help              Show this help message
    -n, --namespace NS      Kubernetes namespace (default: default)
    -d, --deployment DEP    Deployment name (default: finbot-backend)
    -t, --tag TAG           Rollback to specific image tag
    -p, --previous          Rollback to previous version
    --dry-run               Show what would be done without executing

EXAMPLES:
    $0 --previous                           # Rollback to previous version
    $0 --tag v1.2.3                         # Rollback to specific tag
    $0 --namespace production --previous    # Rollback in production namespace
    $0 --dry-run --previous                 # Show rollback plan

EOF
}

# Main script logic
main() {
    local dry_run=false
    local rollback_to_previous=false
    local target_tag=""

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -d|--deployment)
                DEPLOYMENT_NAME="$2"
                shift 2
                ;;
            -t|--tag)
                target_tag="$2"
                shift 2
                ;;
            -p|--previous)
                rollback_to_previous=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Validate inputs
    if [[ "$rollback_to_previous" == true && -n "$target_tag" ]]; then
        log_error "Cannot specify both --previous and --tag"
        exit 1
    fi

    if [[ "$rollback_to_previous" == false && -z "$target_tag" ]]; then
        log_error "Must specify either --previous or --tag"
        exit 1
    fi

    # Show current status
    local current_version
    current_version=$(get_current_version)
    log_info "Current deployment version: $current_version"

    if [[ "$dry_run" == true ]]; then
        log_info "DRY RUN MODE - No changes will be made"

        if [[ "$rollback_to_previous" == true ]]; then
            local prev_version
            prev_version=$(get_previous_version)
            log_info "Would rollback to previous version: $prev_version"
        else
            log_info "Would rollback to tag: $target_tag"
        fi

        exit 0
    fi

    # Confirm rollback
    echo
    log_warn "This will rollback the $DEPLOYMENT_NAME deployment in namespace $NAMESPACE"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Rollback cancelled"
        exit 0
    fi

    # Perform rollback
    if [[ "$rollback_to_previous" == true ]]; then
        rollback_to_previous
    else
        perform_rollback "$target_tag"
    fi

    # Verify rollback
    local new_version
    new_version=$(get_current_version)
    log_info "New deployment version: $new_version"

    # Run health checks
    log_info "Running post-rollback health checks..."
    # Add your health check commands here
    # Example: curl -f http://your-health-endpoint/health || log_error "Health check failed"

    log_info "Rollback process completed"
}

# Run main function
main "$@"
