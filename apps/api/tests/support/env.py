from __future__ import annotations

from ent.features.health.dependencies import get_health_service
from ent.settings import get_settings

VALID_ENV: dict[str, str] = {
    "COMPOSE_PROJECT_NAME": "entshifa",
    "APP_ENV": "local",
    "LOG_LEVEL": "INFO",
    "API_HOST": "0.0.0.0",
    "API_PORT": "8000",
    "WEB_PORT": "3000",
    "WEB_URL": "http://localhost:3000",
    "CORS_ORIGINS": "http://localhost:3000",
    "MYSQL_HOST": "127.0.0.1",
    "MYSQL_PORT": "3306",
    "MYSQL_DATABASE": "entshifa",
    "MYSQL_USER": "entshifa",
    "MYSQL_PASSWORD": "local_dev_mysql_password_change_me",
    "MYSQL_ROOT_PASSWORD": "local_dev_mysql_root_change_me",
    "DATABASE_URL": (
        "mysql+aiomysql://entshifa:local_dev_mysql_password_change_me"
        "@localhost:3306/entshifa?charset=utf8mb4"
    ),
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "REDIS_URL": "redis://localhost:6379/0",
    "S3_ENDPOINT": "http://localhost:9000",
    "S3_REGION": "us-east-1",
    "S3_ACCESS_KEY_ID": "entshifa_minio_access_key",
    "S3_SECRET_ACCESS_KEY": "local_dev_minio_secret_change_me",
    "S3_BUCKET": "entshifa-clinical",
    "MINIO_ROOT_USER": "entshifa_minio_access_key",
    "MINIO_ROOT_PASSWORD": "local_dev_minio_secret_change_me",
    "MINIO_API_PORT": "9000",
    "MINIO_CONSOLE_PORT": "9001",
    "JWT_ISSUER": "entshifa-local",
    "JWT_AUDIENCE": "entshifa-api",
    "ACCESS_TOKEN_SECRET": "local_dev_access_token_secret_min_32_chars",
    "REFRESH_TOKEN_SECRET": "local_dev_refresh_token_secret_min_32_chars",
    "ACCESS_TOKEN_TTL_MINUTES": "15",
    "REFRESH_TOKEN_TTL_DAYS": "30",
    "FIELD_ENCRYPTION_KEY": "local_dev_field_encryption_key_32b_base64==",
    "SMTP_HOST": "",
    "SMTP_PORT": "587",
    "SMTP_USER": "",
    "SMTP_PASSWORD": "",
    "SMTP_FROM": "noreply@example.local",
    "SMS_PROVIDER": "",
    "SENTRY_DSN": "",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "",
}


def clear_settings_cache() -> None:
    get_settings.cache_clear()
    get_health_service.cache_clear()
