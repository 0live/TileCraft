from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import get_settings
from app.core.database import sessionmanager
from app.core.exceptions.handlers import add_all_exception_handlers
from app.core.messages import MessageService
from app.modules.atlases.endpoints import atlasesRouter
from app.modules.auth.endpoints import authRouter
from app.modules.maps.endpoints import mapsRouter
from app.modules.teams.endpoints import teamsRouter
from app.modules.users.endpoints import userRouter


@asynccontextmanager
async def lifespan(app: FastAPI):
    sessionmanager.init(str(get_settings().database_url))
    MessageService.load_messages()
    yield
    await sessionmanager.close()


app = FastAPI(
    title="Canopy API",
    summary="Love and Mappyness",
    version="0.0.1",
    lifespan=lifespan,
    root_path="/api",
)

add_all_exception_handlers(app)

app.add_middleware(
    SessionMiddleware,
    secret_key=get_settings().private_key,
    same_site="lax" if get_settings().env == "dev" else "strict",
    https_only=False if get_settings().env == "dev" else True,
)

if get_settings().cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in get_settings().cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=get_settings().allowed_hosts,
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Docker healthcheck."""
    return {"status": "healthy"}


app.include_router(authRouter)
app.include_router(userRouter)
app.include_router(teamsRouter)
app.include_router(atlasesRouter)
app.include_router(mapsRouter)
