"""Cấu hình đọc từ biến môi trường / file .env cho classroom subpackage."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _path(env_value: str) -> Path:
    p = Path(env_value)
    return p if p.is_absolute() else (BASE_DIR / p).resolve()


class Settings:
    def __init__(self) -> None:
        # LLM — Groq
        self.groq_api_key: str = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        self.ai_enabled: bool = os.getenv(
            "CLASSROOM_AI_ENABLED", os.getenv("VINLEARN_AI_ENABLED", "1")
        ).strip() not in ("0", "false", "False", "")

        # Ứng dụng
        self.jwt_secret: str = os.getenv(
            "CLASSROOM_JWT_SECRET",
            os.getenv("VINLEARN_JWT_SECRET", "dev-secret-doi-truoc-khi-trien-khai"),
        )
        self.jwt_hours: int = int(
            os.getenv("CLASSROOM_JWT_HOURS", os.getenv("VINLEARN_JWT_HOURS", "72"))
        )
        self.database_url: str = os.getenv(
            "CLASSROOM_DATABASE_URL",
            os.getenv("VINLEARN_DATABASE_URL", f"sqlite:///{BASE_DIR / 'classroom.db'}"),
        )
        self.upload_dir: Path = _path(
            os.getenv("CLASSROOM_UPLOAD_DIR", os.getenv("VINLEARN_UPLOAD_DIR", "./uploads"))
        )
        # Ảnh trang PDF đã render — phục vụ bài giảng
        self.slide_page_dir: Path = self.upload_dir / "pages"
        self.trace_dir: Path = BASE_DIR / "traces"
        self.slide_sync_timeout_seconds: int = max(
            1,
            int(
                os.getenv(
                    "CLASSROOM_SLIDE_SYNC_TIMEOUT_SECONDS",
                    os.getenv("VINLEARN_SLIDE_SYNC_TIMEOUT_SECONDS", "300"),
                )
            ),
        )

        # Ngưỡng dữ liệu
        self.min_responses: int = int(
            os.getenv("CLASSROOM_MIN_RESPONSES", os.getenv("VINLEARN_MIN_RESPONSES", "5"))
        )
        self.min_participation: float = float(
            os.getenv(
                "CLASSROOM_MIN_PARTICIPATION",
                os.getenv("VINLEARN_MIN_PARTICIPATION", "0.30"),
            )
        )
        # Ngưỡng định tuyến câu hỏi học viên
        self.confusion_threshold: float = 0.30

    @property
    def ai_available(self) -> bool:
        return self.ai_enabled and bool(self.groq_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    s.trace_dir.mkdir(parents=True, exist_ok=True)
    s.upload_dir.mkdir(parents=True, exist_ok=True)
    s.slide_page_dir.mkdir(parents=True, exist_ok=True)
    return s
