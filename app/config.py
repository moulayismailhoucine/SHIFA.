from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_secret_key: str = "insecure-dev-secret"
    app_debug: bool = False
    app_url: str = "http://localhost:8000"

    # Database
    database_url: str = "postgresql://medisys:medisys_pass@localhost:5432/medisys_db"

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
