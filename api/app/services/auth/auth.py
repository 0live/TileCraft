from datetime import datetime, timedelta
import os
from typing import Optional
from dotenv import load_dotenv
import jwt
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

load_dotenv()
SECRET_KEY = os.getenv("PRIVATE_KEY")
if not SECRET_KEY:
    raise ValueError("The SECRET_KEY environment variable is not set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, str(SECRET_KEY), algorithm=ALGORITHM)


def decode_token(token: str):
    return jwt.decode(token, str(SECRET_KEY), algorithms=[ALGORITHM])
