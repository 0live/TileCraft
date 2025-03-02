from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import init_db
from app.endpoints.users import userRouter
from app.endpoints.teams import teamsRouter


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

app.include_router(userRouter)
app.include_router(teamsRouter)
