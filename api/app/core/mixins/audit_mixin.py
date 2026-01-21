from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlmodel import Field, SQLModel


class AuditMixin(SQLModel):
    created_by_id: Optional[int] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": func.now()},
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"onupdate": func.now(), "server_default": func.now()},
    )
    updated_by_id: Optional[int] = Field(default=None, foreign_key="user.id")
