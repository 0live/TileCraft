from functools import lru_cache
from typing import Any, List

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.exceptions import SecurityException


class Settings(BaseSettings):
    env: str = "dev"
    private_key: str = "your_default_secret_key_change_me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    locale: str = "en"
    site_address: str = ""
    cors_origins: List[str] = ["*"]

    @field_validator("cors_origins", mode="before")
    def assemble_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise SecurityException(key="config.cors_origins_invalid_format")

    @property
    def allowed_hosts(self) -> List[str]:
        """Derive allowed hosts from SITE_ADDRESS."""
        if self.env in ["dev", "test"]:
            return ["*"]

        if self.site_address:
            host = (
                self.site_address.strip().replace("https://", "").replace("http://", "")
            )
            host = host.split("/")[0]
            return [host, f"*.{host}"]

        raise SecurityException(key="config.site_address_missing")

    @field_validator("private_key")
    def validate_secret_key(cls, v: str, info: ValidationInfo) -> str:
        values = info.data
        if values.get("env") == "prod" and v == "your_default_secret_key_change_me":
            raise SecurityException(key="config.insecure_secret_key")
        return v

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

    # Application Features
    allow_self_registration: bool = True

    # Email / SMTP settings
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str = "noreply@canopy.dev"
    smtp_use_tls: bool = False
    smtp_starttls: bool = False

    model_config = SettingsConfigDict(
        env_file=("../.env", "../.env.local", ".env", ".env.local"), extra="ignore"
    )


@lru_cache
def get_settings():
    return Settings()
