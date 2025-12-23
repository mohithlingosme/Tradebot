# Secret Removal and GitHub Secrets Migration TODO

## Completed Tasks
- [x] Create .env.example with secret placeholders
- [x] Update docker-compose.yml to use ${POSTGRES_PASSWORD} instead of hardcoded value
- [x] Update check_password.py to use env var for stored hash
- [x] Verify no hardcoded secrets remain (grep check passed)
- [x] Confirm secret-scan workflow exists
- [x] Confirm rotation instructions in SECURITY.md
- [x] Fix check_password.py to actually use STORED_HASH env var

## Next Steps
- [ ] Set up GitHub Secrets in repository settings for POSTGRES_PASSWORD, SECRET_KEY, GRAFANA_ADMIN_PASSWORD, etc.
- [ ] Create .env file locally with actual values
- [ ] Test docker-compose up to ensure services start correctly
- [ ] Run secret-scan workflow to verify
