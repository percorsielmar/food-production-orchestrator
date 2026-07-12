from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurazione centralizzata del servizio."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    llm_provider: str = "anthropic"  # anthropic | openai | mock
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    llm_model: str = "claude-3-5-sonnet-20241022"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.2

    # Blocco 1 - microservizio analitico
    block1_base_url: str = "http://localhost:7000"
    block1_api_key: str | None = None

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_log_level: str = "INFO"

    # Sicurezza loop tool
    max_tool_turns: int = 5

    @property
    def effective_api_key(self) -> str | None:
        if self.llm_provider == "anthropic":
            return self.anthropic_api_key
        if self.llm_provider == "openai":
            return self.openai_api_key
        return None
