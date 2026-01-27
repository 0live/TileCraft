import logging
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy.inspection import inspect
from sqlalchemy.orm import RelationshipProperty
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing generic CRUD operations with eager loading support.
    """

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model
        # Cache for relationship fields to avoid repeated introspection
        self._relationship_fields_cache: Optional[set[str]] = None

    def _get_relationship_fields(self) -> set[str]:
        """
        Introspects the SQLModel to find all Relationship fields.
        Results are cached to avoid repeated introspection.

        Returns:
            Set of field names that are SQLModel Relationships
        """
        if self._relationship_fields_cache is None:
            mapper = inspect(self.model)
            self._relationship_fields_cache = {
                attr.key
                for attr in mapper.attrs
                if isinstance(attr, RelationshipProperty)
            }
        return self._relationship_fields_cache

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

    async def update(
        self, id: int, attributes: dict, options: Optional[List[Any]] = None
    ) -> Optional[ModelType]:
        """
        Update an entity by ID and return it.
        Automatically excludes relationship fields to prevent lazy loading issues.
        """
        db_obj = await self.get(id, options=options)
        if not db_obj:
            return None

        relationship_fields = self._get_relationship_fields()

        filtered_fields = set(attributes.keys()) & relationship_fields
        if filtered_fields:
            logger.debug(
                f"Filtered relationship fields from {self.model.__name__} update: {filtered_fields}"
            )

        safe_attributes = {
            k: v for k, v in attributes.items() if k not in relationship_fields
        }

        for key, value in safe_attributes.items():
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
