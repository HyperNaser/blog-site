from typing import Annotated

from fastapi import Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from core import app, templates
from database import get_db
from handlers.exception_handlers import register_exception_handlers
from routers import posts, users
from services import post_service, user_service

register_exception_handlers()

app.include_router(router=users.router, prefix="/api/users", tags=["users"])
app.include_router(router=posts.router, prefix="/api/posts", tags=["posts"])


@app.get("/", include_in_schema=False, name="home")
async def homepage(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=settings.max_limit)] = settings.posts_per_page,
):
    paginated_posts_response = await post_service.get_paginated_posts(db, skip, limit)

    return templates.TemplateResponse(
        request=request,
        name="home.jinja",
        context={
            "title": "Home",
            "posts": paginated_posts_response.posts,
            "pages_shown_window": settings.pages_shown_window,
            "total": paginated_posts_response.total,
            "skip": paginated_posts_response.skip,
            "limit": paginated_posts_response.limit,
            "has_more": paginated_posts_response.has_more,
        },
    )


@app.get("/users/{user_id}/posts", include_in_schema=False)
async def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=settings.max_limit)] = settings.posts_per_page,
):
    user = await user_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    paginated_posts_response = await user_service.get_user_posts(
        db, user_id, skip, limit, bypass_user_check=True
    )

    return templates.TemplateResponse(
        request=request,
        name="user_posts.jinja",
        context={
            "user": user,
            "title": f"{user.username}'s Posts",
            "posts": paginated_posts_response.posts,
            "pages_shown_window": settings.pages_shown_window,
            "total": paginated_posts_response.total,
            "skip": paginated_posts_response.skip,
            "limit": paginated_posts_response.limit,
            "has_more": paginated_posts_response.has_more,
        },
    )


@app.get("/posts/{post_id}", include_in_schema=False)
async def post_page(
    request: Request, post_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):
    post = await post_service.get_post_by_id(db, post_id)

    if post:
        return templates.TemplateResponse(
            request=request,
            name="post.jinja",
            context={"title": post.title[:25], "post": post},
        )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.jinja",
        {"title": "Login"},
    )


@app.get("/register", include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "register.jinja",
        {"title": "Register"},
    )


@app.get("/account", include_in_schema=False)
async def account_page(request: Request):
    return templates.TemplateResponse(
        request,
        "account.jinja",
        {"title": "Account"},
    )
