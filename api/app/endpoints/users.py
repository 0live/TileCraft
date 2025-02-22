from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.db.users import User
from app.services.users import authenticate_user, create_user
from app.core.database import SessionDep
from app.models.users import UserLogin, UserRead, UserCreate
from app.models.auth import Token

userRouter = APIRouter(prefix="/users", tags=["Users"])


@userRouter.post("/register", response_model=UserRead)
def register(user: UserCreate, session: SessionDep):
    if session.exec(select(User).where(User.email == user.email)).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user(user, session)


@userRouter.post("/login", response_model=Token)
def login(user: UserLogin, session: SessionDep):
    return authenticate_user(session, user.email, user.password)


# @app.get("/users/me", response_model=UserRead)
# def read_me(token: str = Depends(verify_token), session: Session = Depends(get_session)):
#     user = verify_token(token, session)
#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid or expired token")
#     return user
