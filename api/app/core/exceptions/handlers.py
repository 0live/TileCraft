from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.messages import MessageService

from . import (
    APIException,
    DomainException,
    DuplicateEntityException,
)


async def duplicate_entity_exception_handler(
    request: Request, exc: DuplicateEntityException
):
    msg = MessageService.get_message(exc.key, **exc.params)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": msg, "key": exc.key, "params": exc.params},
    )


async def entity_not_found_handler(request: Request, exc: DomainException):
    # This handler can be specific if we want a 404
    msg = MessageService.get_message(exc.key, **exc.params)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": msg, "key": exc.key, "params": exc.params},
    )


async def permission_denied_handler(request: Request, exc: DomainException):
    msg = MessageService.get_message(exc.key, **exc.params)
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": msg, "key": exc.key, "params": exc.params},
    )


async def authentication_exception_handler(request: Request, exc: DomainException):
    msg = MessageService.get_message(exc.key, **exc.params)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": msg, "key": exc.key, "params": exc.params},
    )


async def domain_exception_handler(request: Request, exc: DomainException):
    msg = MessageService.get_message(exc.key, **exc.params)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": msg, "key": exc.key, "params": exc.params},
    )


async def api_exception_handler(request: Request, exc: APIException):
    # Fallback for generic TileCraft exceptions
    msg = MessageService.get_message(exc.key, **exc.params)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": msg, "key": exc.key, "params": exc.params},
    )
