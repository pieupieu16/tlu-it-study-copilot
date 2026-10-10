"""
TLU Study Assistant Web - Tier 4: Real-World Classroom Application Scenarios
File: tests/test_tier4_classroom_scenarios.py
Coverage: Multi-participant, multi-turn realistic classroom journeys:
          - Standard lecture flow with quizzes
          - Lagging student detection and auto-recovery
          - Severe confusion wave and Advisor intervention
          - Doubt escalation to Teaching Assistant
          - Post-lecture session understanding summary
          - Multi-tab student isolation
          - Rapid slide navigation race prevention
          - Student coaching hint generation
          - Full classroom end-to-end lifecycle
"""

import asyncio
import time
import pytest
from unittest.mock import MagicMock, patch

# ============================================================================
# SCENARIO 1: STANDARD INTERACTIVE LECTURE WORKFLOW
# ============================================================================

def test_tc_t4_scen_01_standard_lecture_workflow(sample_classroom_data, test_db, modules):
    """
    Scenario 1: Lecturer starts room session -> 3 students join -> Lecturer presents
    slides 0-2 -> Quiz opened -> Students submit correct answers -> State is healthy.
    """
    async def _test():
        models = modules["models"]
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        state_engine = modules["state_engine"]
        assessment = modules["assessment"]

        session = sample_classroom_data["session"]
        students = sample_classroom_data["students"]

        # 1. Slide Tracking Setup
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=MagicMock())
        await service.lecturer_changed(session.id, slide_index=0)

        # 2. 3 Students join and sync to slide 0
        for s in students:
            snap = await service.track_student(
                participant_id=s.id, session_id=session.id, slide_index=0,
                following_lecturer=True, lecturer_slide_index=0, socket_id=f"sock_{s.id}"
            )
            assert snap["out_of_sync"] is False

        # 3. Lecturer advances to slide 1
        await service.lecturer_changed(session.id, slide_index=1)
        session.current_slide_index = 1
        test_db.commit()

        # 4. Students follow lecturer to slide 1
        for s in students:
            snap = await service.track_student(
                participant_id=s.id, session_id=session.id, slide_index=1,
                following_lecturer=True, lecturer_slide_index=1, socket_id=f"sock_{s.id}"
            )
            assert snap["slide_index"] == 1
            assert snap["out_of_sync"] is False

        # 5. Checkpoint Quiz: All 3 students submit correct answers
        answer_key = {"value": "void*"}
        for s in students:
            correct, score = assessment.grade("multiple_choice", answer_key, {"value": "void*"})
            ans = models.Answer(
                session_id=session.id,
                participant_id=s.id,
                slide_index=1,
                question_id=1,
                correct=correct,
                score=score,
                confidence=2,
                response_ms=15000,
                skipped=False,
            )
            test_db.add(ans)
        test_db.commit()

        # 6. State Engine evaluation
        SlideMetrics = modules["analytics"].SlideMetrics
        metrics = SlideMetrics(
            slide_index=1,
            slide_title="Cấp phát bộ nhớ động",
            online_students=6,
            responded=6,
            participation=1.0,
            correct_rate=1.0,
            wrong_rate=0.0,
            skip_rate=0.0,
            median_response_s=15.0,
            slow_rate=0.0,
            low_confidence_rate=0.0,
            return_slide_count=0,
            raised_hands=0,
            asked_questions=0,
            graded_answers=6,
        )
        state = state_engine.evaluate(metrics)
        assert state.state == "healthy"
        assert state.severity == 1

    asyncio.run(_test())


# ============================================================================
# SCENARIO 2: LAGGING STUDENT DETECTION AND AUTO-RECOVERY
# ============================================================================

