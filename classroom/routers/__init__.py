"""Classroom REST API routers."""
from __future__ import annotations

from .analytics import router as analytics_router
from .sessions import router as sessions_router
from .slides import router as slides_router
from .student import router as student_router
from .teaching import router as teaching_router

__all__ = [
    "analytics_router",
    "sessions_router",
    "slides_router",
    "student_router",
    "teaching_router",
]
