from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AID_", env_file=BACKEND_DIR / ".env", extra="ignore")

    database_url: str = f"sqlite:///{(BACKEND_DIR / 'data' / 'detections.db').as_posix()}"
    ensemble_config: Path = PROJECT_DIR / "models" / "ensemble" / "ensemble_config.json"
    evaluation_summary: Path = PROJECT_DIR / "evaluation" / "results" / "final" / "summary.json"

    max_upload_bytes: int = 15 * 1024 * 1024
    max_image_pixels: int = 50_000_000
    min_image_side: int = 32
    allowed_extensions: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    allowed_formats: tuple[str, ...] = ("JPEG", "PNG", "WEBP", "BMP")

    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")
    rate_limit_per_minute: int = 60

    device: str = "auto"  # "auto", "cpu" or "cuda"
    load_models: bool = True  # tests set this to False and inject a fake ensemble


@lru_cache
def get_settings() -> Settings:
    return Settings()
