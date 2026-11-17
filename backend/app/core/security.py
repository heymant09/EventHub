from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
import jwt
from uuid import uuid4

from app.core.config import settings


password_hash = PasswordHash.recommended()


def create_access_token(data: dict) -> str:

    to_encode = data.copy()

    now = datetime.now(timezone.utc)

    expire = now + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "iat": now,
        "exp": expire,
        "jti": str(uuid4()),
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt


def hash_password(password: str) -> str:
    """Convert a plain-text password into a secure hash."""
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """Check whether a password matches its stored hash."""
    return password_hash.verify(plain_password, hashed_password)