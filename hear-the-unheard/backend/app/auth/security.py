from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.core.config import get_settings

settings = get_settings()

ALGORITHM = "HS256"

# NOTE: uses the `bcrypt` package directly rather than passlib's
# CryptContext. passlib 1.7.4's bcrypt backend-detection code
# (detect_wrap_bug) throws on bcrypt>=4.1 due to an upstream
# incompatibility (passlib is effectively unmaintained) — hit this for
# real when this file was first written and tested, see docs/STATUS.md.
# bcrypt truncates at 72 bytes silently if not handled; we raise instead
# so a user's actual password never gets silently truncated/weakened.
_MAX_BCRYPT_BYTES = 72


def hash_password(plain_password: str) -> str:
    pw_bytes = plain_password.encode("utf-8")
    if len(pw_bytes) > _MAX_BCRYPT_BYTES:
        raise ValueError(f"Password must be at most {_MAX_BCRYPT_BYTES} bytes")
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(subject: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Raises jose.JWTError on an invalid/expired token — callers should catch it."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
