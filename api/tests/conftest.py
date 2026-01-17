import pytest
from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.seeds import run_seed
from app.main import app
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.postgres import PostgresContainer

POSTGRES_IMAGE = "postgres:16-alpine"
POSTGRES_USER = "tester"
POSTGRES_PASSWORD = "tester"
POSTGRES_DATABASE = "test_database"


@pytest.fixture(name="postgres_container", scope="session")
def postgres_container_fixture():
    """Starts the container once per session."""
    postgres = PostgresContainer(
        image=POSTGRES_IMAGE,
        username=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DATABASE,
    )
    with postgres:
        wait_for_logs(
            container=postgres,
            predicate="database system is ready to accept connections",
        )
        yield postgres


@pytest.fixture(name="settings", scope="session")
def settings_fixture(postgres_container: PostgresContainer):
    """Provides test-specific settings to override environment variables."""
    return Settings(
        env="test",
        private_key="test_secret_key_very_long_for_jwt_requirements_123",
        postgres_user=POSTGRES_USER,
        postgres_password=POSTGRES_PASSWORD,
        postgres_db=POSTGRES_DATABASE,
        database_url=postgres_container.get_connection_url(),
    )


@pytest.fixture(name="engine", scope="session")
def engine_fixture(settings: Settings):
    """Initializes the database schema once per session."""
    engine = create_engine(settings.database_url)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    """
    Wraps each test in a transaction.
    Seeds are run inside the transaction and rolled back after each test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    # Run seeds inside the transaction so they are also rolled back
    run_seed(session, commit=False)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(name="client")
def client_fixture(session: Session, settings: Settings):
    """Configures TestClient with session and settings overrides."""
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="user_data")
def user_data_fixture():
    return {
        "email": "test@test.com",
        "username": "test_user",
        "password": "test_password",
    }


@pytest.fixture(name="existing_users")
def existing_users_fixture():
    return [
        {"email": "user@test.com", "username": "user", "password": "user"},
        {"email": "editor@test.com", "username": "editor", "password": "editor"},
        {"email": "admin@test.com", "username": "admin", "password": "admin"},
    ]


@pytest.fixture(name="auth_token_factory")
def token_factory_fixture(client: TestClient):
    """
    Helper fixture to generate a JWT token for protected routes.
    """

    def _get_token(username: str = "test_user", password: str = "test_password") -> str:
        payload = {"username": username, "password": password}
        response = client.post(
            "/users/login",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        return response.json()["access_token"]

    return _get_token
