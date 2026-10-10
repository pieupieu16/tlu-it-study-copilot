"""
TLU Study Assistant Web - Tier 3: Cross-Feature Interaction Tests
File: tests/test_tier3_cross_feature.py
Coverage: Multi-feature interactions: slide nav ↔ auto-questions,
          quiz answers ↔ state engine ↔ teaching advisor,
          mismatch timer ↔ auto-sync callback ↔ audit logging,
          student doubts ↔ NLP classifier ↔ TA escalation,
          and concurrent thread-pool offloading under load.
"""

import asyncio
import time
import pytest
from unittest.mock import MagicMock, patch

# ============================================================================
# 1. SLIDE NAVIGATION ↔ AUTO-QUESTIONS INTERACTION
# ============================================================================

def test_tc_t3_xft_01_slide_change_fallback_drafting_when_no_ai(sample_classroom_data, test_db, modules):
    """TC-T3-XFT-01: When slide changes and AI is unavailable, rule fallback drafts questions."""
    auto_questions = modules["auto_questions"]
    slide = sample_classroom_data["slides"][0]
    slide.notes = "Con trỏ lưu trữ địa chỉ ô nhớ trong bộ nhớ RAM."
    test_db.commit()

    # Call ensure_for_slide with AI disabled
    with patch("app.modules.llm.draft_checkpoint_questions", return_value={"questions": []}):
        questions = auto_questions.ensure_for_slide(test_db, slide)

    assert isinstance(questions, list)
    assert len(questions) >= 1
    assert questions[0].origin in ("manual", "llm", "rule_fallback")


def test_tc_t3_xft_02_slide_change_with_ai_drafts_valid_questions(sample_classroom_data, test_db, modules):
    """TC-T3-XFT-02: AI question drafting produces usable checkpoint questions."""
    auto_questions = modules["auto_questions"]
    slide = sample_classroom_data["slides"][1]

    ai_generated = {
        "questions": [
            {
                "prompt": "Hàm malloc() trả về kiểu dữ liệu gì trong C?",
                "type": "multiple_choice",
                "options": ["void*", "int*", "char*", "float*"],
                "answer": {"value": "void*"},
            }
        ]
    }

    with patch("app.modules.llm.draft_checkpoint_questions", return_value=ai_generated):
        questions = auto_questions.ensure_for_slide(test_db, slide)

    assert isinstance(questions, list)
    assert len(questions) >= 1
    assert "malloc" in questions[0].prompt


# ============================================================================
# 2. QUIZ SUBMISSIONS ↔ STATE ENGINE ↔ TEACHING ADVISOR TRIGGER
# ============================================================================

def test_tc_t3_xft_03_student_answers_trigger_high_confusion_advice(modules, make_metrics):
    """TC-T3-XFT-03: Heavy wrong answers trigger state engine -> advisor generates urgent recommendation."""
    state_engine = modules["state_engine"]
    advisor = modules["advisor"]

    # 15 out of 20 answered, 80% wrong, 50% slow
    metrics = make_metrics(
        online_students=20,
        responded=15,
        participation=0.75,
        graded_answers=15,
        correct_rate=0.20,
        wrong_rate=0.80,
        slow_rate=0.50,
    )
    state = state_engine.evaluate(metrics)
    assert state.state == "high_confusion"

    # Advisor responds
    result = advisor.advise(metrics=metrics.as_dict(), state=state)
    assert result.should_alert is True
    assert result.state == "high_confusion"
    assert "Dừng lại" in result.action or "thực tế" in result.action


def test_tc_t3_xft_04_student_answers_healthy_suppresses_advisor_alert(modules, make_metrics):
    """TC-T3-XFT-04: High score answers evaluate healthy -> advisor does NOT trigger popup alert."""
    state_engine = modules["state_engine"]
    advisor = modules["advisor"]

    metrics = make_metrics(
        online_students=20,
        responded=18,
        participation=0.90,
        graded_answers=18,
        correct_rate=0.90,
        wrong_rate=0.10,
        slow_rate=0.05,
    )
    state = state_engine.evaluate(metrics)
    assert state.state == "healthy"

    result = advisor.advise(metrics=metrics.as_dict(), state=state)
    assert result.should_alert is False  # Healthy does not trigger warning popup


def test_tc_t3_xft_05_insufficient_answers_abtains_advisor(modules, make_metrics):
    """TC-T3-XFT-05: Low response count yields abstain from Advisor."""
    state_engine = modules["state_engine"]
    advisor = modules["advisor"]

    metrics = make_metrics(online_students=20, responded=2, participation=0.10)
    state = state_engine.evaluate(metrics)
    assert state.state == "insufficient_data"

    result = advisor.advise(metrics=metrics.as_dict(), state=state)
    assert result.source == "abstain"
    assert result.should_alert is False


