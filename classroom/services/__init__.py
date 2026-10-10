"""Classroom subsystem services."""
from __future__ import annotations

from . import (
    advisor,
    agent_tools,
    analytics,
    assessment,
    auto_questions,
    llm,
    question_support,
    session_understanding,
    slide_import,
    slide_tracking,
    state_engine,
    student_coach,
)
from .advisor import AdviceResult, advise, rule_fallback, screen_request
from .analytics import SlideMetrics, collect
from .assessment import grade
from .auto_questions import ensure_for_slide, is_meaningful, usable_questions
from .question_support import answer, classify, summarize
from .session_understanding import build_session_summary
from .slide_import import page_image_url, parse_pdf, parse_pptx, slide_plain_text
from .slide_tracking import AutoSyncCommand, SlideTrackingService
from .state_engine import ALERT_STATES, ClassroomState, evaluate
from .student_coach import HintResult, suggest

__all__ = [
    "ALERT_STATES",
    "AdviceResult",
    "AutoSyncCommand",
    "ClassroomState",
    "HintResult",
    "SlideMetrics",
    "SlideTrackingService",
    "advisor",
    "advise",
    "agent_tools",
    "analytics",
    "answer",
    "assessment",
    "auto_questions",
    "build_session_summary",
    "classify",
    "collect",
    "ensure_for_slide",
    "evaluate",
    "grade",
    "is_meaningful",
    "llm",
    "page_image_url",
    "parse_pdf",
    "parse_pptx",
    "question_support",
    "rule_fallback",
    "screen_request",
    "session_understanding",
    "slide_import",
    "slide_plain_text",
    "slide_tracking",
    "state_engine",
    "student_coach",
    "suggest",
    "summarize",
    "usable_questions",
]
