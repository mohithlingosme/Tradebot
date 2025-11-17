"""Utilities for encrypting and decrypting PII fields."""

from __future__ import annotations

import base64
import os
from cryptography.fernet import Fernet

_raw_key = os.getenv("PII_FERNET_KEY")
if not _raw_key:
    _raw_key = base64.urlsafe_b64encode(os.urandom(32)).decode()

fernet = Fernet(_raw_key)


def encrypt(value: str) -> str:
    """Encrypt a plaintext value."""
    token = fernet.encrypt(value.encode("utf-8"))
    return token.decode("utf-8")


def decrypt(value: str) -> str:
    """Decrypt a PII field."""
    return fernet.decrypt(value.encode("utf-8")).decode("utf-8")
