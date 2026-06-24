from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

import models
from schemas import PostCreate, PostUpdate
from services.auth_service import CurrentUser


class PostDomainError(Exception):
    """Base exception for all post-related domain errors."""

    pass


class PostNotFoundError(PostDomainError):
    def __init__(self, identifier: str | int):
        super().__init__(f"Post with identifier '{identifier}' could not be found.")


class PermissionDeniedError(PostDomainError):
    def __init__(self, reason: str | None = None):
        msg = "User is not authorized to perform this action."
        if reason:
            msg = f"{msg} {reason}"
        super().__init__(msg)


async def add_post(db: AsyncSession, current_user: CurrentUser, post: PostCreate):
    new_post = models.Post(**post.model_dump())
    new_post.user_id = current_user.id

    db.add(new_post)
    await db.commit()
    await db.refresh(new_post, attribute_names=["author"])

    return new_post


async def update_post(
    db: AsyncSession, post_id: int, current_user: CurrentUser, update_data: PostUpdate
) -> models.Post:
    """
    Updates post if found, raises a PostNotFoundError Exception if not.

    Raises a PermissionDeniedError Exception if user is not the owner of post.
    """
    post = await get_post_by_id(db, post_id)

    if post is None:
        raise PostNotFoundError(identifier=post_id)

    if post.user_id != current_user.id:
        raise PermissionDeniedError(reason="User is not the post owner.")

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post, attribute_names=["author"])

    return post


async def delete_post(db: AsyncSession, current_user: CurrentUser, post_id: int):
    """
    Deletes post if found, raises a PostNotFoundError Exception if not.

    Raises a PermissionDeniedError Exception if user is not the owner of post.
    """
    post = await get_post_by_id(db, post_id)

    if not post:
        raise PostNotFoundError(identifier=post_id)

    if post.user_id != current_user.id:
        raise PermissionDeniedError(reason="User is not the post owner.")

    await db.delete(post)
    await db.commit()


async def get_post_by_id(db: AsyncSession, post_id: int) -> models.Post | None:
    """
    Fetches a post from the database by id. Returning None if none is found.
    """
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id)
    )

    return result.scalars().one_or_none()


async def get_all_posts(db: AsyncSession) -> Sequence[models.Post]:
    """
    Fetches all posts in descending order.
    """
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .order_by(models.Post.date_posted.desc())
    )

    return result.scalars().all()
