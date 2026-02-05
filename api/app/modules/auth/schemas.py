from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class AuthResponse(Token):
    refresh_token: str


class LoginRequest(BaseModel):
    username: str
    password: str
