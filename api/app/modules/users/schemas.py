from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.password_validation import validate_password
from app.modules.teams.schemas import TeamSummary
from app.modules.users.models import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str
    roles: List[UserRole] = [UserRole.USER]
    model_config = ConfigDict(from_attributes=True)


class UserSummary(UserBase):
    id: int


class UserDetail(UserSummary):
    teams: List[TeamSummary] = []
    is_verified: bool = False


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def valid_password(cls, v: str) -> str:
        return validate_password(v)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(default=None)
    username: Optional[str] = Field(default=None)
    roles: Optional[List[UserRole]] = Field(default=None)
    password: Optional[str] = Field(default=None)

    @field_validator("password")
    @classmethod
    def valid_password(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_password(v)
