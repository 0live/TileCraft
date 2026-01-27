from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession


class DatabaseSessionManager:
    def __init__(self):
        self.engine: AsyncEngine | None = None

    def init(self, host: str):
        self.engine = create_async_engine(host, echo=True, future=True)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        if self.engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with AsyncSession(self.engine, expire_on_commit=False) as session:
            yield session

    async def close(self):
        if self.engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self.engine.dispose()


sessionmanager = DatabaseSessionManager()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in sessionmanager.get_session():
        yield session


def get_engine() -> AsyncEngine:
    if sessionmanager.engine is None:
        raise Exception("DatabaseSessionManager is not initialized")
    return sessionmanager.engine


SessionDep = Annotated[AsyncSession, Depends(get_session)]
