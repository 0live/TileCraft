from typing import List
from pydantic import BaseModel, EmailStr

from app.models.user_roles import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str
    roles: List[UserRole] = [UserRole.USER]


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
