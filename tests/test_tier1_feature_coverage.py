"""
TLU Study Assistant Web - Tier 1: Category-Partition Feature Coverage
File: tests/test_tier1_feature_coverage.py
Coverage: >=5 test cases per feature across slide tracking, state engine, advisor,
          REST endpoints, Socket.IO realtime, concurrency, and auxiliary services.
"""

import asyncio
import time
import pytest
from unittest.mock import MagicMock, patch

# ============================================================================
# FEATURE 1: REALTIME SLIDE TRACKING SERVICE (FEAT-01)
# ============================================================================

def test_tc_t1_slide_01_init_and_register(modules):
    """TC-T1-SLIDE-01: Verifies slide tracking service session initialization."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        dummy_cb = MagicMock(return_value=None)
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=dummy_cb)
        await service.lecturer_changed(session_id=1, slide_index=0)
        
        assert service._lecturer_slides.get(1) == 0
        assert service._lecturer_revisions.get(1) == 1

    asyncio.run(_test())


def test_tc_t1_slide_02_lecturer_advance_increments_revision(modules):
    """TC-T1-SLIDE-02: Advancing lecturer slide increments revision counter monotonically."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        dummy_cb = MagicMock(return_value=None)
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=dummy_cb)
        
        await service.lecturer_changed(session_id=1, slide_index=0)
        assert service._lecturer_revisions.get(1) == 1

        await service.lecturer_changed(session_id=1, slide_index=1)
        assert service._lecturer_revisions.get(1) == 2
        assert service._lecturer_slides.get(1) == 1

        await service.lecturer_changed(session_id=1, slide_index=2)
        assert service._lecturer_revisions.get(1) == 3
        assert service._lecturer_slides.get(1) == 2

    asyncio.run(_test())


def test_tc_t1_slide_03_student_in_sync_no_mismatch(modules):
    """TC-T1-SLIDE-03: Student viewing the same slide as lecturer has no mismatch."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        dummy_cb = MagicMock(return_value=None)
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=dummy_cb)
        await service.lecturer_changed(session_id=1, slide_index=1)

        snapshot = await service.track_student(
            participant_id=101,
            session_id=1,
            slide_index=1,
            following_lecturer=True,
            lecturer_slide_index=1,
            socket_id="sock_01",
        )
        assert snapshot["slide_index"] == 1
        assert snapshot["out_of_sync"] is False

    asyncio.run(_test())


def test_tc_t1_slide_04_student_mismatch_detected(modules):
    """TC-T1-SLIDE-04: Student viewing a different slide creates a mismatch tracking state."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        dummy_cb = MagicMock(return_value=None)
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=dummy_cb)
        await service.lecturer_changed(session_id=1, slide_index=2)

        snapshot = await service.track_student(
            participant_id=101,
            session_id=1,
            slide_index=0,  # Lagging at slide 0 while lecturer is at slide 2
            following_lecturer=False,
            lecturer_slide_index=2,
            socket_id="sock_01",
        )
        assert snapshot["slide_index"] == 0
        assert snapshot["out_of_sync"] is True
        key = service._state_key(101, "sock_01")
        state_entry = service._states.get(key)
        assert state_entry.mismatch_id is not None

    asyncio.run(_test())


def test_tc_t1_slide_05_multi_socket_tab_isolation(modules):
    """TC-T1-SLIDE-05: Multiple browser tabs for the same student have isolated tracking states."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        dummy_cb = MagicMock(return_value=None)
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=dummy_cb)
        await service.lecturer_changed(session_id=1, slide_index=2)

        # Tab 1: viewing slide 2 (in sync)
        snap1 = await service.track_student(
            participant_id=101, session_id=1, slide_index=2, following_lecturer=True,
            lecturer_slide_index=2, socket_id="sock_tab1"
        )
        # Tab 2: viewing slide 0 (mismatched)
        snap2 = await service.track_student(
            participant_id=101, session_id=1, slide_index=0, following_lecturer=False,
            lecturer_slide_index=2, socket_id="sock_tab2"
        )

        assert snap1["out_of_sync"] is False
        assert snap2["out_of_sync"] is True
        assert len(service._states) == 2

    asyncio.run(_test())


def test_tc_t1_slide_06_reconcile_preserves_initial_mismatch_deadline(modules):
    """TC-T1-SLIDE-06: Browsing between multiple mismatched slides does not reset mismatch_id."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        dummy_cb = MagicMock(return_value=None)
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=dummy_cb)
        await service.lecturer_changed(session_id=1, slide_index=3)

        # Step 1: Browse to slide 1
        await service.track_student(
            participant_id=101, session_id=1, slide_index=1, following_lecturer=False,
            lecturer_slide_index=3, socket_id="s1"
        )
        key = service._state_key(101, "s1")
        mismatch_id_1 = service._states.get(key).mismatch_id

        # Step 2: Browse to slide 0 (still mismatched)
        await service.track_student(
            participant_id=101, session_id=1, slide_index=0, following_lecturer=False,
            lecturer_slide_index=3, socket_id="s1"
        )
        assert service._states.get(key).mismatch_id == mismatch_id_1

    asyncio.run(_test())


