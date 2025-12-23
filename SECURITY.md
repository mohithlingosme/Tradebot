# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in Finbot, please report it to us as follows:

1. **Do not** create a public GitHub issue for the vulnerability.
2. Email security@finbot.com with details of the vulnerability.
3. Include:
   - A clear description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes

We will acknowledge receipt within 48 hours and provide a more detailed response within 7 days indicating our next steps.

## Secret Rotation

### JWT Secrets
- JWT secrets should be rotated every 90 days
- Use cryptographically secure random strings (256 bits)
- Update both `JWT_SECRET` environment variable and any cached tokens

### Database Credentials
- Database passwords should be rotated quarterly
- Use strong, randomly generated passwords (20+ characters)
- Update `DATABASE_URL` environment variable
- Restart all services after rotation

### API Keys
- Third-party API keys should be rotated immediately if compromised
- Monitor for unusual usage patterns
- Use environment variables for all API keys

### Finbot-Specific Secrets
- **POSTGRES_PASSWORD**: Rotate database password quarterly. Update in GitHub Secrets and .env file.
- **SECRET_KEY**: Rotate Flask secret key every 90 days. Generate new 256-bit random string.
- **GRAFANA_ADMIN_PASSWORD**: Rotate Grafana admin password quarterly.
- **DOCKER_USERNAME/PASSWORD**: Rotate Docker registry credentials annually or if compromised.
- **SSH Keys**: Rotate SSH private keys used for deployment annually.
- **API Keys for Environments**: Rotate DEV_API_KEY, PAPER_API_KEY, LIVE_API_KEY quarterly.

To rotate secrets:
1. Generate new secure values
2. Update GitHub Secrets in repository settings
3. Update .env file locally (if applicable)
4. Redeploy services
5. Verify functionality
6. Remove old secrets from any backups or logs

## Security Best Practices

- Never commit secrets to version control
- Use environment variables for all configuration
- Regularly update dependencies
- Run security scans on code and containers
- Monitor logs for suspicious activity
- Use HTTPS in production
- Implement rate limiting on API endpoints

## Responsible Disclosure

We kindly ask that you:

- Give us reasonable time to fix the issue before public disclosure
- Avoid accessing or modifying user data
- Respect the confidentiality of the report

We will credit researchers who responsibly disclose vulnerabilities (with permission).
