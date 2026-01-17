from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "dev"
    private_key: str = "your_default_secret_key_change_me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120

    # Database components
    postgres_user: str = "default"
    postgres_password: str = "default"
    postgres_db: str = "default"
    postgres_host: str = "localhost"
    postgres_port: str = "5432"
    database_url: str = "postgresql://default:default@localhost:5432/default"

    model_config = SettingsConfigDict(
        env_file=("../.env", "../.env.local", ".env", ".env.local"), extra="ignore"
    )


@lru_cache
def get_settings():
    return Settings()
