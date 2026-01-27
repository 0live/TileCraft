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

    async def get_or_raise(
        self,
        id: int,
        entity_name: str,
        key: str,
        options: Optional[List[Any]] = None,
    ) -> ModelType:
        """Retrieve an entity by ID or raise EntityNotFoundException."""
        from app.core.exceptions import EntityNotFoundException

        entity = await self.get(id, options=options)
        if not entity:
            raise EntityNotFoundException(
                entity=entity_name, key=key, params={"id": id}
            )
        return entity

    async def ensure_unique_name(
        self,
        name: str,
        key: str,
        exclude_id: Optional[int] = None,
        **additional_filters,
    ) -> None:
        """
        Ensure a name is unique, raising DuplicateEntityException if not.
        Supports scoped uniqueness via additional_filters (e.g., atlas_id=5).
        """
        from app.core.exceptions import DuplicateEntityException

        if not hasattr(self.model, "name"):
            return

        query = select(self.model).where(getattr(self.model, "name") == name)

        # Add additional filters (e.g., atlas_id for maps)
        for field_name, field_value in additional_filters.items():
            if hasattr(self.model, field_name):
                query = query.where(getattr(self.model, field_name) == field_value)

        # Exclude current entity during updates
        if exclude_id is not None:
            query = query.where(self.model.id != exclude_id)

        result = await self.session.exec(query)
        existing = result.first()

        if existing:
            raise DuplicateEntityException(key=key, params={"name": name})

    async def get_related_entity(
        self,
        model_class: Type[SQLModel],
        entity_id: int,
        entity_name: str,
        key: str,
    ) -> SQLModel:
        """
        Retrieve an entity of a different type by ID or raise EntityNotFoundException.

        This method allows services to verify the existence of related entities
        from other modules without directly accessing the session, respecting
        the Repository Pattern.

        Args:
            model_class: The SQLModel class to retrieve
            entity_id: ID of the entity to retrieve
            entity_name: Human-readable entity name for error messages
            key: Localization key for the error message

        Returns:
            The retrieved entity

        Raises:
            EntityNotFoundException: If the entity does not exist

        Example:
            # In TeamService, verify a User exists before adding to team
            from app.modules.users.models import User
            user = await self.repository.get_related_entity(
                User, user_id, "User", "user.not_found"
            )
        """
        from app.core.exceptions import EntityNotFoundException

        entity = await self.session.get(model_class, entity_id)
        if not entity:
            raise EntityNotFoundException(
                entity=entity_name, key=key, params={"id": entity_id}
            )
        return entity
