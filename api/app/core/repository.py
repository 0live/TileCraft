from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing generic CRUD operations with eager loading support.

    Subclasses should override `get_load_options()` to specify relationships
    that need to be eagerly loaded to avoid MissingGreenlet errors.
    """

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    async def create(self, attributes: dict) -> ModelType:
        db_obj = self.model(**attributes)
        self.session.add(db_obj)
        await self.session.flush()
        return db_obj

    async def get(
        self, id: int, options: Optional[List[Any]] = None
    ) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id)
        if options:
            for option in options:
                query = query.options(option)
        result = await self.session.exec(query)
        return result.first()

    async def get_all(self, options: Optional[List[Any]] = None) -> List[ModelType]:
        query = select(self.model)
        if options:
            for option in options:
                query = query.options(option)
        result = await self.session.exec(query)
        return list(result.all())

    async def update(self, id: int, attributes: dict) -> Optional[ModelType]:
        """Update an entity by ID and return it."""
        db_obj = await self.get(id)
        if not db_obj:
            return None

        for key, value in attributes.items():
            setattr(db_obj, key, value)

        self.session.add(db_obj)
        await self.session.flush()
        return db_obj

    async def delete(self, id: int) -> bool:
        """Delete an entity by ID."""
        db_obj = await self.get(id)
        if not db_obj:
            return False

        await self.session.delete(db_obj)
        await self.session.flush()
        return True

    async def get_by_name(self, name: str) -> Optional[ModelType]:
        # Note: This assumes the model has a 'name' attribute.
        if not hasattr(self.model, "name"):
            return None

        query = select(self.model).where(getattr(self.model, "name") == name)
        result = await self.session.exec(query)
        return result.first()