def test_tc_t4_scen_02_lagging_student_auto_recovery(sample_classroom_data, test_db, modules):
    """
    Scenario 2: Student A drifts back to slide 0 while Lecturer is on slide 2.
    Timer triggers AutoSyncCommand -> Student client forced back to slide 2.
    """
    async def _test():
        models = modules["models"]
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        session = sample_classroom_data["session"]
        student_a = sample_classroom_data["students"][0]

        sync_commands = []

        async def _sync_handler(cmd):
            sync_commands.append(cmd)
            # Persist event in DB
            evt = models.LearningEvent(
                session_id=cmd.session_id,
                participant_id=cmd.participant_id,
                slide_index=cmd.slide_index,
                type="auto_slide_sync",
                payload=cmd.as_payload(),
            )
            test_db.add(evt)
            test_db.commit()
            return cmd.slide_index

        service = SlideTrackingService(timeout_seconds=0.05, on_force_sync=_sync_handler)
        await service.lecturer_changed(session.id, slide_index=2)

        # Student A stays on slide 0
        await service.track_student(
            participant_id=student_a.id, session_id=session.id, slide_index=0,
            following_lecturer=False, lecturer_slide_index=2, socket_id="sock_a"
        )

        # Wait for deadline expiry
        await asyncio.sleep(0.12)

        assert len(sync_commands) == 1
        cmd = sync_commands[0]
        assert cmd.participant_id == student_a.id
        assert cmd.slide_index == 2
        assert cmd.from_slide_index == 0

        # Verify DB audit trail
        logged = test_db.query(models.LearningEvent).filter_by(
            session_id=session.id, type="auto_slide_sync"
        ).first()
        assert logged is not None
        assert logged.payload["sync_id"] == cmd.sync_id

        await service.close()

    asyncio.run(_test())


# ============================================================================
# SCENARIO 3: HIGH CONFUSION WAVE AND ADVISOR INTERVENTION
# ============================================================================

def test_tc_t4_scen_03_high_confusion_advisor_intervention(modules, make_metrics):
    """
    Scenario 3: Difficult slide causes 80% wrong answers with slow responses.
    State engine classifies high_confusion -> Advisor pops up structured advice.
    """
    state_engine = modules["state_engine"]
    advisor = modules["advisor"]

    # 10 students, 8 wrong answers, 5 slow answers (>45s)
    metrics = make_metrics(
        slide_index=2,
        slide_title="Các lỗi con trỏ kinh điển (Memory leak)",
        online_students=12,
        responded=10,
        participation=0.833,
        graded_answers=10,
        correct_rate=0.20,
        wrong_rate=0.80,
        slow_rate=0.50,
        median_response_s=52.0,
    )
    state = state_engine.evaluate(metrics)
    assert state.state == "high_confusion"
    assert state.severity == 7

    advice = advisor.advise(metrics=metrics.as_dict(), state=state)
    assert advice.should_alert is True
    assert len(advice.headline) <= 60
    assert len(advice.action) <= 140
    # Must contain actionable guidance
    assert "Dừng lại" in advice.action or "ví dụ" in advice.action


# ============================================================================
# SCENARIO 4: STUDENT DOUBT ESCALATION TO TEACHING ASSISTANT
# ============================================================================

def test_tc_t4_scen_04_doubt_escalation_to_ta(sample_classroom_data, test_db, modules):
    """
    Scenario 4: Student asks obscure doubt -> Confusion score = 0.72 -> Escalates to TA ->
    TA provides answer -> Marked answered.
    """
    models = modules["models"]
    session = sample_classroom_data["session"]
    student = sample_classroom_data["students"][1]

    # 1. Student submits doubt
    doubt_text = "Tại sao sizeof(p) lại bằng 8 trên máy 64-bit bất kể kiểu con trỏ là char hay int?"
    confusion_score = 0.72

    doubt = models.SupportQuestion(
        session_id=session.id,
        participant_id=student.id,
        slide_index=0,
        text=doubt_text,
        confusion_score=confusion_score,
        escalated=confusion_score >= 0.30,
        status="pending",
    )
    test_db.add(doubt)
    test_db.commit()

    assert doubt.escalated is True
    assert doubt.status == "pending"

    # 2. TA answers the question
    doubt.answer_text = "Vì trên kiến trúc 64-bit, mọi địa chỉ bộ nhớ đều có độ dài 64 bit (8 bytes)."
    doubt.answered_by = "assistant"
    doubt.status = "answered"
    test_db.commit()

    # 3. Verification
    refreshed = test_db.query(models.SupportQuestion).filter_by(id=doubt.id).first()
    assert refreshed.status == "answered"
    assert refreshed.answered_by == "assistant"
    assert "64-bit" in refreshed.answer_text


