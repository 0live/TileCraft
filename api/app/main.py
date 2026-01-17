from contextlib import asynccontextmanager
import os
from app.core.config import get_settings
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.endpoints.users import userRouter
from app.endpoints.teams import teamsRouter
from app.endpoints.sso.google import googleRouter
from app.endpoints.atlases import atlasesRouter
from app.endpoints.maps import mapsRouter

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="TileCraft API",
    summary="Love and Mappyness",
    version="0.0.1",
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=get_settings().private_key,
    same_site="lax" if get_settings().env == "dev" else "strict",
    https_only=False if get_settings().env == "dev" else True,
)

app.include_router(userRouter)
app.include_router(teamsRouter)
app.include_router(googleRouter)
app.include_router(atlasesRouter)
app.include_router(mapsRouter)
