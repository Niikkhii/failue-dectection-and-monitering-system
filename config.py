import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Settings:
    app_env: str
    db_path: str
    batch_window_size: int
    thresholds: dict[str, float]


def _default_thresholds_for_env(app_env: str) -> dict[str, float]:
    if app_env == "prod":
        return {"cpu": 75.0, "memory": 80.0, "disk": 85.0, "error_rate": 2.0}
    return {"cpu": 85.0, "memory": 90.0, "disk": 95.0, "error_rate": 5.0}


@lru_cache
def get_settings() -> Settings:
    app_env = os.getenv("APP_ENV", "dev").strip().lower()
    thresholds = _default_thresholds_for_env(app_env)
    for metric in thresholds:
        env_key = f"THRESHOLD_{metric.upper()}"
        if env_key in os.environ:
            thresholds[metric] = float(os.environ[env_key])

    batch_window_size = int(os.getenv("BATCH_WINDOW_SIZE", "10"))
    return Settings(
        app_env=app_env,
        db_path=os.getenv("DB_PATH", "monitoring.db"),
        batch_window_size=batch_window_size,
        thresholds=thresholds,
    )
