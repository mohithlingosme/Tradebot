# MVP Authentication Implementation TODO

## Backend
- [x] Update backend/api/auth.py: Use env vars for JWT, add hash_password/verify_password helpers, fix get_current_user to use Session, add UserResponse model
- [x] Update backend/app/main.py: Fix login to use .identifier, update response to include user info, make /auth/me sync, add CORS with CORS_ORIGINS env

## Frontend
- [x] Update frontend/src/api.ts: Add 401 interceptor for logout, add getCurrentUser function
- [x] Update frontend/src/App.tsx: Add auth context for user state and route guards

## Tests
- [x] Create tests/test_auth.py: Add tests for login success/fail, /auth/me, inactive user block

## Config
- [x] Update .env.example: Add JWT and CORS env vars

## Verification
- [x] Run pytest -q
- [x] Run npm run build (frontend)
- [x] Manual login test
