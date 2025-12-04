# Path and Resource Issues TODO

## 1. Use absolute paths for test fixtures and logs
- [ ] Review all test files for relative path usage
- [ ] Update any test files using relative paths to use absolute paths
- [ ] Ensure logs directory creation uses absolute paths

## 2. Fix environment variable expansion in config files
- [ ] Verify `_expand_env_vars` implementation in market_data_ingestion/src/settings.py
- [ ] Check other config files for consistent environment variable handling
- [ ] Ensure all config files properly expand ${VAR_NAME} patterns

## 3. Document expected environment variables in CONTRIBUTING.md
- [ ] Collect all environment variables used across the codebase
- [ ] Add comprehensive environment variables section to CONTRIBUTING.md
- [ ] Include descriptions, defaults, and usage examples
