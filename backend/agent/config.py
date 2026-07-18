"""Load local-agent configuration from the workspace root .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV_FILE)


class Config:
    """全局配置单例"""

    # ── DeepSeek API ──
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-reasoner")
    DEEPSEEK_TIMEOUT = int(os.getenv("DEEPSEEK_TIMEOUT", "120"))
    DEEPSEEK_MAX_RETRIES = int(os.getenv("DEEPSEEK_MAX_RETRIES", "3"))

    @classmethod
    def validate(cls) -> bool:
        """验证必要配置是否完整，返回 True/False"""
        if not cls.DEEPSEEK_API_KEY or cls.DEEPSEEK_API_KEY == "your_api_key_here":
            print("[Config ERROR] DEEPSEEK_API_KEY is not set in the workspace root .env")
            return False
        return True
