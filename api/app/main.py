from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.core.database import init_db
from app.endpoints.users import userRouter
from app.endpoints.teams import teamsRouter
from app.endpoints.sso.google import googleRouter


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="TileCraft API",
    summary="Love and Mappyness",
    version="0.0.1",
    lifespan=lifespan,
)

load_dotenv()
SECRET_KEY = os.getenv("PRIVATE_KEY")
if not SECRET_KEY:
    raise ValueError("The SECRET_KEY environment variable is not set")
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=3600,
    same_site="lax",
    https_only=False,
)

app.include_router(userRouter)
app.include_router(teamsRouter)
app.include_router(googleRouter)
