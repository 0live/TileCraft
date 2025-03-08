from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from app.core.database import init_db, mock_database
from app.endpoints.users import userRouter
from app.endpoints.teams import teamsRouter
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

app.include_router(userRouter)
app.include_router(teamsRouter)
app.include_router(atlasesRouter)
app.include_router(mapsRouter)