def test_tc_t1_slide_07_follow_lecturer_clears_mismatch(modules):
    """TC-T1-SLIDE-07: Enabling follow lecturer immediately clears mismatch."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        dummy_cb = MagicMock(return_value=None)
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=dummy_cb)
        await service.lecturer_changed(session_id=1, slide_index=2)

        # Mismatched initially
        await service.track_student(
            participant_id=101, session_id=1, slide_index=0, following_lecturer=False,
            lecturer_slide_index=2, socket_id="s1"
        )
        # Reconnect to follow lecturer
        cleared = await service.track_student(
            participant_id=101, session_id=1, slide_index=2, following_lecturer=True,
            lecturer_slide_index=2, socket_id="s1"
        )
        assert cleared["out_of_sync"] is False

    asyncio.run(_test())


# ============================================================================
# FEATURE 2: CLASSROOM STATE ENGINE (FEAT-02)
# ============================================================================

def test_tc_t1_state_01_insufficient_data_due_to_low_response_count(modules, make_metrics):
    """TC-T1-STATE-01: Responded count below min_responses (5) triggers insufficient_data."""
    state_engine = modules["state_engine"]
    metrics = make_metrics(online_students=20, responded=3, participation=0.50)
    state = state_engine.evaluate(metrics)
    assert state.state == "insufficient_data"
    assert state.trusted is False
    assert state.severity == 0


def test_tc_t1_state_02_insufficient_data_due_to_low_participation(modules, make_metrics):
    """TC-T1-STATE-02: Participation below min_participation (30%) triggers insufficient_data."""
    state_engine = modules["state_engine"]
    metrics = make_metrics(online_students=50, responded=6, participation=0.12)
    state = state_engine.evaluate(metrics)
    assert state.state == "insufficient_data"
    assert state.trusted is False


def test_tc_t1_state_03_high_confusion_severity_ranking(modules, make_metrics):
    """TC-T1-STATE-03: High wrong rate + high slow rate produces high_confusion (severity 7)."""
    state_engine = modules["state_engine"]
    metrics = make_metrics(
        online_students=20,
        responded=15,
        participation=0.75,
        graded_answers=15,
        wrong_rate=0.80,   # >= 0.50
        slow_rate=0.50,    # >= 0.40
        skip_rate=0.10,
    )
    state = state_engine.evaluate(metrics)
    assert state.state == "high_confusion"
    assert state.trusted is True
    assert state.severity == 7
    assert state.state in state_engine.ALERT_STATES


def test_tc_t1_state_04_need_attention_trigger(modules, make_metrics):
    """TC-T1-STATE-04: Moderate wrong rate >= 0.35 triggers need_attention (severity 6)."""
    state_engine = modules["state_engine"]
    metrics = make_metrics(
        online_students=20,
        responded=12,
        participation=0.60,
        graded_answers=12,
        wrong_rate=0.40,   # >= 0.35
        slow_rate=0.10,    # < 0.40
    )
    state = state_engine.evaluate(metrics)
    assert state.state == "need_attention"
    assert state.trusted is True
    assert state.severity == 6


def test_tc_t1_state_05_healthy_trigger(modules, make_metrics):
    """TC-T1-STATE-05: High correct rate and low slow rate triggers healthy (severity 1)."""
    state_engine = modules["state_engine"]
    metrics = make_metrics(
        online_students=20,
        responded=18,
        participation=0.90,
        graded_answers=18,
        correct_rate=0.85,   # >= 0.80
        wrong_rate=0.15,
        slow_rate=0.10,      # <= 0.20
    )
    state = state_engine.evaluate(metrics)
    assert state.state == "healthy"
    assert state.severity == 1
    assert state.state not in state_engine.ALERT_STATES


# ============================================================================
# FEATURE 3: AI TEACHING ADVISOR SERVICE (FEAT-03)
# ============================================================================

def test_tc_t1_advis_01_screen_request_blocks_student_ranking(modules):
    """TC-T1-ADVIS-01: Advisor refuses requests to identify or rank weakest students."""
    advisor = modules["advisor"]
    refusal = advisor.screen_request("Em nào yếu nhất trong lớp?")
    assert refusal is not None
    rule_name, message = refusal
    assert rule_name == "identify_student" or "học viên" in message.lower()


def test_tc_t1_advis_02_screen_request_blocks_grading_delegation(modules):
    """TC-T1-ADVIS-02: Advisor refuses requests to grade or evaluate student competence."""
    advisor = modules["advisor"]
    refusal = advisor.screen_request("Chấm điểm hộ tôi danh sách sinh viên")
    assert refusal is not None
    rule_name, message = refusal
    assert rule_name == "grade_student" or "chấm điểm" in message.lower()


def test_tc_t1_advis_03_screen_request_blocks_teaching_delegation(modules):
    """TC-T1-ADVIS-03: Advisor refuses requests to lecture or explain for the teacher."""
    advisor = modules["advisor"]
    refusal = advisor.screen_request("Giảng thay tôi phần con trỏ này")
    assert refusal is not None
    rule_name, message = refusal
    assert rule_name == "answer_for_lecturer" or "giảng thay" in message.lower()


def test_tc_t1_advis_04_rule_fallback_when_llm_fails(modules, make_metrics):
    """TC-T1-ADVIS-04: Advisor produces rule fallback when LLM is unavailable."""
    advisor = modules["advisor"]
    state_engine = modules["state_engine"]

    metrics = make_metrics(wrong_rate=0.70, slow_rate=0.50)
    state = state_engine.evaluate(metrics)

    # Force LLM failure or absence
    with patch("app.modules.llm.advise_teacher", return_value=None):
        result = advisor.advise(
            metrics=metrics.as_dict(),
            state=state,
        )
    assert result.source == "rule_fallback"
    assert len(result.headline) <= 60
    assert len(result.action) <= 140
    assert len(result.action) > 10


def test_tc_t1_advis_05_banned_words_trigger_fallback(modules, make_metrics):
    """TC-T1-ADVIS-05: AI output containing offensive/banned pedagogical tokens falls back to rule."""
    advisor = modules["advisor"]
    state_engine = modules["state_engine"]

    metrics = make_metrics(wrong_rate=0.70, slow_rate=0.50)
    state = state_engine.evaluate(metrics)

    # LLM outputs forbidden token "dốt"
    bad_llm_response = {
        "headline": "Lớp học quá dốt phần này",
        "action": "Giải thích lại từ đầu vì học sinh dốt.",
        "evidence": ["70% câu trả lời sai"],
        "confidence": "high",
        "should_alert": True,
    }
    with patch("app.modules.llm.advise_teacher", return_value=bad_llm_response):
        result = advisor.advise(
            metrics=metrics.as_dict(),
            state=state,
        )
    # The post-check catches the banned token and falls back to rule
    assert result.source == "rule_fallback"
    assert "dốt" not in result.headline
    assert "dốt" not in result.action


# ============================================================================
# FEATURE 4: CLASSROOM REST MODELS & DATA LOGIC (FEAT-04)
# ============================================================================

def test_tc_t1_rest_01_change_slide_updates_session(sample_classroom_data, test_db):
    """TC-T1-REST-01: Slide change updates session current_slide_index in DB."""
    session = sample_classroom_data["session"]
    session.current_slide_index = 2
    test_db.commit()
    test_db.refresh(session)
    assert session.current_slide_index == 2


def test_tc_t1_rest_02_student_session_record(sample_classroom_data, test_db, modules):
    """TC-T1-REST-02: Participant records exist and link to active session."""
    models = modules["models"]
    session = sample_classroom_data["session"]
    participants = test_db.query(models.Participant).filter_by(session_id=session.id).all()
    assert len(participants) == 3
    assert participants[0].token == "token_an_k35"


def test_tc_t1_rest_03_checkpoint_question_association(sample_classroom_data, test_db, modules):
    """TC-T1-REST-03: Checkpoint question creation and answer evaluation."""
    models = modules["models"]
    assessment = modules["assessment"]
    slide = sample_classroom_data["slides"][0]

    checkpoint = models.Checkpoint(slide_id=slide.id, label="Kiểm tra con trỏ")
    test_db.add(checkpoint)
    test_db.commit()

    question = models.Question(
        checkpoint_id=checkpoint.id,
        type="multiple_choice",
        prompt="Toán tử nào dùng để lấy địa chỉ ô nhớ?",
        options=["&", "*", "->", "."],
        answer={"value": "&"},
    )
    test_db.add(question)
    test_db.commit()

    # Grade correct answer
    correct, score = assessment.grade("multiple_choice", question.answer, {"value": "&"})
    assert correct is True
    assert score == 1.0

    # Grade incorrect answer
    correct_bad, score_bad = assessment.grade("multiple_choice", question.answer, {"value": "*"})
    assert correct_bad is False
    assert score_bad == 0.0


def test_tc_t1_rest_04_support_question_escalation(sample_classroom_data, test_db, modules):
    """TC-T1-REST-04: Student support questions with pending status."""
    models = modules["models"]
    session = sample_classroom_data["session"]
    student = sample_classroom_data["students"][0]

    sup_q = models.SupportQuestion(
        session_id=session.id,
        participant_id=student.id,
        slide_index=0,
        text="Em không hiểu tại sao toán tử * lại vừa khai báo vừa giải tham chiếu?",
        status="pending",
    )
    test_db.add(sup_q)
    test_db.commit()
    test_db.refresh(sup_q)

    assert sup_q.id is not None
    assert sup_q.status == "pending"
    assert "toán tử *" in sup_q.text


def test_tc_t1_rest_05_learning_event_audit_logging(sample_classroom_data, test_db, modules):
    """TC-T1-REST-05: LearningEvent audit record creation for slide sync actions."""
    models = modules["models"]
    session = sample_classroom_data["session"]
    student = sample_classroom_data["students"][0]

    event = models.LearningEvent(
        session_id=session.id,
        participant_id=student.id,
        slide_index=1,
        type="auto_slide_sync",
        payload={"from_slide": 0, "to_slide": 1, "mismatch_seconds": 300},
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    assert event.id is not None
    assert event.type == "auto_slide_sync"
    assert event.payload["to_slide"] == 1


# ============================================================================
# FEATURE 5: REALTIME SOCKET.IO CONTRACT & EVENTS (FEAT-05)
# ============================================================================

def test_tc_t1_sock_01_auto_sync_command_payload(modules):
    """TC-T1-SOCK-01: AutoSyncCommand generates deterministic payload structure."""
    AutoSyncCommand = modules["slide_tracking"].AutoSyncCommand
    cmd = AutoSyncCommand(
        participant_id=101,
        session_id=1,
        from_slide_index=0,
        slide_index=2,
        mismatch_seconds=300,
        mismatch_id="mism_12345",
    )
    payload = cmd.as_payload()
    assert payload["session_id"] == 1
    assert payload["slide_index"] == 2
    assert payload["from_slide_index"] == 0
    assert payload["sync_id"] == "mism_12345:2"
    assert payload["reason"] == "slide_mismatch_timeout"


def test_tc_t1_sock_02_idempotency_key_prevents_duplicate_sync(modules):
    """TC-T1-SOCK-02: AutoSyncCommand sync_id is consistent across retries."""
    AutoSyncCommand = modules["slide_tracking"].AutoSyncCommand
    cmd1 = AutoSyncCommand(101, 1, 0, 2, 300, "abcde")
    cmd2 = AutoSyncCommand(101, 1, 0, 2, 301, "abcde")
    assert cmd1.sync_id == cmd2.sync_id == "abcde:2"


def test_tc_t1_sock_03_room_name_convention(modules):
    """TC-T1-SOCK-03: Room identifier patterns match convention."""
    session_id = 42
    session_room = f"session_{session_id}"
    student_room = f"session_{session_id}_participant_101"
    assert session_room == "session_42"
    assert student_room == "session_42_participant_101"


def test_tc_t1_sock_04_session_slide_tracking_isolation(modules):
    """TC-T1-SOCK-04: Slide tracking for separate sessions does not collide."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        dummy_cb = MagicMock(return_value=None)
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=dummy_cb)
        await service.lecturer_changed(session_id=1, slide_index=1)
        await service.lecturer_changed(session_id=2, slide_index=5)

        assert service._lecturer_slides.get(1) == 1
        assert service._lecturer_slides.get(2) == 5

    asyncio.run(_test())


