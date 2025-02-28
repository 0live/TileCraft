from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

from app.models.user_roles import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str
    roles: List[UserRole] = [UserRole.USER]


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(default=None)
    username: Optional[str] = Field(default=None)
    roles: Optional[List[UserRole]] = Field(default=None)
    password: Optional[str] = Field(default=None)
