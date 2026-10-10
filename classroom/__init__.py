"""TLU Study Assistant Web — Classroom & Realtime Subsystem.

Encapsulates slide tracking, State Engine, Teaching Advisor, Socket.IO,
concurrency offloading, and REST routers.
"""
from __future__ import annotations

import sys
import types
from fastapi import FastAPI

from . import models, schemas, services
from .concurrency import (
    AdvisorThreadPoolExecutor,
    advisor_executor,
    get_event_loop_lag_monitor,
    run_in_advisor_pool,
)
from .database import Base, SessionLocal, engine, get_db, get_db_context
from .realtime import broadcast, lecturer_room, participant_room, room, sio, shutdown as realtime_shutdown
from .routers import (
    analytics_router,
    sessions_router,
    slides_router,
    student_router,
    teaching_router,
)

# Compatibility bridging for test harnesses expecting app.modules namespace
if "app.modules" not in sys.modules:
    sys.modules["app.modules"] = types.ModuleType("app.modules")
for mod_name in [
    "llm",
    "slide_tracking",
    "state_engine",
    "advisor",
    "auto_questions",
    "session_understanding",
    "analytics",
    "assessment",
    "question_support",
    "student_coach",
    "slide_import",
    "agent_tools",
]:
    mod_obj = getattr(services, mod_name, None)
    if mod_obj is not None:
        sys.modules[f"app.modules.{mod_name}"] = mod_obj
        setattr(sys.modules["app.modules"], mod_name, mod_obj)


def register_classroom_routes(app: FastAPI) -> None:
    """Mounts all classroom REST routers into the target FastAPI app instance."""
    # Canonical /api/* routers
    app.include_router(teaching_router, prefix="/api/teaching", tags=["Classroom Teaching"])
    app.include_router(student_router, prefix="/api/student", tags=["Classroom Student"])
    app.include_router(sessions_router, prefix="/api/sessions", tags=["Classroom Sessions"])
    app.include_router(slides_router, prefix="/api/slides", tags=["Classroom Slides"])
    app.include_router(analytics_router, prefix="/api/analytics", tags=["Classroom Analytics"])

    # Legacy fallback routes for backward compatibility
    app.include_router(student_router, prefix="", include_in_schema=False)
    app.include_router(teaching_router, prefix="/teaching", include_in_schema=False)


__all__ = [
    "AdvisorThreadPoolExecutor",
    "Base",
    "SessionLocal",
    "advisor_executor",
    "analytics_router",
    "broadcast",
    "engine",
    "get_db",
    "get_db_context",
    "get_event_loop_lag_monitor",
    "lecturer_room",
    "models",
    "participant_room",
    "register_classroom_routes",
    "realtime_shutdown",
    "room",
    "run_in_advisor_pool",
    "schemas",
    "services",
    "sessions_router",
    "sio",
    "slides_router",
    "student_router",
    "teaching_router",
]
