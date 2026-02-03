from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class RefreshToken(SQLModel, table=True):
    """
    Refresh Token model for handling long-lived authentication sessions.
    Stores a hash of the token to prevent database leaks from compromising accounts.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    token_hash: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    revoked: bool = Field(default=False)
