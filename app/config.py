from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://foodops:local_demo_only@localhost:5433/foodops"
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-4.1-mini"
    agent_mode: Literal["demo", "ai"] = "demo"
    max_tool_calls: int = Field(default=8, ge=1, le=16)
    llm_timeout: float = Field(default=20, gt=0, le=60)

    @property
    def active_mode(self):
        return (
            "ai" if self.agent_mode == "ai" and self.openai_api_key.get_secret_value() else "demo"
        )


@lru_cache
def get_settings():
    return Settings()
