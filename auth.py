from datetime import UTC, datetime, timedelta

import jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from config import settings
from typing import Any

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token")

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)

def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_duration)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(  # type: ignore[reportUnknownMemberType]
        payload=to_encode,
        key=settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm
    )

    return encoded_jwt

def verify_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode( # type: ignore[reportUnknownMemberType]
            jwt=token,
            key=settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub"]}
        )
        return payload.get("sub")
    except jwt.InvalidTokenError:
        return None