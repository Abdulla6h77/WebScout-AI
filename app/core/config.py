from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    time_budget_s: float = Field(30, ge=0.05, le=180)
    request_timeout_s: float = Field(8, ge=0.05, le=60)
    max_pages: int = Field(8, ge=1, le=20)
    max_hops: int = Field(2, ge=0, le=4)
    max_attempts: int = Field(3, ge=1, le=5)
    concurrency: int = Field(3, ge=1, le=5)
    max_response_bytes: int = Field(1_000_000, ge=1000, le=5_000_000)
    max_content_chars: int = Field(60_000, ge=1000, le=100_000)
    cache_ttl_s: int = Field(0, ge=0, le=3600)
    cache_entries: int = Field(64, ge=1, le=256)
    tinyfish_api_key: SecretStr = SecretStr("")
    tinyfish_agent_enabled: bool = False
    playwright_enabled: bool = False
    llm_provider: Literal["auto", "gemini", "openrouter", "nvidia", "local", "none"] = "auto"
    provider_priority: str = "openrouter,gemini,nvidia"
    gemini_api_key: SecretStr = SecretStr("")
    openrouter_api_key: SecretStr = SecretStr("")
    nvidia_api_key: SecretStr = SecretStr("")
    gemini_model: str = "gemini-3.5-flash-lite"
    openrouter_model: str = "nvidia/nemotron-3.5-super-vl:free"
    nvidia_model: str = ""
    gemini_free_tier_confirmed: bool = False
    nvidia_free_tier_confirmed: bool = False
    local_base_url: str = "http://127.0.0.1:8001/v1"
    local_model: str = ""
    max_output_tokens: int = Field(1000, ge=100, le=3000)
    temperature: float = Field(0, ge=0, le=0.3)
    llm_retry_limit: int = Field(1, ge=0, le=2)
    provider_min_interval_s: float = Field(1, ge=0, le=10)
    max_estimated_api_cost_usd: float = Field(0, ge=0)

    def key(self, provider: str) -> str:
        return getattr(self, f"{provider}_api_key").get_secret_value()