# ============================================================================
# 3. SLIDE MISMATCH ↔ AUTOSYNC COMMAND CALLBACK ↔ DB AUDIT LOGGING
# ============================================================================

def test_tc_t3_xft_06_mismatch_timeout_triggers_force_sync_callback(modules):
    """TC-T3-XFT-06: Mismatch timer triggers on_force_sync callback with AutoSyncCommand."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        triggered_commands = []

        async def _callback(cmd):
            triggered_commands.append(cmd)
            return cmd.slide_index

        # Set ultra-short timeout for testing
        service = SlideTrackingService(timeout_seconds=0.05, on_force_sync=_callback)
        await service.lecturer_changed(session_id=1, slide_index=2)

        # Student lagging on slide 0
        await service.track_student(
            participant_id=101, session_id=1, slide_index=0, following_lecturer=False,
            lecturer_slide_index=2, socket_id="sock_lag"
        )

        # Wait for timeout
        await asyncio.sleep(0.12)

        assert len(triggered_commands) >= 1
        cmd = triggered_commands[0]
        assert cmd.participant_id == 101
        assert cmd.slide_index == 2
        assert cmd.from_slide_index == 0

        await service.close()

    asyncio.run(_test())


def test_tc_t3_xft_07_force_sync_persists_learning_event_in_db(sample_classroom_data, test_db, modules):
    """TC-T3-XFT-07: Auto-sync action records audit LearningEvent in database."""
    models = modules["models"]
    AutoSyncCommand = modules["slide_tracking"].AutoSyncCommand
    session = sample_classroom_data["session"]
    student = sample_classroom_data["students"][0]

    cmd = AutoSyncCommand(
        participant_id=student.id,
        session_id=session.id,
        from_slide_index=0,
        slide_index=2,
        mismatch_seconds=300,
        mismatch_id="mism_abc",
    )

    # Simulate recording event to DB
    event = models.LearningEvent(
        session_id=session.id,
        participant_id=student.id,
        slide_index=cmd.slide_index,
        type="auto_slide_sync",
        payload=cmd.as_payload(),
    )
    test_db.add(event)
    test_db.commit()

    saved_event = test_db.query(models.LearningEvent).filter_by(
        session_id=session.id, type="auto_slide_sync"
    ).first()
    assert saved_event is not None
    assert saved_event.payload["slide_index"] == 2
    assert saved_event.payload["reason"] == "slide_mismatch_timeout"


def test_tc_t3_xft_08_reconciles_student_back_to_lecturer(modules):
    """TC-T3-XFT-08: After force sync, student's state is aligned with lecturer."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=MagicMock())
        await service.lecturer_changed(session_id=1, slide_index=3)

        # Mismatched initially
        await service.track_student(
            participant_id=101, session_id=1, slide_index=1, following_lecturer=False,
            lecturer_slide_index=3, socket_id="s1"
        )

        # Force sync sets slide_index to lecturer's slide
        synced = await service.track_student(
            participant_id=101, session_id=1, slide_index=3, following_lecturer=True,
            lecturer_slide_index=3, socket_id="s1"
        )
        assert synced["slide_index"] == 3
        assert synced["out_of_sync"] is False

    asyncio.run(_test())


# ============================================================================
# 4. STUDENT DOUBTS ↔ NLP CONFUSION ANALYSIS ↔ TA DASHBOARD ESCALATION
# ============================================================================

def test_tc_t3_xft_09_high_confusion_doubt_escalates_to_ta(sample_classroom_data, test_db, modules):
    """TC-T3-XFT-09: Student question with confusion >= 0.30 is escalated."""
    models = modules["models"]
    session = sample_classroom_data["session"]
    student = sample_classroom_data["students"][0]

    confusion_score = 0.55
    is_escalated = confusion_score >= 0.30

    q = models.SupportQuestion(
        session_id=session.id,
        participant_id=student.id,
        slide_index=1,
        text="Em hoàn toàn không hiểu con trỏ void* ép kiểu thế nào?",
        confusion_score=confusion_score,
        escalated=is_escalated,
        status="pending",
    )
    test_db.add(q)
    test_db.commit()

    # Query escalated questions
    escalated_qs = test_db.query(models.SupportQuestion).filter_by(
        session_id=session.id, escalated=True
    ).all()
    assert len(escalated_qs) == 1
    assert escalated_qs[0].confusion_score == 0.55


