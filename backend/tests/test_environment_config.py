from pathlib import Path

from app.core.config import Settings, WORKSPACE_ROOT


def test_backend_settings_read_the_workspace_root_env_file():
    assert Settings.model_config["env_file"] == WORKSPACE_ROOT / ".env"


def test_local_agent_declares_the_workspace_root_env_file():
    config_file = Path(__file__).resolve().parents[1] / "agent" / "config.py"

    assert 'ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"' in config_file.read_text(
        encoding="utf-8"
    )
