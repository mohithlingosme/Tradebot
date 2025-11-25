# Staging Environment Verification Checklist

This document outlines steps to verify the backend staging environment after deployment.

## Endpoints to Check

### 1. Health Check

- Endpoint: `GET /health`
- Expected: HTTP 200, JSON with status info and timestamp

Example curl command:
```
curl -v http://<staging-backend-url>/health
```

### 2. Metrics Endpoint

- Endpoint: `GET /metrics`
- Expected: HTTP 200, Prometheus-style metrics text output

Example curl command:
```
curl -v http://<staging-backend-url>/metrics
```

### 3. Logs Endpoint

- Endpoint: `GET /logs`
- Requires: Admin JWT token in Authorization header
- Supports query parameters:
  - `limit` (default 100, max 500)
  - `level` (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - `since` ISO8601 datetime string
  - `until` ISO8601 datetime string

Example curl command (replace `<TOKEN>` and `<staging-backend-url>`):
```
curl -v -H "Authorization: Bearer <TOKEN>" "http://<staging-backend-url>/logs?limit=20&level=ERROR"
```

### Notes

- Use a valid admin token obtained via `/auth/login`.
- Verify that logs returned are structured, filtered according to parameters.
- Check that no sensitive data such as passwords or tokens appear in log fields (masked).
- Test edge cases with invalid or expired tokens to verify security.

---

Please follow this checklist after deploying to staging to confirm health, metrics, and logging functionality.
