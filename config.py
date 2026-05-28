from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM Settings
    LLM_PROVIDER: str = "openai"  # openai, gemini, anthropic, ollama, custom
    LLM_MODEL: Optional[str] = None  # defaults to provider's smart default if None

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"

    GEMINI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # GuardRail Core Settings
    GUARDRAIL_DB_PATH: str = "./guardrail.db"
    GUARDRAIL_HOST: str = "0.0.0.0"
    GUARDRAIL_PORT: int = 8000
    DRIFT_THRESHOLD: float = 0.70
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

