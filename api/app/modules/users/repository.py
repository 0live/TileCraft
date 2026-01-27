from typing import Any, List, Optional

from sqlmodel import select

from app.core.exceptions import DuplicateEntityException
from app.core.repository import BaseRepository
from app.modules.users.models import User


class UserRepository(BaseRepository[User]):
    """Repository for User entities."""

    async def get_by_username(
        self, username: str, options: Optional[List[Any]] = None
    ) -> Optional[User]:
        query = select(User).where(User.username == username)
        if options:
            for option in options:
                query = query.options(option)
        result = await self.session.exec(query)
        return result.first()

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        result = await self.session.exec(query)
        return result.first()

    async def validate_unique_credentials(
        self,
        email: str,
        username: str,
        exclude_user_id: Optional[int] = None,
    ) -> None:
        """
        Validate that email and username are unique.

        This method centralizes the validation logic to avoid duplication
        between UserService and AuthService, respecting the DRY principle.
        """
        # Check email uniqueness
        existing_email = await self.get_by_email(email)
        if existing_email and existing_email.id != exclude_user_id:
            raise DuplicateEntityException(
                key="user.email_exists", params={"email": email}
            )

        # Check username uniqueness
        existing_username = await self.get_by_username(username)
        if existing_username and existing_username.id != exclude_user_id:
            raise DuplicateEntityException(
                key="user.username_exists", params={"username": username}
            )
