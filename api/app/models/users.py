from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
