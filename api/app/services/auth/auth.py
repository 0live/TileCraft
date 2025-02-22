from datetime import datetime, timedelta
import os
from typing import Optional
from jose import jwt

file_path = os.path.join(os.path.dirname(__file__), "private_key.pem")
with open(file_path, "r") as f:
    SECRET_KEY = f.read()
ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
