"""Application configuration loaded from the environment (architecture §33)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_API_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """All runtime configuration; no secrets or defaults that hide misconfiguration."""

    model_config = SettingsConfigDict(
        env_file=(
            _API_ROOT / ".env",
            _REPO_ROOT / ".env",
        ),
        env_file_encoding="utf-8",
        extra="forbid",
        case_sensitive=False,
    )

    compose_project_name: str = Field(validation_alias="COMPOSE_PROJECT_NAME")

    app_env: Literal["local", "staging", "production"] = Field(
        validation_alias="APP_ENV",
    )
    log_level: str = Field(validation_alias="LOG_LEVEL")
    api_host: str = Field(validation_alias="API_HOST")
    api_port: int = Field(validation_alias="API_PORT")
    web_port: int = Field(validation_alias="WEB_PORT")
    web_url: str = Field(validation_alias="WEB_URL")
    cors_origins: Annotated[list[str], NoDecode] = Field(
        validation_alias="CORS_ORIGINS",
    )

    mysql_host: str = Field(validation_alias="MYSQL_HOST")
    mysql_port: int = Field(validation_alias="MYSQL_PORT")
    mysql_database: str = Field(validation_alias="MYSQL_DATABASE")
    mysql_user: str = Field(validation_alias="MYSQL_USER")
    mysql_password: str = Field(validation_alias="MYSQL_PASSWORD")
    mysql_root_password: str = Field(validation_alias="MYSQL_ROOT_PASSWORD")
    database_url: str = Field(min_length=1, validation_alias="DATABASE_URL")

    redis_host: str = Field(validation_alias="REDIS_HOST")
    redis_port: int = Field(validation_alias="REDIS_PORT")
    redis_url: str = Field(validation_alias="REDIS_URL")

    s3_endpoint: str = Field(validation_alias="S3_ENDPOINT")
    s3_region: str = Field(validation_alias="S3_REGION")
    s3_access_key_id: str = Field(validation_alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str = Field(validation_alias="S3_SECRET_ACCESS_KEY")
    s3_bucket: str = Field(validation_alias="S3_BUCKET")
    minio_root_user: str = Field(validation_alias="MINIO_ROOT_USER")
    minio_root_password: str = Field(validation_alias="MINIO_ROOT_PASSWORD")
    minio_api_port: int = Field(validation_alias="MINIO_API_PORT")
    minio_console_port: int = Field(validation_alias="MINIO_CONSOLE_PORT")
    # s3 (default, MinIO/S3) or local (filesystem adapter for unit tests).
    storage_backend: Literal["s3", "local"] = Field(
        default="s3",
        validation_alias="STORAGE_BACKEND",
    )
    local_storage_root: str = Field(
        default="/tmp/entshifa-storage",
        validation_alias="LOCAL_STORAGE_ROOT",
    )
    attachment_upload_url_ttl_seconds: int = Field(
        default=900,
        ge=60,
        le=3600,
        validation_alias="ATTACHMENT_UPLOAD_URL_TTL_SECONDS",
    )
    attachment_download_url_ttl_seconds: int = Field(
        default=300,
        ge=30,
        le=900,
        validation_alias="ATTACHMENT_DOWNLOAD_URL_TTL_SECONDS",
    )

    jwt_issuer: str = Field(validation_alias="JWT_ISSUER")
    jwt_audience: str = Field(validation_alias="JWT_AUDIENCE")
    access_token_secret: str = Field(validation_alias="ACCESS_TOKEN_SECRET")
    refresh_token_secret: str = Field(validation_alias="REFRESH_TOKEN_SECRET")
    access_token_ttl_minutes: int = Field(validation_alias="ACCESS_TOKEN_TTL_MINUTES")
    refresh_token_ttl_days: int = Field(validation_alias="REFRESH_TOKEN_TTL_DAYS")

    field_encryption_key: str = Field(validation_alias="FIELD_ENCRYPTION_KEY")

    smtp_host: str | None = Field(default=None, validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, validation_alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, validation_alias="SMTP_PASSWORD")
    smtp_from: str = Field(validation_alias="SMTP_FROM")
    sms_provider: str | None = Field(default=None, validation_alias="SMS_PROVIDER")

    sentry_dsn: str | None = Field(default=None, validation_alias="SENTRY_DSN")
    otel_exporter_otlp_endpoint: str | None = Field(
        default=None,
        validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        if isinstance(value, list):
            return value
        msg = "CORS_ORIGINS must be a comma-separated string"
        raise TypeError(msg)

    @field_validator(
        "smtp_host",
        "smtp_user",
        "smtp_password",
        "sms_provider",
        "sentry_dsn",
        "otel_exporter_otlp_endpoint",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


def load_settings() -> Settings:
    """Load settings and translate validation failures into a short startup message."""

    try:
        return get_settings()
    except Exception as exc:
        from pydantic import ValidationError
        from pydantic_settings import SettingsError

        if isinstance(exc, SettingsError):
            raise SystemExit(f"Configuration error: {exc}") from exc
        if isinstance(exc, ValidationError):
            missing = [
                err["loc"][0] for err in exc.errors() if err["type"] == "missing"
            ]
            if missing:
                names = ", ".join(str(name) for name in missing)
                raise SystemExit(
                    f"Configuration error: missing required environment variable(s): "
                    f"{names}"
                ) from exc
            first = exc.errors()[0]
            field = ".".join(str(part) for part in first["loc"])
            raise SystemExit(
                f"Configuration error: invalid value for {field}: {first['msg']}"
            ) from exc
        raise
