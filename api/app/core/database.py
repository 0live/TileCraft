from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings


def get_engine():
    settings = get_settings()
    return create_async_engine(str(settings.database_url), echo=True, future=True)


engine = get_engine()


async def get_session():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


# This Session will be used by all DB request
SessionDep = Annotated[AsyncSession, Depends(get_session)]
