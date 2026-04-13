"""Email verification codes (hashed at rest)."""

from __future__ import annotations

import hashlib
import hmac
import secrets

from django.conf import settings
from django.utils import timezone

CODE_LENGTH = 6


def hash_verification_code(code: str) -> str:
    msg = f"v1:{code}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()


def generate_numeric_code() -> str:
    n = secrets.randbelow(10**CODE_LENGTH)
    return f"{n:0{CODE_LENGTH}d}"


def verification_expires_at():
    from datetime import timedelta

    return timezone.now() + timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS)


def code_matches_stored(code: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_verification_code(code), stored_hash)
