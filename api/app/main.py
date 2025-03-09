from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.core.database import init_db, mock_database
from app.endpoints.users import userRouter
from app.endpoints.teams import teamsRouter
from app.endpoints.sso.google import googleRouter
from app.endpoints.atlases import atlasesRouter
from app.endpoints.maps import mapsRouter


load_dotenv()
ENV = os.getenv("ENV")
if not ENV:
    raise ValueError("The development environment variable is not set")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if ENV == "dev":
        mock_database()
    else:
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
    same_site="lax" if ENV == "dev" else "strict",
    https_only=False if ENV == "dev" else True,
)

app.include_router(userRouter)
app.include_router(teamsRouter)
app.include_router(googleRouter)
app.include_router(atlasesRouter)
app.include_router(mapsRouter)
