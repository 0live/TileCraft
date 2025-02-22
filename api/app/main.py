from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="MapStudio API",
    summary="Love and Mappyness",
    version="0.0.1",
    lifespan=lifespan,
)

# @app.on_event("startup")
# def on_startup():
#     init_db()
