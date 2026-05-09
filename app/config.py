import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_secret_key: str = "insecure-dev-secret"
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

    # Rate limiting
    rate_limit_booking: str = "5/minute"
    rate_limit_contact: str = "5/minute"

    # Edge
    backend_origin: str = "http://localhost:8000"

    @model_validator(mode="after")
    def check_database_url(self):
        env_url = os.getenv("DATABASE_URL", "")
        if env_url and "localhost" not in env_url:
            self.database_url = env_url
        else:
            self.database_url = "sqlite:///./medisys.db"
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
