from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine

from app.core.config import get_settings


def get_engine():
    """
    Returns the engine based on current settings.
    During tests, this will use the overridden settings.
    """
    settings = get_settings()
    return create_engine(settings.database_url, echo=True)


def get_session():
    with Session(get_engine()) as session:
        yield session


# This Session will be used by all DB request
SessionDep = Annotated[Session, Depends(get_session)]
