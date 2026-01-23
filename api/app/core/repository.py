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

    def get_load_options(self) -> List[Any]:
        """
        Override this method in subclasses to specify relationships to eager-load.

        Example:
            def get_load_options(self):
                return [selectinload(User.teams).selectinload(Team.users)]
        """
        return []

    async def create(self, attributes: dict) -> ModelType:
        """Create a new entity and return it with relations loaded."""
        db_obj = self.model(**attributes)
        self.session.add(db_obj)
        await self.session.flush()
        if self.get_load_options():
            return await self.get(db_obj.id)

        return db_obj

    async def get(
        self, id: int, options: Optional[List[Any]] = None
    ) -> Optional[ModelType]:
        """Get an entity by ID with eager-loaded relations."""
        query = select(self.model).where(self.model.id == id)
        query_options = self.get_load_options() if options is None else options
        for option in query_options:
            query = query.options(option)
        result = await self.session.exec(query)
        return result.first()

    async def get_all(self, options: Optional[List[Any]] = None) -> List[ModelType]:
        """Get all entities with eager-loaded relations."""
        query = select(self.model)
        query_options = self.get_load_options() if options is None else options
        for option in query_options:
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
        if self.get_load_options():
            return await self.get(db_obj.id)

        return db_obj

    async def delete(self, id: int) -> bool:
        """Delete an entity by ID."""
        db_obj = await self.get(id)
        if not db_obj:
            return False

        await self.session.delete(db_obj)
        await self.session.flush()
        return True

    async def get_by_name(
        self, name: str, options: Optional[List[Any]] = None
    ) -> Optional[ModelType]:
        """Get an entity by name with eager-loaded relations."""
        # Note: This assumes the model has a 'name' attribute.
        if not hasattr(self.model, "name"):
            return None

        query = select(self.model).where(getattr(self.model, "name") == name)
        query_options = self.get_load_options() if options is None else options
        for option in query_options:
            query = query.options(option)
        result = await self.session.exec(query)
        return result.first()
