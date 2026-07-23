from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ReWear API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    firebase_project_id: str = ""
    firebase_credentials_path: str = ""
    firebase_storage_bucket: str = ""

    max_upload_size_mb: int = 10
    allowed_image_types: tuple[str, ...] = ("image/jpeg", "image/png", "image/webp")


@lru_cache
def get_settings() -> Settings:
    return Settings()
