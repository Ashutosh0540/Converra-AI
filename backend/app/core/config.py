from functools import lru_cache

from pydantic import field_validator, model_validator
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
    cors_origins: list[str] = ["http://localhost:3000"]
    trusted_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    max_upload_size_bytes: int = 10 * 1024 * 1024

    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/converra_ai"
    )

    jwt_secret: str = "local-development-secret"
    jwt_algorithm: str = "HS256"
    access_token_expiration_minutes: int = 30
    refresh_token_expiration_days: int = 7

    groq_api_key: str = ""
    openai_api_key: str = ""
    llm_provider: str = "rule_based"
    llm_model_name: str = "gpt-4o-mini"
    llm_base_url: str = ""
    orchestration_failure_threshold: int = 2

    voice_stt_provider: str = "rule_based"
    voice_tts_provider: str = "rule_based"
    voice_session_timeout_minutes: int = 30
    voice_audio_sample_rate: int = 16000
    voice_audio_channels: int = 1
    voice_audio_chunk_size: int = 2048

    hitl_low_confidence_threshold: float = 0.55
    hitl_repeated_failure_threshold: int = 2
    hitl_default_priority: str = "MEDIUM"

    chroma_path: str = "./chroma_db"
    embedding_provider: str = "deterministic"
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    knowledge_chunk_size: int = 1000
    knowledge_chunk_overlap: int = 200

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
        enable_decoding=False,
    )

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> object:
        if isinstance(value, str) and value.lower() in {"release", "prod"}:
            return False

        return value

    @field_validator("cors_origins", "trusted_hosts", mode="before")
    @classmethod
    def parse_csv_list(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.app_env.lower() in {"production", "prod"}:
            if self.debug:
                raise ValueError("DEBUG must be disabled in production.")
            if not self.jwt_secret or self.jwt_secret == "local-development-secret":
                raise ValueError(
                    "JWT_SECRET must be set to a strong secret in production."
                )
            if not self.database_url.startswith("postgresql"):
                raise ValueError("A PostgreSQL DATABASE_URL is required in production.")
            if "*" in self.cors_origins:
                raise ValueError("CORS_ORIGINS cannot contain '*' in production.")
        return self


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings object.

    The configuration is loaded only once
    during the application's lifetime.
    """
    return Settings()


settings = get_settings()