# ============================================================================
# SCENARIO 5: POST-LECTURE SESSION UNDERSTANDING ANALYTICS
# ============================================================================

def test_tc_t4_scen_05_session_understanding_analytics(sample_classroom_data, test_db, modules):
    """
    Scenario 5: End-of-class session summary calculates topic mastery distribution
    with strict privacy preservation (no raw student tokens).
    """
    models = modules["models"]
    session_understanding = modules["session_understanding"]
    session = sample_classroom_data["session"]
    students = sample_classroom_data["students"]

    # Student 0: Understood (correct, confident)
    test_db.add(models.Answer(
        session_id=session.id, participant_id=students[0].id, slide_index=0,
        question_id=1, correct=True, score=1.0, confidence=2, response_ms=10000, skipped=False
    ))

    # Student 1: Temporary (unsure)
    test_db.add(models.Answer(
        session_id=session.id, participant_id=students[1].id, slide_index=0,
        question_id=1, correct=False, score=0.0, confidence=1, response_ms=25000, skipped=False
    ))

    # Student 2: Not understood (wrong and unsure)
    test_db.add(models.Answer(
        session_id=session.id, participant_id=students[2].id, slide_index=0,
        question_id=1, correct=False, score=0.0, confidence=0, response_ms=50000, skipped=False
    ))
    test_db.commit()

    summary = session_understanding.build_session_summary(test_db, session)
    assert isinstance(summary, dict)
    assert summary["classified_students"] == 3
    # Privacy verification: no participant token in summary keys
    summary_str = str(summary)
    for s in students:
        assert s.token not in summary_str


# ============================================================================
# SCENARIO 6: MULTI-TAB STUDENT TAB ISOLATION
# ============================================================================

def test_tc_t4_scen_06_multi_tab_student_isolation(modules):
    """
    Scenario 6: Student uses 2 browser tabs simultaneously. Tab 1 is following lecturer,
    Tab 2 is reviewing previous slides. Both states remain independently tracked.
    """
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=MagicMock())
        await service.lecturer_changed(session_id=1, slide_index=3)

        # Tab 1: following lecturer on slide 3
        tab1_snap = await service.track_student(
            participant_id=101, session_id=1, slide_index=3, following_lecturer=True,
            lecturer_slide_index=3, socket_id="tab_active"
        )
        # Tab 2: reviewing slide 1
        tab2_snap = await service.track_student(
            participant_id=101, session_id=1, slide_index=1, following_lecturer=False,
            lecturer_slide_index=3, socket_id="tab_review"
        )

        assert tab1_snap["out_of_sync"] is False
        assert tab2_snap["out_of_sync"] is True

        # Detaching tab 2 leaves tab 1 active
        await service.detach_socket("tab_review")
        assert len(service._states) == 1
        key1 = service._state_key(101, "tab_active")
        assert key1 in service._states

    asyncio.run(_test())


# ============================================================================
# SCENARIO 7: RAPID SLIDE NAVIGATION RACE CONDITION PREVENTION
# ============================================================================

def test_tc_t4_scen_07_rapid_slide_navigation_monotonicity(modules):
    """
    Scenario 7: Lecturer flips through slides in rapid succession. Revision counter
    increments strictly monotonically preventing stale out-of-order broadcasts.
    """
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=MagicMock())

        revisions = []
        for slide_idx in range(6):
            await service.lecturer_changed(session_id=1, slide_index=slide_idx)
            revisions.append(service._lecturer_revisions.get(1, 0))

        # Check monotonic increase: rev[i] < rev[i+1]
        for i in range(len(revisions) - 1):
            assert revisions[i] < revisions[i + 1]

        assert service._lecturer_slides.get(1) == 5

    asyncio.run(_test())


# ============================================================================
# SCENARIO 8: STUDENT COACHING HINT GENERATION
# ============================================================================

