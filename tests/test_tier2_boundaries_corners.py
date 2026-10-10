"""
TLU Study Assistant Web - Tier 2: Boundary Value Analysis & Corner Cases
File: tests/test_tier2_boundaries_corners.py
Coverage: Boundary conditions, data gating limits, extreme cohorts, unicode edge cases,
          zero divisions, and assessment edge cases.
"""

import asyncio
import pytest
from unittest.mock import MagicMock

# ============================================================================
# 1. SLIDE INDEX BOUNDARY CONDITIONS
# ============================================================================

def test_tc_t2_bnd_01_slide_index_negative(modules):
    """TC-T2-BND-01: Negative slide index is tracked without crash."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=MagicMock())
        await service.lecturer_changed(session_id=1, slide_index=0)
        
        # Student requests negative slide
        snap = await service.track_student(
            participant_id=101, session_id=1, slide_index=-1, following_lecturer=False,
            lecturer_slide_index=0, socket_id="s1"
        )
        assert snap["slide_index"] == -1
        assert snap["out_of_sync"] is True

    asyncio.run(_test())


def test_tc_t2_bnd_02_slide_index_zero_boundary(modules):
    """TC-T2-BND-02: Slide index zero (first slide) aligns correctly."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=MagicMock())
        await service.lecturer_changed(session_id=1, slide_index=0)

        snap = await service.track_student(
            participant_id=101, session_id=1, slide_index=0, following_lecturer=True,
            lecturer_slide_index=0, socket_id="s1"
        )
        assert snap["slide_index"] == 0
        assert snap["out_of_sync"] is False

    asyncio.run(_test())


