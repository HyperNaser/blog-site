from datetime import UTC, datetime, timedelta

import jwt
from fastapi.security import OAuth2PasswordBearer

from config import settings
from typing import Any, Annotated
from fastapi import Depends
from exceptions import UnauthorizedCredentialsException

from sqlalchemy.ext.asyncio import AsyncSession
from services import user_service

import models
from database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token")

def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_duration
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(  # type: ignore[reportUnknownMemberType]
        payload=to_encode,
        key=settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )

    return encoded_jwt


def verify_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(  # type: ignore[reportUnknownMemberType]
            jwt=token,
            key=settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub"]},
        )
        return payload.get("sub")
    except jwt.InvalidTokenError:
        return None

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> models.User:
    user_id = verify_access_token(token)
    
    if user_id is None:
        raise UnauthorizedCredentialsException(detail="Invalid or expired token")

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise UnauthorizedCredentialsException(detail="Invalid or expired token")
    
    user = await user_service.get_user_by_id(db, user_id_int)
    
    if not user:
        raise UnauthorizedCredentialsException(detail="User not found")
    
    return user

CurrentUser = Annotated[models.User, Depends(get_current_user)]