def test_tc_t4_scen_08_student_coach_suggestions(modules):
    """
    Scenario 8: Student stalled on a slide gets 3 suggested inquiry questions
    written in first person without revealing answers.
    """
    coach = modules["student_coach"]
    
    # Mock LLM suggestions
    mock_suggestions = {
        "questions": [
            "Em chưa rõ con trỏ NULL khác gì con trỏ chưa khởi tạo?",
            "Khi nào thì toán tử * đóng vai trò là kiểu, khi nào là toán tử?",
            "Tại sao cần giải phóng bộ nhớ động bằng free()?",
        ]
    }
    with patch("app.modules.llm.suggest_student_questions", return_value=mock_suggestions):
        result = coach.suggest(
            slide_title="Con trỏ C++",
            slide_text="Khái niệm con trỏ NULL và vùng nhớ Heap.",
            signals={"stalled": True},
        )

    assert result is not None
    # Result contains questions for student
    questions = result.questions if hasattr(result, "questions") else result
    assert len(questions) >= 1
    assert any("Em chưa rõ" in q for q in questions)


# ============================================================================
# SCENARIO 9: COMPLETE CLASSROOM LIFECYCLE INTEGRATION
# ============================================================================

def test_tc_t4_scen_09_full_classroom_lifecycle(sample_classroom_data, test_db, modules):
    """
    Scenario 9: Full lifecycle:
    User/Course -> Room -> Session -> Slide traversal -> Quiz answer -> Post session summary.
    """
    async def _test():
        models = modules["models"]
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        session_understanding = modules["session_understanding"]

        session = sample_classroom_data["session"]
        student = sample_classroom_data["students"][0]

        # 1. Slide Tracking Service
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=MagicMock())
        await service.lecturer_changed(session.id, slide_index=0)
        await service.track_student(
            participant_id=student.id, session_id=session.id, slide_index=0,
            following_lecturer=True, lecturer_slide_index=0, socket_id="sock_full"
        )

        # 2. Advance to slide 1
        await service.lecturer_changed(session.id, slide_index=1)
        session.current_slide_index = 1
        test_db.commit()

        # 3. Answer submitted
        test_db.add(models.Answer(
            session_id=session.id, participant_id=student.id, slide_index=1,
            question_id=1, correct=True, score=1.0, confidence=2, response_ms=10000, skipped=False
        ))
        test_db.commit()

        # 4. End session
        session.status = "ended"
        session.ended_at = models.utcnow()
        test_db.commit()
        await service.end_session(session.id)

        # 5. Build summary
        summary = session_understanding.build_session_summary(test_db, session)
        assert summary["classified_students"] == 1
        assert len(service._states) == 0

    asyncio.run(_test())


# ============================================================================
# SCENARIO 10: CONCURRENT MULTI-SESSION ISOLATION
# ============================================================================

def test_tc_t4_scen_10_concurrent_multi_session_isolation(modules):
    """
    Scenario 10: Two parallel classroom sessions running concurrently maintain
    strict slide state, revision, and participant separation.
    """
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=MagicMock())

        # Session 1: Lab 301 at slide 2
        await service.lecturer_changed(session_id=101, slide_index=2)
        # Session 2: Lab 302 at slide 5
        await service.lecturer_changed(session_id=102, slide_index=5)

        # Participant in session 1
        s1 = await service.track_student(
            participant_id=1, session_id=101, slide_index=2, following_lecturer=True,
            lecturer_slide_index=2, socket_id="sock_s1"
        )
        # Participant in session 2
        s2 = await service.track_student(
            participant_id=2, session_id=102, slide_index=5, following_lecturer=True,
            lecturer_slide_index=5, socket_id="sock_s2"
        )

        assert s1["lecturer_slide_index"] == 2
        assert s2["lecturer_slide_index"] == 5

        # End Session 1 only
        await service.end_session(session_id=101)
        assert service._lecturer_slides.get(101) is None
        assert service._lecturer_slides.get(102) == 5
        assert len(service._states) == 1

    asyncio.run(_test())