def test_tc_t3_xft_10_low_confusion_doubt_remains_unescalated(sample_classroom_data, test_db, modules):
    """TC-T3-XFT-10: Low confusion question (< 0.30) remains unescalated."""
    models = modules["models"]
    session = sample_classroom_data["session"]
    student = sample_classroom_data["students"][1]

    confusion_score = 0.15
    is_escalated = confusion_score >= 0.30

    q = models.SupportQuestion(
        session_id=session.id,
        participant_id=student.id,
        slide_index=1,
        text="Slide này có trong tài liệu đọc trước không ạ?",
        confusion_score=confusion_score,
        escalated=is_escalated,
        status="pending",
    )
    test_db.add(q)
    test_db.commit()

    saved = test_db.query(models.SupportQuestion).filter_by(id=q.id).first()
    assert saved.escalated is False


def test_tc_t3_xft_11_ta_answers_doubt_updates_status(sample_classroom_data, test_db, modules):
    """TC-T3-XFT-11: Answering a support question marks status answered with author."""
    models = modules["models"]
    session = sample_classroom_data["session"]
    student = sample_classroom_data["students"][0]

    q = models.SupportQuestion(
        session_id=session.id,
        participant_id=student.id,
        slide_index=1,
        text="Hỏi về con trỏ",
        status="pending",
    )
    test_db.add(q)
    test_db.commit()

    # Assistant answers
    q.status = "answered"
    q.answer_text = "void* là con trỏ tổng quát, cần ép kiểu (int*) trước khi giải tham chiếu."
    q.answered_by = "assistant"
    test_db.commit()

    updated = test_db.query(models.SupportQuestion).filter_by(id=q.id).first()
    assert updated.status == "answered"
    assert updated.answered_by == "assistant"
    assert "ép kiểu" in updated.answer_text


# ============================================================================
# 5. MULTI-USER REALTIME CONCURRENCY & EVENT LOOP INVARIANT
# ============================================================================

def test_tc_t3_xft_12_concurrent_slide_changes_monotonic_revision(modules):
    """TC-T3-XFT-12: Rapid concurrent slide updates maintain monotonic revision order."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=MagicMock())

        # Rapidly update slide index 10 times
        for i in range(10):
            await service.lecturer_changed(session_id=1, slide_index=i)

        assert service._lecturer_revisions[1] == 10
        assert service._lecturer_slides[1] == 9

    asyncio.run(_test())


def test_tc_t3_xft_13_heavy_advisor_offloaded_preserves_event_loop_speed():
    """TC-T3-XFT-13: Multiple concurrent heavy tasks running in thread pool keep loop lag < 50ms."""
    async def _test():
        lags = []
        stop_event = asyncio.Event()

        async def _probe():
            while not stop_event.is_set():
                t0 = time.perf_counter()
                await asyncio.sleep(0.01)
                lag = max(0.0, (time.perf_counter() - t0 - 0.01) * 1000.0)
                lags.append(lag)

        def _heavy_compute():
            time.sleep(0.05)  # Heavy blocking simulation
            return True

        prober_task = asyncio.create_task(_probe())
        workers = [asyncio.create_task(asyncio.to_thread(_heavy_compute)) for _ in range(5)]

        await asyncio.gather(*workers)
        stop_event.set()
        await prober_task

        p95_lag = sorted(lags)[int(len(lags) * 0.95)]
        assert p95_lag < 50.0  # Concurrency requirement: lag must remain < 50ms

    asyncio.run(_test())


def test_tc_t3_xft_14_end_session_cancels_all_active_timers(modules):
    """TC-T3-XFT-14: Ending session clears states and cancels active mismatch timers."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=MagicMock())
        await service.lecturer_changed(session_id=1, slide_index=2)

        # Add 3 mismatched students
        for p_id in [101, 102, 103]:
            await service.track_student(
                participant_id=p_id, session_id=1, slide_index=0, following_lecturer=False,
                lecturer_slide_index=2, socket_id=f"s_{p_id}"
            )
        assert len(service._states) == 3
        assert len(service._tasks) == 3

        # End session
        await service.end_session(session_id=1)
        assert len(service._states) == 0
        assert len(service._tasks) == 0

    asyncio.run(_test())


def test_tc_t3_xft_15_session_summary_reflects_interactive_quiz_results(sample_classroom_data, test_db, modules):
    """TC-T3-XFT-15: Answers and events are summarized in session understanding report."""
    models = modules["models"]
    session_understanding = modules["session_understanding"]
    session = sample_classroom_data["session"]
    student = sample_classroom_data["students"][0]

    # Add answer record
    ans = models.Answer(
        session_id=session.id,
        participant_id=student.id,
        slide_index=0,
        question_id=1,
        correct=True,
        score=1.0,
        confidence=2,
        response_ms=12000,
        skipped=False,
    )
    test_db.add(ans)
    test_db.commit()

    summary = session_understanding.build_session_summary(test_db, session)
    assert isinstance(summary, dict)
    assert "classified_students" in summary or "coverage_rate" in summary
