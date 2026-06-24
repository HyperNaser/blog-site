from typing import Sequence

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

import models
from schemas import UserCreate, UserUpdate
from security.passwords import hash_password


class UserDomainError(Exception):
    """Base exception for all user-related domain errors."""
    pass

class UsernameTakenError(UserDomainError):
    def __init__(self, username: str):
        super().__init__(f"The username '{username}' is already taken.")

class EmailTakenError(UserDomainError):
    def __init__(self, email: str):
        super().__init__(f"The email '{email}' is already registered.")

class UserNotFoundError(UserDomainError):
    def __init__(self, identifier: str | int):
        super().__init__(f"User with identifier '{identifier}' could not be found.")

async def add_user(db: AsyncSession, user: UserCreate) -> models.User:
    """
    Creates a new user and adds it to the database, returning the created user if unique constraints are not breached.
    Raises Domain Error Exception if unique constraints violated.
    """
    new_user = models.User()
    new_user.username = user.username
    new_user.email = user.email.lower()
    new_user.password_hash = hash_password(user.password)

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return new_user
    except IntegrityError as e:
        await db.rollback()
        
        error_msg = str(e.orig).lower()
        
        if "username" in error_msg:
            raise UsernameTakenError(user.username)
        if "email" in error_msg:
            raise EmailTakenError(user.email)
        
        raise UserDomainError("Failed to add user due to a database constraint violation.")


async def update_user(
    db: AsyncSession, user: models.User, update_data: UserUpdate
) -> models.User:
    """
    Updates a user in the database using provided update data, returning the updated user
    Raises Domain Error Exception if unique constraints violated.
    """
    if update_data.username is not None:
        user.username = update_data.username
    if update_data.email is not None:
        user.email = update_data.email.lower()
    if update_data.image_file is not None:
        user.image_file = update_data.image_file

    try:
        await db.commit()
        await db.refresh(user)

        return user
    except IntegrityError as e:
        await db.rollback()
        
        error_msg = str(e.orig).lower()
        
        if "username" in error_msg:
            raise UsernameTakenError(update_data.username or "The requested username")
        if "email" in error_msg:
            raise EmailTakenError(update_data.email or "The requested email")
        
        raise UserDomainError("Failed to update user due to a database constraint violation.")


async def delete_user(db: AsyncSession, user_id: int):
    """
    Deletes user from database if exists, otherwise raises a UserNotFoundError Exception
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(identifier=user_id)

    await db.delete(user)
    await db.commit()


async def get_user_posts(db: AsyncSession, user_id: int, bypass_user_check: bool = False) -> Sequence[models.Post]:
    """
    Fetches user posts from database, raises an UserNotFoundError Exception if user doesn't exist
    """
    if not bypass_user_check:
        user = await get_user_by_id(db, user_id)

        if not user:
            raise UserNotFoundError(identifier=user_id)

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
        .order_by(models.Post.date_posted.desc())
    )

    posts = result.scalars().all()
    return posts


async def get_user_by_email(db: AsyncSession, email: str) -> models.User | None:
    """
    Fetches a user from the database by their email address (case-insensitive).
    """
    result = await db.execute(
        select(models.User).where(func.lower(models.User.email) == email.lower())
    )
    return result.scalars().one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> models.User | None:
    """
    Fetches a user from the database by their username (case-insensitive).
    """
    result = await db.execute(
        select(models.User).where(func.lower(models.User.username) == username.lower())
    )
    return result.scalars().one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> models.User | None:
    """
    Fetches a user from the database by their id.
    """
    result = await db.execute(select(models.User).where(models.User.id == user_id))

    return result.scalars().one_or_none()
