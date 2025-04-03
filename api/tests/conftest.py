from fastapi.testclient import TestClient
import pytest
from sqlmodel import SQLModel, Session, create_engine
from testcontainers.postgres import PostgresContainer
from testcontainers.core.waiting_utils import wait_for_logs

from app.core.mock_data import create_mock_data
from app.core.database import get_session
from app.main import app

POSTGRES_IMAGE = "postgres:16-alpine"
POSTGRES_USER = "tester"
POSTGRES_PASSWORD = "tester"
POSTGRES_DATABASE = "test_database"
POSTGRES_CONTAINER_PORT = 5432


@pytest.fixture(name="postgres_container")
def postgres_container():
    postgres = PostgresContainer(
        image=POSTGRES_IMAGE,
        username=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DATABASE,
        port=POSTGRES_CONTAINER_PORT,
    )
    with postgres:
        wait_for_logs(
            container=postgres,
            predicate="database system is ready to accept connections",
            timeout=30,
            interval=0.5,
        )
        yield postgres


@pytest.fixture(name="session")
def session_fixture(postgres_container: PostgresContainer):
    engine = create_engine(postgres_container.get_connection_url(), echo=True)
    SQLModel.metadata.create_all(engine)
    create_mock_data(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="user_data")
def user_data():
    return {
        "email": "test@test.com",
        "username": "test_user",
        "password": "test_password",
    }


@pytest.fixture(name="existing_users")
def existing_users():
    return [
        {
            "email": "user@test.com",
            "username": "user",
            "password": "user",
        },
        {
            "email": "editor@test.com",
            "username": "editor",
            "password": "editor",
        },
        {
            "email": "admin@test.com",
            "username": "admin",
            "password": "admin",
        },
    ]


@pytest.fixture(name="get_token")
def token_factory_fixture(client: TestClient):
    def _get_token(username="test_user", password="test_password"):
        response = client.post(
            "/users/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        return response.json()["access_token"]

    return _get_token
