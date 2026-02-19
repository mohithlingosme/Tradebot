# Security & Deployment Configuration Plan for Finbot

## Task Overview
Secure the Finbot algorithmic trading system by moving from hardcoded credentials to secret-based configuration.

---

## TODO List

### Phase 1: GitHub Secrets & CI/CD Security

- [ ] 1.1 List all environment variables that should be in GitHub Secrets
- [ ] 1.2 Create secret-scan.yml GitHub Action workflow
- [ ] 1.3 Update ci-cd.yml to map GitHub Secrets into jobs

### Phase 2: Local Environment Configuration

- [ ] 2.1 Create .env.example template file
- [ ] 2.2 Provide Python snippet to generate SECRET_KEY

### Phase 3: Docker Orchestration Validation

- [ ] 3.1 Fix hardcoded credentials in infrastructure/docker-compose.yml
- [ ] 3.2 Provide terminal commands to validate and start services

### Phase 4: Verification Workflow

- [ ] 4.1 Create Smoke Test procedure

---

## Detailed Information Gathered

### Environment Variables Found

#### docker-compose.yml (root):
- POSTGRES_PASSWORD
- POSTGRES_USER (finbot)
- POSTGRES_DB (finbot)
- SECRET_KEY
- GRAFANA_ADMIN_PASSWORD

#### infrastructure/docker-compose.yml:
- POSTGRES_PASSWORD: finbot123 (HARDCODED!)
- DATABASE_URL: postgresql://finbot:finbot123@... (HARDCODED!)
- ALPHAVANTAGE_API_KEY
- KITE_API_KEY
- KITE_API_SECRET

#### backend/app/core/config.py:
- DATABASE_URL
- JWT_SECRET_KEY
- JWT_REFRESH_SECRET_KEY
- JWT_ALGORITHM
- JWT_ACCESS_TOKEN_EXPIRE_MINUTES
- JWT_REFRESH_TOKEN_EXPIRE_DAYS
- BCRYPT_ROUNDS
- CORS_ORIGINS
- RATE_LIMIT_REQUESTS
- RATE_LIMIT_WINDOW_MINUTES
- SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD
- REDIS_URL
- EXECUTION_MODE
- PAPER_STARTING_CASH
- SLIPPAGE_BPS
- BROKERAGE_FLAT, BROKERAGE_BPS
- PAPER_ENFORCE_MARKET_HOURS
- ENABLE_RISK_ENFORCEMENT
- ENABLE_FORCE_SQUARE_OFF
- MAX_DAILY_LOSS_INR, MAX_DAILY_LOSS_PCT
- MAX_POSITION_VALUE_INR, MAX_POSITION_QTY
- MAX_GROSS_EXPOSURE_INR, MAX_NET_EXPOSURE_INR
- MAX_OPEN_ORDERS
- CUTOFF_TIME

### Current GitHub Secrets (from ci-cd.yml):
- DOCKER_USERNAME
- DOCKER_PASSWORD
- ENV_FILE
- REGISTRY_URL
- HOST
- USERNAME
- PRIVATE_KEY

### Missing GitHub Secrets:
- POSTGRES_PASSWORD
- POSTGRES_USER
- SECRET_KEY
- JWT_SECRET_KEY
- JWT_REFRESH_SECRET_KEY
- GRAFANA_ADMIN_PASSWORD
- ALPHAVANTAGE_API_KEY
- KITE_API_KEY
- KITE_API_SECRET
- POLYGON_API_KEY (for future)
- BINANCE_API_KEY (for future)
- BINANCE_SECRET_KEY (for future)

### Files to Edit:
1. .github/workflows/secret-scan.yml (CREATE)
2. .github/workflows/ci-cd.yml (UPDATE)
3. .env.example (CREATE)
4. infrastructure/docker-compose.yml (FIX HARDCODED CREDS)