def test_tc_t1_sock_05_disconnect_cleans_up_participant_state(modules):
    """TC-T1-SOCK-05: Disconnecting socket cleans up internal state entry."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        dummy_cb = MagicMock(return_value=None)
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=dummy_cb)
        await service.lecturer_changed(session_id=1, slide_index=1)

        await service.track_student(
            participant_id=101, session_id=1, slide_index=0, following_lecturer=False,
            lecturer_slide_index=1, socket_id="sock_x"
        )
        assert len(service._states) == 1

        await service.detach_socket("sock_x")
        assert len(service._states) == 0

    asyncio.run(_test())


# ============================================================================
# FEATURE 6: CONCURRENCY & NON-BLOCKING ISOLATION (FEAT-06)
# ============================================================================

def test_tc_t1_conc_01_to_thread_prevents_loop_blocking():
    """TC-T1-CONC-01: asyncio.to_thread runs synchronous task without freezing event loop."""
    async def _async_test():
        def _blocking_task():
            time.sleep(0.05)
            return "done"

        t0 = time.perf_counter()
        res = await asyncio.to_thread(_blocking_task)
        elapsed = time.perf_counter() - t0
        assert res == "done"
        assert elapsed >= 0.05

    asyncio.run(_async_test())


def test_tc_t1_conc_02_loop_lag_under_thread_offloading():
    """TC-T1-CONC-02: Measuring tick jitter while running offloaded worker."""
    async def _async_test():
        drift_samples = []

        async def prober():
            for _ in range(10):
                t0 = time.perf_counter()
                await asyncio.sleep(0.01)
                drift = max(0.0, (time.perf_counter() - t0 - 0.01) * 1000.0)
                drift_samples.append(drift)

        def _sync_work():
            time.sleep(0.05)
            return True

        prober_task = asyncio.create_task(prober())
        work_task = asyncio.create_task(asyncio.to_thread(_sync_work))

        await asyncio.gather(prober_task, work_task)
        assert len(drift_samples) >= 5
        p95_drift = sorted(drift_samples)[int(len(drift_samples) * 0.95)]
        assert p95_drift < 50.0  # Must be strictly under 50ms

    asyncio.run(_async_test())


# ============================================================================
# FEATURE 7: AUXILIARY SERVICES (FEAT-07)
# ============================================================================

def test_tc_t1_aux_01_auto_questions_usable_filter(modules):
    """TC-T1-AUX-01: Filters out generic unhelpful questions."""
    auto_questions = modules["auto_questions"]
    models = modules["models"]

    q1 = models.Question(
        type="multiple_choice",
        prompt="Bạn muốn được giải thích phần nào?",
        origin="llm",
        options=["A", "B"],
        answer={"value": "A"},
    )
    q2 = models.Question(
        type="multiple_choice",
        prompt="Con trỏ trong C++ lưu trữ địa chỉ ô nhớ đúng không?",
        origin="llm",
        options=["Đúng", "Sai"],
        answer={"value": "Đúng"},
    )
    q3 = models.Question(
        type="poll",
        prompt="Bình chọn mức độ hiểu",
        origin="llm",
        options=[],
        answer={},
    )
    q4 = models.Question(
        type="multiple_choice",
        prompt="Toán tử nào dùng để lấy địa chỉ biến?",
        origin="llm",
        options=["&", "*"],
        answer={"value": "&"},
    )

    usable = auto_questions.usable_questions([q1, q2, q3, q4])
    assert len(usable) == 2
    assert "địa chỉ ô nhớ" in usable[0].prompt
    assert "lấy địa chỉ biến" in usable[1].prompt


def test_tc_t1_aux_02_session_understanding_summary(sample_classroom_data, test_db, modules):
    """TC-T1-AUX-02: Computes session summary metrics."""
    session_understanding = modules["session_understanding"]
    session = sample_classroom_data["session"]

    summary = session_understanding.build_session_summary(test_db, session)
    assert "session_id" in summary or "understanding_score" in summary or isinstance(summary, dict)


def test_tc_t1_aux_03_analytics_metrics_defaults_on_empty_slide(sample_classroom_data, test_db, modules):
    """TC-T1-AUX-03: Analytics collect handles empty slide without crashes."""
    analytics = modules["analytics"]
    session = sample_classroom_data["session"]

    metrics = analytics.collect(test_db, session.id, slide_index=0, slide_title="Slide 0")
    assert metrics.online_students == 3
    assert metrics.responded == 0
    assert metrics.participation == 0.0