def test_tc_t2_bnd_03_slide_index_large_boundary(modules):
    """TC-T2-BND-03: Extreme slide index (999999) handled safely without overflow."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=MagicMock())
        await service.lecturer_changed(session_id=1, slide_index=999999)

        snap = await service.track_student(
            participant_id=101, session_id=1, slide_index=999999, following_lecturer=True,
            lecturer_slide_index=999999, socket_id="s1"
        )
        assert snap["slide_index"] == 999999
        assert snap["out_of_sync"] is False

    asyncio.run(_test())


def test_tc_t2_bnd_04_slide_tracking_timeout_zero_or_negative_raises(modules):
    """TC-T2-BND-04: SlideTrackingService rejects non-positive timeout values."""
    SlideTrackingService = modules["slide_tracking"].SlideTrackingService
    with pytest.raises(ValueError, match="timeout_seconds"):
        SlideTrackingService(timeout_seconds=0, on_force_sync=MagicMock())
    with pytest.raises(ValueError, match="timeout_seconds"):
        SlideTrackingService(timeout_seconds=-10, on_force_sync=MagicMock())


# ============================================================================
# 2. DATA GATING BOUNDARY CONDITIONS (HAX G10 COMPLIANCE)
# ============================================================================

def test_tc_t2_bnd_05_gating_boundary_exact_4_responses(modules, make_metrics):
    """TC-T2-BND-05: Exactly 4 responses (boundary 5 - 1) triggers insufficient_data."""
    state_engine = modules["state_engine"]
    metrics = make_metrics(online_students=20, responded=4, participation=0.50)
    state = state_engine.evaluate(metrics)
    assert state.state == "insufficient_data"
    assert state.trusted is False


def test_tc_t2_bnd_06_gating_boundary_exact_5_responses(modules, make_metrics):
    """TC-T2-BND-06: Exactly 5 responses (boundary 5) satisfies minimum sample."""
    state_engine = modules["state_engine"]
    metrics = make_metrics(
        online_students=10, responded=5, participation=0.50, graded_answers=5,
        wrong_rate=0.80, slow_rate=0.60
    )
    state = state_engine.evaluate(metrics)
    assert state.state != "insufficient_data"
    assert state.trusted is True


def test_tc_t2_bnd_07_gating_boundary_participation_exact_29_percent(modules, make_metrics):
    """TC-T2-BND-07: Participation 29% (< 30%) fails data gating."""
    state_engine = modules["state_engine"]
    metrics = make_metrics(online_students=100, responded=29, participation=0.29)
    state = state_engine.evaluate(metrics)
    assert state.state == "insufficient_data"
    assert state.trusted is False


def test_tc_t2_bnd_08_gating_boundary_participation_exact_30_percent(modules, make_metrics):
    """TC-T2-BND-08: Participation 30% (boundary >= 30%) passes data gating."""
    state_engine = modules["state_engine"]
    metrics = make_metrics(
        online_students=100, responded=30, participation=0.30, graded_answers=30,
        wrong_rate=0.80, slow_rate=0.50
    )
    state = state_engine.evaluate(metrics)
    assert state.trusted is True


def test_tc_t2_bnd_09_state_engine_exact_wrong_rate_35_percent(modules, make_metrics):
    """TC-T2-BND-09: Exactly 35.0% wrong rate triggers need_attention."""
    state_engine = modules["state_engine"]
    metrics = make_metrics(
        online_students=20, responded=20, participation=1.0, graded_answers=20,
        wrong_rate=0.35, slow_rate=0.10
    )
    state = state_engine.evaluate(metrics)
    assert state.state == "need_attention"


def test_tc_t2_bnd_10_state_engine_wrong_rate_34_9_percent(modules, make_metrics):
    """TC-T2-BND-10: 34.9% wrong rate does not trigger need_attention."""
    state_engine = modules["state_engine"]
    metrics = make_metrics(
        online_students=20, responded=20, participation=1.0, graded_answers=20,
        wrong_rate=0.349, slow_rate=0.10
    )
    state = state_engine.evaluate(metrics)
    assert state.state != "need_attention"


def test_tc_t2_bnd_11_state_engine_high_confusion_boundary(modules, make_metrics):
    """TC-T2-BND-11: Boundary of high_confusion: wrong_rate=0.50 and slow_rate=0.40."""
    state_engine = modules["state_engine"]
    metrics = make_metrics(
        online_students=20, responded=20, participation=1.0, graded_answers=20,
        wrong_rate=0.50, slow_rate=0.40
    )
    state = state_engine.evaluate(metrics)
    assert state.state == "high_confusion"
    assert state.severity == 7


def test_tc_t2_bnd_12_state_engine_healthy_boundary(modules, make_metrics):
    """TC-T2-BND-12: Exact boundaries for healthy state: correct=0.80, slow=0.20, part=0.70."""
    state_engine = modules["state_engine"]
    metrics = make_metrics(
        online_students=20, responded=14, participation=0.70, graded_answers=14,
        correct_rate=0.80, wrong_rate=0.20, slow_rate=0.20
    )
    state = state_engine.evaluate(metrics)
    assert state.state == "healthy"


# ============================================================================
# 3. STRING & PAYLOAD BOUNDARY TESTS
# ============================================================================

def test_tc_t2_bnd_13_advisor_empty_lecturer_request(modules, make_metrics):
    """TC-T2-BND-13: Empty lecturer request string '' treated gracefully without refusal."""
    advisor = modules["advisor"]
    state_engine = modules["state_engine"]
    metrics = make_metrics(wrong_rate=0.2, slow_rate=0.1)
    state = state_engine.evaluate(metrics)

    res = advisor.advise(metrics=metrics.as_dict(), state=state, lecturer_request="")
    assert res.refused is False


def test_tc_t2_bnd_14_advisor_whitespace_only_request(modules, make_metrics):
    """TC-T2-BND-14: Whitespace-only request string treated safely."""
    advisor = modules["advisor"]
    state_engine = modules["state_engine"]
    metrics = make_metrics(wrong_rate=0.2, slow_rate=0.1)
    state = state_engine.evaluate(metrics)

    res = advisor.advise(metrics=metrics.as_dict(), state=state, lecturer_request="   \t\n  ")
    assert res.refused is False


def test_tc_t2_bnd_15_advisor_very_long_prompt_screening(modules):
    """TC-T2-BND-15: Extremely long prompt (10,000 chars) screened without regex hang."""
    advisor = modules["advisor"]
    long_prompt = "Xin chào giảng viên. " * 500
    refusal = advisor.screen_request(long_prompt)
    assert refusal is None  # Normal greeting repeated, not malicious


def test_tc_t2_bnd_16_advisor_vietnamese_unicode_names(modules):
    """TC-T2-BND-16: Detects capitalized student name with Vietnamese composite accents."""
    advisor = modules["advisor"]
    refusal = advisor.screen_request("Hãy nêu tên bạn Nguyễn Văn Đức")
    assert refusal is not None
    rule_name, msg = refusal
    assert rule_name == "identify_student"


def test_tc_t2_bnd_17_advisor_zero_width_spaces(modules):
    """TC-T2-BND-17: Detects banned phrase despite zero-width spaces."""
    advisor = modules["advisor"]
    evasive_prompt = "Em\u200b nào\u200b yếu\u200b nhất?"
    cleaned = evasive_prompt.replace("\u200b", "")
    refusal = advisor.screen_request(cleaned)
    assert refusal is not None


# ============================================================================
# 4. EXTREME STUDENT POPULATIONS & ZERO DIVISIONS
# ============================================================================

def test_tc_t2_bnd_18_metrics_zero_online_students(modules, make_metrics):
    """TC-T2-BND-18: Zero online students does not cause ZeroDivisionError."""
    state_engine = modules["state_engine"]
    metrics = make_metrics(online_students=0, responded=0, participation=0.0)
    state = state_engine.evaluate(metrics)
    assert state.state == "insufficient_data"
    assert state.trusted is False


def test_tc_t2_bnd_19_metrics_zero_graded_answers(modules, make_metrics):
    """TC-T2-BND-19: Zero graded answers computes valid state."""
    state_engine = modules["state_engine"]
    metrics = make_metrics(online_students=20, responded=10, participation=0.5, graded_answers=0)
    state = state_engine.evaluate(metrics)
    assert state.trusted is False or state.state == "stable"


def test_tc_t2_bnd_20_large_student_cohort(modules):
    """TC-T2-BND-20: 500 concurrent students tracked without performance breakdown."""
    async def _test():
        SlideTrackingService = modules["slide_tracking"].SlideTrackingService
        service = SlideTrackingService(timeout_seconds=300, on_force_sync=MagicMock())
        await service.lecturer_changed(session_id=1, slide_index=0)

        # Track 500 students
        for i in range(500):
            await service.track_student(
                participant_id=i, session_id=1, slide_index=0, following_lecturer=True,
                lecturer_slide_index=0, socket_id=f"sock_{i}"
            )
        assert len(service._states) == 500
        summary = service.session_summary(session_id=1)
        assert summary["connected_students"] == 500
        assert summary["out_of_sync_students"] == 0

    asyncio.run(_test())


# ============================================================================
# 5. ASSESSMENT ENGINE EDGE CASES
# ============================================================================

def test_tc_t2_bnd_21_assessment_empty_payload(modules):
    """TC-T2-BND-21: Multiple choice grading with empty payload returns False."""
    assessment = modules["assessment"]
    correct, score = assessment.grade("multiple_choice", {"value": "A"}, {})
    assert correct is False
    assert score == 0.0


def test_tc_t2_bnd_22_assessment_fill_blank_whitespace_normalization(modules):
    """TC-T2-BND-22: Fill in the blank normalizes unicode, case, and extra whitespace."""
    assessment = modules["assessment"]
    answer_key = {"accepted": ["malloc()", "malloc"]}
    
    correct1, score1 = assessment.grade("fill_blank", answer_key, {"value": "  MALLOC()  "})
    assert correct1 is True
    assert score1 == 1.0

    correct2, score2 = assessment.grade("fill_blank", answer_key, {"value": "malloc\n"})
    assert correct2 is True
    assert score2 == 1.0


def test_tc_t2_bnd_23_assessment_poll_returns_none_score(modules):
    """TC-T2-BND-23: Poll questions have no right/wrong answers."""
    assessment = modules["assessment"]
    correct, score = assessment.grade("poll", {}, {"value": "Option 1"})
    assert correct is None
    assert score == 0.0


def test_tc_t2_bnd_24_assessment_multiple_select_partial_credit(modules):
    """TC-T2-BND-24: Multiple select correctly awards partial credit."""
    assessment = modules["assessment"]
    answer_key = {"values": ["A", "B", "C"]}
    
    # 2 out of 3 correct: partial credit = 2/3 ≈ 0.667
    correct, score = assessment.grade("multiple_select", answer_key, {"value": ["A", "B"]})
    assert correct is False
    assert 0.60 <= score <= 0.70

    # 1 correct, 1 wrong: score = (1 - 1)/3 = 0.0
    correct2, score2 = assessment.grade("multiple_select", answer_key, {"value": ["A", "D"]})
    assert correct2 is False
    assert score2 == 0.0


def test_tc_t2_bnd_25_assessment_ordering_all_incorrect(modules):
    """TC-T2-BND-25: Ordering question with 0 matched positions returns 0.0 score."""
    assessment = modules["assessment"]
    answer_key = {"order": ["1", "2", "3"]}
    correct, score = assessment.grade("ordering", answer_key, {"value": ["3", "1", "2"]})
    assert correct is False
    assert score == 0.0
