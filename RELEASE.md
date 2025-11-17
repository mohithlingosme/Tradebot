# Release Process

This document outlines the process for releasing new versions of the Market Data Ingestion System.

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

## Release Checklist

### Pre-Release
- [ ] All CI checks pass on `main` branch
- [ ] Code is reviewed and approved
- [ ] CHANGELOG.md is updated with new features, fixes, and breaking changes
- [ ] Version number is updated in relevant files
- [ ] Documentation is updated
- [ ] Tests pass locally and in CI
- [ ] Docker images build successfully

### Release Steps
1. **Create Release Branch**
   ```bash
   git checkout -b release/v1.2.3
   ```

2. **Update Version Numbers**
   - Update `__version__` in `market_data_ingestion/__init__.py`
   - Update version in `pyproject.toml` (if applicable)
   - Update version in `setup.py` (if applicable)

3. **Update CHANGELOG.md**
   ```markdown
   ## [1.2.3] - 2024-01-15

   ### Added
   - New feature description

   ### Fixed
   - Bug fix description

   ### Changed
   - Breaking change description

   ### Removed
   - Deprecated feature removal
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "Release v1.2.3"
   ```

5. **Create Git Tag**
   ```bash
   git tag -a v1.2.3 -m "Release version 1.2.3"
   git push origin v1.2.3
   ```

6. **Merge to Main**
   ```bash
   git checkout main
   git merge release/v1.2.3
   git push origin main
   ```

7. **Create GitHub Release**
   - Go to [Releases](https://github.com/your-org/finbot/releases)
   - Click "Create a new release"
   - Select the tag `v1.2.3`
   - Copy changelog content as release notes
   - Publish release

8. **Build and Publish Docker Images**
   ```bash
   # Build images
   docker build -t your-registry/market-data-ingestion:v1.2.3 .

   # Push to registry
   docker push your-registry/market-data-ingestion:v1.2.3
   docker tag your-registry/market-data-ingestion:v1.2.3 your-registry/market-data-ingestion:latest
   docker push your-registry/market-data-ingestion:latest
   ```

9. **Publish to PyPI** (if applicable)
   ```bash
   python -m build
   twine upload dist/*
   ```

### Post-Release
- [ ] Monitor for issues in production
- [ ] Update deployment manifests with new version
- [ ] Notify stakeholders of new release
- [ ] Start next development cycle

## Hotfix Releases

For critical bug fixes:

1. Create hotfix branch from the release tag
   ```bash
   git checkout -b hotfix/v1.2.4 v1.2.3
   ```

2. Apply fix and update version to 1.2.4

3. Follow release steps above

## Rollback Process

If a release needs to be rolled back:

1. **Immediate Rollback**
   - Revert the merge commit on main
   - Deploy previous version
   - Investigate root cause

2. **Tag Rollback**
   - Create a new tag pointing to previous commit
   - Update deployment to use rollback tag

## Release Cadence

- **Major releases**: As needed for breaking changes
- **Minor releases**: Monthly or when significant features are ready
- **Patch releases**: As needed for critical fixes

## Communication

- **Internal**: Slack channel notification
- **External**: GitHub release notes
- **Customers**: Release notes via email/newsletter if applicable

## Changelog Format

```markdown
## [1.2.3] - 2024-01-15

### Added
- New adapter for Provider X (#123)
- Rate limiting for all adapters (#124)

### Fixed
- Memory leak in WebSocket connections (#125)
- Incorrect timestamp parsing in Alpha Vantage adapter (#126)

### Changed
- Updated FastAPI to version 0.100.0 (BREAKING: requires Python 3.8+)
- Changed default database from SQLite to PostgreSQL

### Removed
- Deprecated `old_function()` - use `new_function()` instead

### Security
- Fixed API key exposure in logs (#127)
```

## Version File Locations

Update version in these files:
- `market_data_ingestion/__init__.py`
- `pyproject.toml` (if using modern Python packaging)
- `setup.py` (if using legacy packaging)
- `Dockerfile` (ARG VERSION)
- Documentation files

## Testing Releases

Before releasing:
- [ ] Run full test suite
- [ ] Test Docker build
- [ ] Test database migrations
- [ ] Test CLI commands
- [ ] Test API endpoints
- [ ] Test with sample data
- [ ] Test upgrade from previous version
