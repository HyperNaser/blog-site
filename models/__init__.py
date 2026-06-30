from sqlalchemy.ext.asyncio import AsyncEngine

from core.database import Base
from models.post import Post
from models.token import PasswordResetToken
from models.user import User

__all__ = ["Base", "User", "Post", "PasswordResetToken"]


async def init_models(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
