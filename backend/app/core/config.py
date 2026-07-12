from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration.

    Values are loaded from the .env file
    or system environment variables.
    """

    app_name: str = "Converra AI"
    app_version: str = "1.0.0"

    app_env: str = "development"

    debug: bool = True

    host: str = "127.0.0.1"

    port: int = 8000

    log_level: str = "INFO"

    database_url: str = ""

    jwt_secret: str = ""

    groq_api_key: str = ""

    chroma_path: str = "./chroma_db"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings object.

    The configuration is loaded only once
    during the application's lifetime.
    """
    return Settings()


settings = get_settings()