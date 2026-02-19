#!/usr/bin/env python3
"""
Script to generate secure secret keys for Finbot.

Usage:
    python scripts/generate_secret_key.py

This script generates:
- SECRET_KEY for Flask/FastAPI sessions
- JWT_SECRET_KEY for JWT token signing
- JWT_REFRESH_SECRET_KEY for JWT refresh token signing
"""

import secrets
import string


def generate_secure_key(length: int = 32) -> str:
    """Generate a cryptographically secure hex string."""
    return secrets.token_hex(length)


def generate_alphanumeric_key(length: int = 50) -> str:
    """Generate a cryptographically secure alphanumeric string."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


if __name__ == "__main__":
    print("=" * 60)
    print("Finbot Secure Key Generator")
    print("=" * 60)
    print()
    print("Add these to your .env file:")
    print()
    print(f"SECRET_KEY={generate_secure_key(32)}")
    print(f"JWT_SECRET_KEY={generate_secure_key(32)}")
    print(f"JWT_REFRESH_SECRET_KEY={generate_secure_key(32)}")
    print()
    print("=" * 60)
    print("Or use these one-liners to generate keys:")
    print()
    print("Python:")
    print('  python -c "import secrets; print(secrets.token_hex(32))"')
    print()
    print("OpenSSL:")
    print('  openssl rand -hex 32')
    print("=" * 60)
