from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from email_utils import send_password_reset_email
from schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    PostResponse,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserPrivate,
    UserPublic,
    UserUpdate,
)
from services import auth_service, user_service
from services.auth_service import CurrentUser

router = APIRouter()


@router.post(
    "",
    response_model=UserPrivate,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"description": "Username/email taken or malformed request"}},
)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    return await user_service.add_user(db, user)


@router.post(
    "/token",
    response_model=Token,
    responses={401: {"description": "Incorrect credentials"}},
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.authenticate_user_and_create_token(
        db, email=form_data.username, password=form_data.password
    )


@router.get(
    "/me",
    response_model=UserPrivate,
    responses={
        401: {"description": "Not authenticated"},
    },
)
async def get_current_user(current_user: CurrentUser):
    return current_user


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        user = await user_service.get_user_by_email(db, request_data.email)
        if user:
            token = await user_service.create_reset_token_for_user(db, user.id)
            background_tasks.add_task(
                send_password_reset_email,
                to_email=user.email,
                username=user.username,
                token=token,
            )
    except Exception:
        pass

    return {
        "message": "If an account with this email exists, you will receive password reset instructions."
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request_data: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    reset_token = await auth_service.validate_reset_token(db, request_data.token)

    user = await user_service.get_user_by_id(db, reset_token.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    await user_service.change_password(db, user, request_data.new_password)

    return {
        "message": "Password reset successfully. You can now log in with your new password."
    }


@router.patch("/me/password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not auth_service.verify_password(
        password_data.current_password, current_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    await user_service.change_password(db, current_user, password_data.new_password)
    return {"message": "Password changed successfully"}


@router.get(
    "/{user_id}",
    response_model=UserPublic,
    responses={404: {"description": "User not found"}},
)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await user_service.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


@router.patch(
    "/{user_id}",
    response_model=UserPrivate,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to update user"},
        400: {"description": "Username/email taken or malformed request"},
    },
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user",
        )

    return await user_service.update_user(db, user=current_user, update_data=user_data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to delete user"},
        404: {"description": "User not found"},
    },
)
async def delete_user(
    user_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user",
        )

    await user_service.delete_user(db, user_id)


@router.get(
    "/{user_id}/posts",
    response_model=list[PostResponse],
    responses={
        404: {"description": "User not found"},
    },
)
async def get_user_posts(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=settings.max_limit)] = settings.posts_per_page,
):
    return await user_service.get_user_posts(db, user_id, skip, limit)


@router.patch(
    "/{user_id}/picture",
    response_model=UserPrivate,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to update user's picture"},
        413: {"description": "File too large"},
        400: {"description": "Invalid image file"},
    },
)
async def upload_profile_picture(
    user_id: int,
    file: UploadFile,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's picture",
        )

    content = await file.read()

    return await user_service.update_profile_picture(db, current_user, content)


@router.delete(
    "/{user_id}/picture",
    response_model=UserPrivate,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to delete user's picture"},
        400: {"description": "No profile picture to delete"},
    },
)
async def delete_user_picture(
    user_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user's picture",
        )

    return await user_service.delete_profile_picture(db, current_user)
