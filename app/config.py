import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator, computed_field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    secret_key: str = "insecure-dev-secret"
    app_debug: bool = False
    app_url: str = "http://localhost:8000"

    # Database (use DATABASE_URL env var for Postgres; fallback to SQLite)
    database_url: str = "sqlite:///./medisys.db"

    # JWT
    jwt_secret: str = "insecure-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080

    # Storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10

    # AI
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Rate limiting
    rate_limit_booking: str = "5/minute"
    rate_limit_contact: str = "5/minute"

    # Edge
    backend_origin: str = "http://localhost:8000"

    @computed_field  # type: ignore
    @property
    def DB_URL(self) -> str:
        # If no DATABASE_URL is set, fall back to SQLite for local dev
        if not self.DATABASE_URL or self.DATABASE_URL.lower() in ("", "none", "null"):
            return "sqlite"
        return self.DATABASE_URL

    @model_validator(mode="after")
    def check_database_url(self):
        # Pydantic already loaded .env into self.database_url (defaults to sqlite if not set)
        env_url = self.database_url or ""

        # Explicit sqlite URL -> use it
        if env_url.startswith("sqlite"):
            return self

        # Empty or not a valid URL -> fallback to local sqlite
        if not env_url or "://" not in env_url:
            self.database_url = "sqlite:///./medisys.db"
            return self

        # Parse hostname and treat loopback addresses as local
        try:
            from urllib.parse import urlparse

            parsed = urlparse(env_url)
            host = (parsed.hostname or "").lower()
        except Exception:
            host = ""

        loopbacks = {"localhost", "127.0.0.1", "::1"}
        if host in loopbacks or "localhost" in env_url:
            self.database_url = "sqlite:///./medisys.db"
        else:
            self.database_url = env_url
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
