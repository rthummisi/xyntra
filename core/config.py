from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "xyntra"
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    structured_logging: bool = True

    database_url: str = Field(
        default="postgresql+asyncpg://xyntra:xyntra@postgres:5432/xyntra"
    )
    redis_url: str = "redis://redis:6379/0"
    broker_url: str = "redis://redis:6379/1"
    result_backend: str = "redis://redis:6379/2"

    request_id_header: str = "X-Request-ID"
    api_key_header: str = "X-API-Key"
    default_rate_limit_per_minute: int = 120
    ready_timeout_seconds: float = 3.0

    artifacts_root: str = "./artifacts"
    local_only_default: bool = False
    local_ollama_base_url: str = "http://ollama:11434"
    ollama_auto_provision: bool = True
    ollama_default_models: list[str] = ["mistral", "nomic-embed-text"]
    semantic_cache_similarity_threshold: float = 0.95
    semantic_cache_embedding_model: str = "nomic-embed-text"
    provider_timeout_seconds: float = 60.0
    anthropic_base_url: str = "https://api.anthropic.com"
    openai_base_url: str = "https://api.openai.com"
    gemini_base_url: str = "https://generativelanguage.googleapis.com"
    grok_base_url: str = "https://api.x.ai"
    mistral_base_url: str = "https://api.mistral.ai"
    deepseek_base_url: str = "https://api.deepseek.com"
    groq_base_url: str = "https://api.groq.com"

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    ollama_api_key: str = ""
    gemini_api_key: str = ""
    grok_api_key: str = ""
    mistral_api_key: str = ""
    deepseek_api_key: str = ""
    groq_api_key: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
