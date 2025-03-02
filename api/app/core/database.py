import os
from typing import Annotated
from dotenv import load_dotenv
from fastapi import Depends
from sqlmodel import SQLModel, Session, create_engine

from app.core.mock_data import create_mock_data


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("The DATABASE_URL environment variable is not set")


engine = create_engine(DATABASE_URL, echo=True, future=True)


def init_db():
    SQLModel.metadata.create_all(engine)


def mock_database():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    create_mock_data(engine)


def get_session():
    with Session(engine) as session:
        yield session


# This Session will be used by all DB request
SessionDep = Annotated[Session, Depends(get_session)]
