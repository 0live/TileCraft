from datetime import datetime, timedelta
import os
from typing import Optional
from dotenv import load_dotenv
import jwt
import bcrypt
from fastapi.security import OAuth2PasswordBearer
from authlib.integrations.starlette_client import OAuth
from app.models.users import UserRead
from app.models.auth import Token

load_dotenv()
SECRET_KEY = os.getenv("PRIVATE_KEY")
if not SECRET_KEY:
    raise ValueError("The SECRET_KEY environment variable is not set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, str(SECRET_KEY), algorithm=ALGORITHM)


def decode_token(token: str):
    return jwt.decode(token, str(SECRET_KEY), algorithms=[ALGORITHM])


def get_token(user: UserRead) -> Token:
    token = create_access_token(data={**user.model_dump()})
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
