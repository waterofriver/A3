"""
全局配置模块
-----------
从 .env 文件加载所有配置项，提供统一的配置入口。

.env 文件查找顺序（先找到的优先）：
1. agent/.env（与 config.py 同目录，开发环境）
2. ../agent/.env（从 backend/ 启动时）
3. 系统环境变量（DEEPSEEK_API_KEY 等，生产环境推荐）
"""

import os
from dotenv import load_dotenv

# 按优先级尝试多个路径加载 .env
_ENV_PATHS = [
    os.path.join(os.path.dirname(__file__), ".env"),                       # agent/.env
    os.path.join(os.path.dirname(__file__), "..", "agent", ".env"),       # backend/agent/.env
    os.path.join(os.path.dirname(__file__), "..", "..", "agent", ".env"), # .../agent/.env
]
_loaded = False
for _p in _ENV_PATHS:
    _p = os.path.abspath(_p)
    if os.path.isfile(_p):
        load_dotenv(_p)
        _loaded = True
        break

# 兜底：从当前工作目录加载
if not _loaded:
    load_dotenv()


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
            print("[Config ERROR] DEEPSEEK_API_KEY 未设置，请在 agent/.env 中填入你的 API Key")
            return False
        return True
