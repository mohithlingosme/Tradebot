# TODO: Fix Testing and CI/CD Issues for BlackboxAI Finbot

## Overview
This TODO list addresses the comprehensive issues outlined in `testingissues.md` for automated testing and CI/CD workflow improvements.

## Critical Fixes (High Priority)

### 1. CI/CD Workflow Updates
- [ ] Update `.github/workflows/ci.yml` to use Python 3.12
- [ ] Add yamllint to CI workflow for YAML validation
- [ ] Pin Node.js version in CI for frontend consistency
- [ ] Add pre-flight checks in CI for environment and dependencies
- [ ] Run safety audit (`scripts/safety_audit.py`) in CI for all deploys
- [ ] Add fail-fast steps in CI to surface errors early

### 2. Environment and Dependencies
- [ ] Create `.env.example` with all required environment variables
- [ ] Update requirements to use pandas-ta instead of TA-Lib as primary indicator library
- [ ] Document exact Python/Node/npm versions in README and verify in CI
- [ ] Ensure Docker usage for TA-Lib when needed, with fallback instructions

### 3. Test Fixes and Coverage
- [ ] Fix failing integration tests for log endpoints (500 errors when store unavailable)
- [ ] Add missing E2E tests for full trading workflows in `tests/e2e/`
- [ ] Complete scenario/end-to-end tests for critical trading workflows
- [ ] Add robust error handling and edge cases in all tests
- [ ] Mock external API responses consistently and document expected results

### 4. Path and Resource Issues
- [ ] Use absolute paths for test fixtures and logs
- [ ] Fix environment variable expansion in config files
- [ ] Document expected environment variables in CONTRIBUTING.md

### 5. Documentation Updates
- [ ] Update docs/env_setup.md with Python 3.12 requirements
- [ ] Document TA-Lib installation alternatives (Docker, pandas-ta)
- [ ] Add troubleshooting section for common CI/CD failures

## Implementation Order
1. Start with CI/CD workflow fixes (critical for automation)
2. Environment setup and dependencies
3. Test fixes and additions
4. Documentation updates

## Testing Checklist
- [ ] Run full test suite locally with Python 3.12
- [ ] Verify CI workflows pass with new configurations
- [ ] Test E2E scenarios manually before automation
- [ ] Validate safety audit script integration

## Notes
- All changes should maintain backward compatibility where possible
- Use Docker for complex dependencies to avoid OS-specific issues
- Ensure all fixes are tested in CI before marking complete
