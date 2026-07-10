from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/zhixue.db"
    agent_mode: Literal["mock", "remote"] = "mock"
    mock_event_delay_ms: int = 40
    remote_agent_base_url: str = ""
    remote_agent_api_key: str = ""
    remote_agent_timeout_seconds: int = 120
    allow_mock_fallback: bool = False
