from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/zhixue.db"
    agent_mode: Literal["mock", "remote", "local"] = "mock"
    mock_event_delay_ms: int = 40
    remote_agent_base_url: str = ""
    remote_agent_api_key: str = ""
    remote_agent_timeout_seconds: int = 120
    allow_mock_fallback: bool = False
    remote_profile_path: str = "/profile/stream"
    remote_resources_path: str = "/resources/stream"
    remote_qa_path: str = "/qa/stream"
    remote_path_path: str = "/path"
    remote_evaluation_path: str = "/evaluation"
    web_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    sse_poll_interval_ms: int = 250
    sse_heartbeat_seconds: int = 15
    course_root: Path = Path("./data/courses")
    knowledge_base_root: Path = Path("knowledge_base")

    @model_validator(mode="after")
    def resolve_knowledge_base_root(self) -> "Settings":
        if not self.knowledge_base_root.is_absolute():
            self.knowledge_base_root = WORKSPACE_ROOT / self.knowledge_base_root
        return self

    @property
    def allowed_web_origins(self) -> list[str]:
        return [origin.strip() for origin in self.web_origins.split(",") if origin.strip()]
