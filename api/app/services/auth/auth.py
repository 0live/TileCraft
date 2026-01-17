import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from authlib.integrations.starlette_client import OAuth
from fastapi.security import OAuth2PasswordBearer

from app.core.config import Settings
from app.models.auth import Token
from app.models.users import UserRead

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(
    data: dict,
    settings: Settings,
    expires_delta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.now() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, str(settings.private_key), algorithm=settings.algorithm
    )


def decode_token(token: str, settings: Settings):
    return jwt.decode(token, str(settings.private_key), algorithms=[settings.algorithm])


# Dans app/services/auth/auth.py


def get_token(user: UserRead, settings) -> Token:
    token = create_access_token(data={**user.model_dump()}, settings=settings)
    return Token(access_token=token, token_type="bearer")


ACTIVATE_GOOGLE_SSO = os.getenv("ACTIVATE_GOOGLE_SSO", "false").lower() == "true"
oauth = OAuth()
if ACTIVATE_GOOGLE_SSO:
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise ValueError("Google SSO keys are missing")
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile", "response_type": "code"},
    )
