from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from schemas import Token
from services import user_service
from datetime import timedelta
from config import settings
from security.auth import create_access_token, verify_access_token, oauth2_scheme
from security.passwords import verify_password
from exceptions import UnauthorizedCredentialsException
from typing import Annotated
from database import get_db

import models

class AuthDomainError(Exception):
    """Base exception for all auth-related domain errors."""

    pass

class IncorrectCredentialsError(AuthDomainError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)

async def authenticate_user_and_create_token(
    db: AsyncSession, email: str, password: str
) -> Token:
    """Authenticates a user and returns an access token."""
    email_input = email.lower()
    user = await user_service.get_user_by_email(db, email_input)

    if not user or not verify_password(password, user.password_hash):
        raise IncorrectCredentialsError(reason="Incorrect email or password")

    expires_delta = timedelta(minutes=settings.access_token_expire_duration)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=expires_delta
    )

    return Token(access_token=access_token, token_type="bearer")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
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
