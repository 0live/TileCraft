from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    APIException,
    AuthenticationException,
    DomainException,
    DuplicateEntityException,
    EntityNotFoundException,
    PermissionDeniedException,
    SecurityException,
)
from app.core.logging_config import logger
from app.core.messages import MessageService


async def duplicate_entity_exception_handler(
    request: Request, exc: DuplicateEntityException
):
    logger.warning(f"Duplicate entity error: {exc.key}", extra={"params": exc.params})
    msg = MessageService.get_message(exc.key, **exc.params)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": msg, "key": exc.key, "params": exc.params},
    )


async def entity_not_found_handler(request: Request, exc: DomainException):
    logger.info(f"Entity not found: {exc.key}", extra={"params": exc.params})
    msg = MessageService.get_message(exc.key, **exc.params)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": msg, "key": exc.key, "params": exc.params},
    )


async def permission_denied_handler(request: Request, exc: DomainException):
    user_id = (
        request.scope.get("user").id
        if "user" in request.scope and hasattr(request.scope["user"], "id")
        else "unknown"
    )
    logger.warning(
        f"Permission denied for user {user_id}: {exc.key}",
        extra={"params": exc.params},
    )
    msg = MessageService.get_message(exc.key, **exc.params)
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": msg, "key": exc.key, "params": exc.params},
    )


async def authentication_exception_handler(request: Request, exc: DomainException):
    logger.warning(f"Authentication failed: {exc.key}", extra={"params": exc.params})
    msg = MessageService.get_message(exc.key, **exc.params)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": msg, "key": exc.key, "params": exc.params},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def domain_exception_handler(request: Request, exc: DomainException):
    logger.warning(f"Domain exception: {exc.key}", extra={"params": exc.params})
    msg = MessageService.get_message(exc.key, **exc.params)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": msg, "key": exc.key, "params": exc.params},
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    logger.info("Validation error", extra={"errors": exc.errors()})
    # Transform Pydantic errors to our standard format
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "key": "VALIDATION_ERROR",
            "params": {"errors": exc.errors()},
        },
    )


async def api_exception_handler(request: Request, exc: APIException):
    # Fallback for generic exceptions. Log with traceback.
    logger.error(f"Internal Server Error: {exc.key}", exc_info=True)
    msg = MessageService.get_message(exc.key, **exc.params)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": msg, "key": exc.key, "params": exc.params},
    )


async def security_exception_handler(request: Request, exc: SecurityException):
    logger.critical(f"Security error: {exc.key}", extra={"params": exc.params})
    msg = MessageService.get_message(exc.key, **exc.params)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": msg, "key": exc.key, "params": exc.params},
    )


def add_all_exception_handlers(app):
    app.add_exception_handler(
        DuplicateEntityException, duplicate_entity_exception_handler
    )
    app.add_exception_handler(EntityNotFoundException, entity_not_found_handler)
    app.add_exception_handler(PermissionDeniedException, permission_denied_handler)
    app.add_exception_handler(AuthenticationException, authentication_exception_handler)
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(SecurityException, security_exception_handler)
    app.add_exception_handler(
        RequestValidationError, request_validation_exception_handler
    )
    app.add_exception_handler(APIException, api_exception_handler)
