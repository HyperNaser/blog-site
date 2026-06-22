from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Sequence
from schemas import PostUpdate, PostCreate
import models

class PostDomainError(Exception):
    """Base exception for all post-related domain errors."""
    pass

class PostNotFoundError(PostDomainError):
    def __init__(self, identifier: str | int):
        super().__init__(f"Post with identifier '{identifier}' could not be found.")


async def add_post(db: AsyncSession, post: PostCreate):
    new_post = models.Post(**post.model_dump())

    db.add(new_post)
    await db.commit()
    await db.refresh(new_post, attribute_names=["author"])

    return new_post


async def update_post(db: AsyncSession, post: models.Post, update_data: PostUpdate) -> models.Post: 
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post, attribute_names=["author"])

    return post


async def delete_post(db: AsyncSession, post_id: int): 
    post = await get_post_by_id(db, post_id)

    if not post:
        raise PostNotFoundError(identifier=post_id)

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
