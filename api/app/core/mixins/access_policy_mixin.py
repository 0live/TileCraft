from app.core.enums.access_policy import AccessPolicy
from sqlalchemy import Enum as SAEnum
from sqlalchemy import text
from sqlmodel import Field, SQLModel


class AccessPolicyMixin(SQLModel):
    access_policy: AccessPolicy = Field(
        sa_type=SAEnum(
            AccessPolicy,
            name="accesspolicy",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        sa_column_kwargs={"server_default": text("'standard'")},
        nullable=False,
        default=AccessPolicy.STANDARD,
    )
