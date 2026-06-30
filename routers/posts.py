from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from core.database import get_db
from schemas import PaginatedPostsResponse, PostCreate, PostResponse, PostUpdate
from services import post_service
from services.auth_service import CurrentUser

router = APIRouter()


@router.get("", response_model=PaginatedPostsResponse)
async def get_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=settings.max_limit)] = settings.posts_per_page,
):
    return await post_service.get_paginated_posts(db, skip, limit)


@router.get(
    "/{post_id}",
    response_model=PostResponse,
    responses={404: {"description": "Post not found"}},
)
async def get_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    post = await post_service.get_post_by_id(db, post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    return post


@router.put(
    "/{post_id}",
    response_model=PostResponse,
    responses={
        404: {"description": "Post not found"},
        403: {"description": "Not authorized to update post"},
    },
)
async def update_post_full(
    post_id: int,
    post_data: PostCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await post_service.update_post(
        db,
        post_id=post_id,
        current_user=current_user,
        update_data=PostUpdate(**post_data.model_dump()),
    )


@router.patch(
    "/{post_id}",
    response_model=PostResponse,
    responses={
        404: {"description": "Post not found"},
        403: {"description": "Not authorized to update post"},
    },
)
async def update_post_partial(
    post_id: int,
    post_data: PostUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await post_service.update_post(
        db, post_id=post_id, current_user=current_user, update_data=post_data
    )


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post: PostCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await post_service.add_post(db, current_user=current_user, post=post)


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Post not found"},
        403: {"description": "Not authorized to delete post"},
    },
)
async def delete_post(
    post_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await post_service.delete_post(db, current_user, post_id)
