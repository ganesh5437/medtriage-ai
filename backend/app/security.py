"""
security.py — password hashing, JWT issue/verify, and basic input
sanitization (gap-fixes: auth register, input sanitization).
"""
import re
import time
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    password = password[:72]
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRY_HOURS)
    payload = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])


_TAG_RE = re.compile(r"<[^>]+>")


def sanitize_text(text: str) -> str:
    """Strip HTML/script tags from user-entered text before storing/rendering."""
    return _TAG_RE.sub("", text).strip()
