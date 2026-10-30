# SPDX-License-Identifier: Apache-2.0
"""Password hashing and signed access-token helpers."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from container_api.config import settings

_password_hash = PasswordHash.recommended()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _password_hash.verify(password, password_hash)


def create_access_token(subject: str) -> tuple[str, int]:
    ttl = settings.access_token_ttl_minutes * 60
    now = datetime.now(UTC)
    claims = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(seconds=ttl),
        "jti": str(uuid4()),
        "type": "access",
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=ALGORITHM), ttl


def decode_access_token(token: str) -> str | None:
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    subject = claims.get("sub")
    if claims.get("type") != "access" or not isinstance(subject, str):
        return None
    return subject
