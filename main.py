from typing import Annotated

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import Base, engine, get_db
from schemas import PostCreate, PostResponse, PostUpdate, UserCreate, UserResponse, UserUpdate

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")

@app.get("/", include_in_schema=False, name="home")
async def homepage(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).limit(10))
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request=request, 
        name="home.html", 
        context={
        "title": "Home",
        "posts": posts
    })

@app.get("/posts/{post_id}", include_in_schema=False)
async def post_page(request: Request, post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))
    post = result.scalars().first()
    
    if post:
        return templates.TemplateResponse(
            request=request, 
            name="post.html", 
            context={
                "title": post.title[:25],
                "post": post
            })
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

@app.get("/users/{user_id}/posts", response_model=list[PostResponse], include_in_schema=False)
async def user_posts_page(request: Request, user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    
    return templates.TemplateResponse(
        request=request,
        name="user_posts.html",
        context={
            "user": user,
            "title": f"{user.username}'s Posts",
            "posts": posts
        }
    )

@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.username == user.username))
    
    existing_user = result.scalars().one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
        
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    
    existing_user = result.scalars().one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    new_user = models.User()
    new_user.username = user.username
    new_user.email = user.email
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    
    user = result.scalars().first()
    
    if user:
        return user
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

@app.patch("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user_data.username is not None and user_data.username != user.username:
        result = await db.execute(select(models.User).where(models.User.username == user_data.username))
        
        existing_user = result.scalars().one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
    
    if user_data.email is not None and user_data.email != user.email:
        result = await db.execute(select(models.User).where(models.User.email == user_data.email))
        
        existing_user = result.scalars().one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    update_data = user_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return user
        
@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user_full(user_id: int, user_data: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user_data.username != user.username:
        result = await db.execute(select(models.User).where(models.User.username == user_data.username))
        
        existing_user = result.scalars().one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
    
    if user_data.email != user.email:
        result = await db.execute(select(models.User).where(models.User.email == user_data.email))
        
        existing_user = result.scalars().one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    for field, value in user_data.model_dump().items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    
    return user

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.delete(user)
    await db.commit()

@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return posts

@app.get("/api/posts", response_model=list[PostResponse])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).limit(10))
    return result.scalars().all()

@app.get("/api/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))

    post = result.scalars().first()
    
    if post:
        return post
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

@app.put("/api/posts/{post_id}", response_model=PostResponse)
async def update_post_full(post_id: int, post_data: PostCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))

    post = result.scalars().first()
    
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    if post_data.user_id != post.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to update this post")
    
    post.title = post_data.title
    post.content = post_data.content
    
    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    
    return post
    
@app.patch("/api/posts/{post_id}", response_model=PostResponse)
async def update_post_partial(post_id: int, post_data: PostUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))

    post = result.scalars().first()
    
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    update_data = post_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(post, field, value)
    
    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    
    return post

@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == post.user_id))
    
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    new_post = models.Post()
    new_post.title = post.title
    new_post.user_id = post.user_id
    new_post.content = post.content

    db.add(new_post)
    await db.commit()
    await db.refresh(new_post, attribute_names=["author"])
    
    return new_post

@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))

    post = result.scalars().first()
    
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    await db.delete(post)
    await db.commit()

@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    if request.url.path.startswith("/api"):
        return await http_exception_handler(request=request, exc=exception)
    
    message = exception.detail if exception.detail else "An error occurred. Please check your request and try again."

    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message
        },
        status_code=exception.status_code
    )
    
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request=request, exc=exception)
    
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again."
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    )