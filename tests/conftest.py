"""
TLU Study Assistant Web - Automated Test Configuration & Shared Fixtures
File: tests/conftest.py
"""

import sys
import os
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

BASE_DIR = Path(__file__).resolve().parent.parent
REF_BACKEND_DIR = Path("/tmp/k3_hackathon/codebase/backend")

# SQLAlchemy imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

def _ensure_backend_import_path():
    """Ensures REF_BACKEND_DIR is at the front of sys.path and BASE_DIR/cwd are removed."""
    while "" in sys.path:
        sys.path.remove("")
    while str(BASE_DIR) in sys.path:
        sys.path.remove(str(BASE_DIR))
    if str(REF_BACKEND_DIR) in sys.path:
        sys.path.remove(str(REF_BACKEND_DIR))
    if REF_BACKEND_DIR.exists():
        sys.path.insert(0, str(REF_BACKEND_DIR))
    if "app" in sys.modules and not hasattr(sys.modules["app"], "__path__"):
        del sys.modules["app"]

_ensure_backend_import_path()

# Module resolution helper
def get_classroom_modules():
    """
    Dynamically loads classroom modules from either tlu_study_assistant_web.classroom
    or the reference /tmp/k3_hackathon app.
    """
    try:
        if (BASE_DIR / "classroom").exists() and str(BASE_DIR) not in sys.path:
            sys.path.insert(0, str(BASE_DIR))
        import classroom
        import classroom.models as models
        import classroom.schemas as schemas
        from classroom.services import (
            slide_tracking,
            state_engine,
            advisor,
            auto_questions,
            session_understanding,
            analytics,
            assessment,
            question_support,
        )
        from classroom import realtime
        from classroom.database import Base
        return {
            "models": models,
            "schemas": schemas,
            "slide_tracking": slide_tracking,
            "state_engine": state_engine,
            "advisor": advisor,
            "auto_questions": auto_questions,
            "session_understanding": session_understanding,
            "analytics": analytics,
            "assessment": assessment,
            "question_support": question_support,
            "student_coach": getattr(classroom.services, "student_coach", None) if hasattr(classroom, "services") else None,
            "realtime": realtime,
            "Base": Base,
        }
    except (ImportError, AttributeError):
        _ensure_backend_import_path()
        from app import models, schemas, realtime
        from app.db import Base
        from app.modules import (
            slide_tracking,
            state_engine,
            advisor,
            auto_questions,
            session_understanding,
            analytics,
            assessment,
            question_support,
            student_coach,
        )
        return {
            "models": models,
            "schemas": schemas,
            "slide_tracking": slide_tracking,
            "state_engine": state_engine,
            "advisor": advisor,
            "auto_questions": auto_questions,
            "session_understanding": session_understanding,
            "analytics": analytics,
            "assessment": assessment,
            "question_support": question_support,
            "student_coach": student_coach,
            "realtime": realtime,
            "Base": Base,
        }


@pytest.fixture(scope="session")
def modules():
    return get_classroom_modules()


@pytest.fixture
def make_metrics(modules):
    """Factory fixture to create SlideMetrics with sensible defaults."""
    SlideMetrics = modules["analytics"].SlideMetrics

    def _factory(
        slide_index: int = 0,
        slide_title: str = "Slide 0: Con trỏ C++",
        online_students: int = 20,
        responded: int = 15,
        participation: float = 0.75,
        correct_rate: float = 0.50,
        wrong_rate: float = 0.50,
        skip_rate: float = 0.0,
        median_response_s: float = 20.0,
        slow_rate: float = 0.10,
        low_confidence_rate: float = 0.10,
        return_slide_count: int = 0,
        raised_hands: int = 0,
        asked_questions: int = 0,
        graded_answers: int = 15,
        top_wrong_options: list = None,
    ):
        return SlideMetrics(
            slide_index=slide_index,
            slide_title=slide_title,
            online_students=online_students,
            responded=responded,
            participation=participation,
            correct_rate=correct_rate,
            wrong_rate=wrong_rate,
            skip_rate=skip_rate,
            median_response_s=median_response_s,
            slow_rate=slow_rate,
            low_confidence_rate=low_confidence_rate,
            return_slide_count=return_slide_count,
            raised_hands=raised_hands,
            asked_questions=asked_questions,
            graded_answers=graded_answers,
            top_wrong_options=top_wrong_options or [],
        )

    return _factory


@pytest.fixture
def test_db(modules):
    """
    Creates an isolated in-memory SQLite database session for each test.
    """
    Base = modules["Base"]
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_classroom_data(test_db, modules):
    """
    Seeds database with a sample user, course, slides, room, and session.
    """
    models = modules["models"]

    # 1. Lecturer
    lecturer = models.User(
        email="gv_thanglong@tlu.edu.vn",
        password_hash="test_hash_password",
        full_name="Giảng viên Khoa CNTT",
    )
    test_db.add(lecturer)
    test_db.commit()
    test_db.refresh(lecturer)

    # 2. Course
    course = models.Course(
        title="Nhập môn lập trình C/C++ (IT101)",
        description="Khoá học lập trình cơ sở cho sinh viên K35",
        owner_id=lecturer.id,
    )
    test_db.add(course)
    test_db.commit()
    test_db.refresh(course)

    # 3. Slides
    slides = [
        models.Slide(
            course_id=course.id,
            index=0,
            title="Giới thiệu về Bộ nhớ & Con trỏ",
            blocks=[],
        ),
        models.Slide(
            course_id=course.id,
            index=1,
            title="Cấp phát bộ nhớ động",
            blocks=[],
        ),
        models.Slide(
            course_id=course.id,
            index=2,
            title="Các lỗi con trỏ kinh điển",
            blocks=[],
        ),
    ]
    test_db.add_all(slides)
    test_db.commit()

    # 4. Room
    room = models.Room(
        code="TLU01",
        name="Phòng thực hành Lab 301",
        course_id=course.id,
        owner_id=lecturer.id,
    )
    test_db.add(room)
    test_db.commit()
    test_db.refresh(room)

    # 5. Session
    session = models.Session(
        room_id=room.id,
        current_slide_index=0,
    )
    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)

    # 6. Participants (Students)
    students = [
        models.Participant(
            session_id=session.id,
            display_name="Nguyễn Văn An",
            token="token_an_k35",
            online=True,
        ),
        models.Participant(
            session_id=session.id,
            display_name="Trần Mai Linh",
            token="token_linh_k34",
            online=True,
        ),
        models.Participant(
            session_id=session.id,
            display_name="Lê Hoàng Long",
            token="token_long_k35",
            online=True,
        ),
    ]
    test_db.add_all(students)
    test_db.commit()

    return {
        "lecturer": lecturer,
        "course": course,
        "slides": slides,
        "room": room,
        "session": session,
        "students": students,
    }
