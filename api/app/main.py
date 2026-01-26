from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.core.database import sessionmanager
from app.core.exceptions import (
    APIException,
    AuthenticationException,
    DomainException,
    DuplicateEntityException,
    EntityNotFoundException,
    PermissionDeniedException,
)
from app.core.exceptions.handlers import (
    api_exception_handler,
    authentication_exception_handler,
    domain_exception_handler,
    duplicate_entity_exception_handler,
    entity_not_found_handler,
    permission_denied_handler,
    request_validation_exception_handler,
)
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
    title="TileCraft API",
    summary="Love and Mappyness",
    version="0.0.1",
    lifespan=lifespan,
)

app.add_exception_handler(EntityNotFoundException, entity_not_found_handler)
app.add_exception_handler(DuplicateEntityException, duplicate_entity_exception_handler)
app.add_exception_handler(PermissionDeniedException, permission_denied_handler)
app.add_exception_handler(AuthenticationException, authentication_exception_handler)
app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)

app.add_middleware(
    SessionMiddleware,
    secret_key=get_settings().private_key,
    same_site="lax" if get_settings().env == "dev" else "strict",
    https_only=False if get_settings().env == "dev" else True,
)

app.include_router(authRouter)
app.include_router(userRouter)
app.include_router(teamsRouter)
app.include_router(atlasesRouter)
app.include_router(mapsRouter)
