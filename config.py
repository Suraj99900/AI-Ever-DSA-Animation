"""
AI-EVER Code Visualizer — application configuration.

All settings are environment-aware but default to safe offline values.
"""

from __future__ import annotations

import os
from pathlib import Path


BASE_DIR: Path = Path(__file__).resolve().parent


class BaseConfig:
    """Shared configuration for all environments."""

    APP_NAME: str = "AI-EVER Code Visualizer"
    APP_VERSION: str = "1.0.0-phase1"

    SECRET_KEY: str = os.environ.get("AIEVER_SECRET_KEY", "ai-ever-dev-secret-change-me")

    # Directories
    UPLOAD_FOLDER: Path = BASE_DIR / "uploads"
    LOG_FOLDER: Path = BASE_DIR / "logs"
    DATABASE_FOLDER: Path = BASE_DIR / "database"
    DATABASE_PATH: Path = DATABASE_FOLDER / "aiever.db"

    # Editor / execution limits
    MAX_CODE_SIZE_BYTES: int = 5 * 1024 * 1024   # 5 MB source limit
    MAX_CONTENT_LENGTH: int = 10 * 1024 * 1024   # request body cap
    MAX_EXECUTION_STEPS: int = 200_000           # tracer step cap
    EXECUTION_TIMEOUT_SEC: int = 30

    # SocketIO — threading mode keeps everything offline and dependency-light
    SOCKETIO_ASYNC_MODE: str = "threading"

    # Playback speeds exposed to the frontend
    PLAYBACK_SPEEDS: tuple[float, ...] = (0.25, 0.5, 1.0, 2.0, 5.0, 10.0)

    @classmethod
    def ensure_directories(cls) -> None:
        """Create runtime directories if they do not exist."""
        for folder in (cls.UPLOAD_FOLDER, cls.LOG_FOLDER, cls.DATABASE_FOLDER):
            folder.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(BaseConfig):
    """Local development settings."""

    DEBUG: bool = True
    TESTING: bool = False


class ProductionConfig(BaseConfig):
    """Production settings."""

    DEBUG: bool = False
    TESTING: bool = False


CONFIG_MAP: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None) -> type[BaseConfig]:
    """Return a config class by name (defaults to AIEVER_ENV or development)."""
    key = name or os.environ.get("AIEVER_ENV", "development")
    return CONFIG_MAP.get(key, DevelopmentConfig)
