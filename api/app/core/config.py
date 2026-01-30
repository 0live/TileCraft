from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "dev"
    private_key: str = "your_default_secret_key_change_me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    locale: str = "en"

    # Database components
    postgres_user: str = "default"
    postgres_password: str = "default"
    postgres_db: str = "default"
    postgres_host: str = "localhost"
    postgres_port: str = "5432"
    database_url: str = "postgresql+psycopg://default:default@localhost:5432/default"

    # Martin tile server (internal network)
    martin_internal_url: str = "http://martin:3000"

    # Google SSO
    activate_google_auth: bool = False
    google_client_id: str | None = None
    google_client_secret: str | None = None

    model_config = SettingsConfigDict(
        env_file=("../.env", "../.env.local", ".env", ".env.local"), extra="ignore"
    )


@lru_cache
def get_settings():
    return Settings()
