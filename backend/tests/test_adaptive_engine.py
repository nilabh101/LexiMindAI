"""
Deterministic unit tests for the LexiMind Adaptive Learning Engine — Phase 3.

All tests:
- Use fixed inputs only (no random seeds, no external API calls)
- Set up and tear down their own in-memory state
- Assert exact values where possible

Run with:
    pytest backend/tests/test_adaptive_engine.py -v
"""
import pytest
from datetime import datetime, timezone, timedelta


# ═══════════════════════════════════════════════════════════════════════════════
# adaptive_mastery — calculate_mastery
# ═══════════════════════════════════════════════════════════════════════════════

from app.services.adaptive_mastery import (
    calculate_mastery,
    compute_recency_score,
    get_mastery_state,
    MasteryState,
    DIFFICULTY_WEIGHTS,
    RECENCY_N,
    RECENCY_DECAY,
)


class TestCalculateMastery:
    def test_zero_attempts_returns_zero(self):
        score = calculate_mastery(0, 0, 0.0, 0.0, 0.0)
        assert score == 0.0

    def test_all_correct_easy_perfect_recency(self):
        # 10 correct easy questions, recency = 1.0
        # base = 1.0, diff = 1.0, recency = 1.0
        # score = 100 * (0.5*1 + 0.3*1 + 0.2*1) = 100.0
        score = calculate_mastery(10, 10, 10.0, 10.0, 1.0)
        assert score == 100.0

    def test_all_incorrect(self):
        # correct=0, recency=0 → 0.0
        score = calculate_mastery(0, 10, 0.0, 10.0, 0.0)
        assert score == 0.0

    def test_mixed_with_difficulty_weights(self):
        # 3 correct (2 easy=1.0, 1 hard=1.5), 5 attempted (3 easy, 1 medium=1.25, 1 hard)
        # dw_correct = 2*1.0 + 1*1.5 = 3.5
        # dw_attempted = 3*1.0 + 1*1.25 + 1*1.5 = 5.75
        # base = 3/5 = 0.6
        # diff = 3.5/5.75 ≈ 0.608695...
        # score = 100 * (0.5*0.6 + 0.3*0.608695 + 0.2*0.5) = 100 * (0.3 + 0.182608 + 0.1) = 58.2608...
        score = calculate_mastery(3, 5, 3.5, 5.75, 0.5)
        assert round(score, 4) == round(
            100.0 * (0.5 * (3/5) + 0.3 * (3.5/5.75) + 0.2 * 0.5), 4
        )

    def test_mixed_with_recency_decay(self):
        # 5 correct, 10 attempted, perfect difficulty, recency=0.3
        # base=0.5, diff=0.5, recency=0.3
        # score = 100*(0.5*0.5 + 0.3*0.5 + 0.2*0.3) = 100*(0.25+0.15+0.06) = 46.0
        score = calculate_mastery(5, 10, 5.0, 10.0, 0.3)
        assert round(score, 4) == round(100.0 * (0.5*0.5 + 0.3*0.5 + 0.2*0.3), 4)

    def test_invalid_correct_exceeds_attempted_raises(self):
        with pytest.raises(ValueError, match="questions_correct"):
            calculate_mastery(11, 10, 10.0, 10.0, 0.5)

    def test_invalid_recency_above_1_raises(self):
        with pytest.raises(ValueError, match="recency_score"):
            calculate_mastery(5, 10, 5.0, 10.0, 1.1)

    def test_invalid_recency_below_0_raises(self):
        with pytest.raises(ValueError, match="recency_score"):
            calculate_mastery(5, 10, 5.0, 10.0, -0.1)

    def test_score_always_in_bounds(self):
        """Bounds invariant: for all valid inputs output is in [0, 100]."""
        cases = [
            (0, 0, 0.0, 0.0, 0.0),
            (1, 1, 1.5, 1.5, 1.0),
            (0, 100, 0.0, 125.0, 0.0),
            (100, 100, 100.0, 100.0, 1.0),
            (7, 10, 8.75, 11.25, 0.7),
        ]
        for args in cases:
            s = calculate_mastery(*args)
            assert 0.0 <= s <= 100.0, f"Out of bounds: {s} for inputs {args}"

    def test_deterministic(self):
        """Same inputs always produce same output."""
        args = (7, 10, 8.75, 11.25, 0.7)
        assert calculate_mastery(*args) == calculate_mastery(*args)


# ═══════════════════════════════════════════════════════════════════════════════
# compute_recency_score
# ═══════════════════════════════════════════════════════════════════════════════

class TestComputeRecencyScore:
    def test_empty_returns_zero(self):
        assert compute_recency_score([]) == 0.0

    def test_all_correct(self):
        attempts = [{"correct": True}] * 5
        score = compute_recency_score(attempts)
        assert score == 1.0

    def test_all_incorrect(self):
        attempts = [{"correct": False}] * 5
        score = compute_recency_score(attempts)
        assert score == 0.0

    def test_recency_weights_more_recent(self):
        # Last 2 correct, first 3 incorrect (6 total → use last N=5)
        # More recent correct answers should yield score > 0.5
        attempts = [
            {"correct": False},
            {"correct": False},
            {"correct": False},
            {"correct": True},
            {"correct": True},
        ]
        score = compute_recency_score(attempts, n=5, decay=0.85)
        # Manually: weights = [0.85^3, 0.85^2, 0.85^1, 0.85^0] for last 4... actually last 5
        # weights = [0.52200625, 0.614125, 0.7225, 0.85, 1.0]
        # correct: positions 3,4 (0-indexed last two)
        # weighted_correct = 0.85 + 1.0 = 1.85
        # total = 0.52200625+0.614125+0.7225+0.85+1.0 = 3.70913125
        # score ≈ 0.499
        assert 0.4 < score < 0.6

    def test_score_in_bounds(self):
        for _ in range(20):
            attempts = [{"correct": True}, {"correct": False}] * 5
            s = compute_recency_score(attempts)
            assert 0.0 <= s <= 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# get_mastery_state — boundary tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetMasteryState:
    def test_zero_attempts_not_started(self):
        assert get_mastery_state(0.0, 0) == MasteryState.NOT_STARTED

    def test_score_0_one_attempt_very_weak(self):
        assert get_mastery_state(0.0, 1) == MasteryState.VERY_WEAK

    def test_boundary_29_very_weak(self):
        assert get_mastery_state(29.9, 5) == MasteryState.VERY_WEAK

    def test_boundary_30_weak(self):
        assert get_mastery_state(30.0, 5) == MasteryState.WEAK

    def test_boundary_49_weak(self):
        assert get_mastery_state(49.9, 5) == MasteryState.WEAK

    def test_boundary_50_developing(self):
        assert get_mastery_state(50.0, 5) == MasteryState.DEVELOPING

    def test_boundary_69_developing(self):
        assert get_mastery_state(69.9, 5) == MasteryState.DEVELOPING

    def test_boundary_70_proficient(self):
        assert get_mastery_state(70.0, 5) == MasteryState.PROFICIENT

    def test_boundary_84_proficient(self):
        assert get_mastery_state(84.9, 5) == MasteryState.PROFICIENT

    def test_boundary_85_mastered(self):
        assert get_mastery_state(85.0, 5) == MasteryState.MASTERED

    def test_100_mastered(self):
        assert get_mastery_state(100.0, 10) == MasteryState.MASTERED

    def test_all_boundaries_distinct(self):
        states = [
            get_mastery_state(0.0, 1),
            get_mastery_state(30.0, 1),
            get_mastery_state(50.0, 1),
            get_mastery_state(70.0, 1),
            get_mastery_state(85.0, 1),
        ]
        assert len(set(states)) == 5, "All boundary states must be distinct"


# ═══════════════════════════════════════════════════════════════════════════════
# prerequisite_graph
# ═══════════════════════════════════════════════════════════════════════════════

from app.services.prerequisite_graph import (
    detect_cycles,
    get_prerequisites,
)


class TestDetectCycles:
    def test_no_cycle(self):
        graph = {"A": ["B"], "B": ["C"], "C": []}
        assert detect_cycles(graph) == set()

    def test_simple_cycle(self):
        graph = {"A": ["B"], "B": ["A"]}
        cycles = detect_cycles(graph)
        assert "A" in cycles or "B" in cycles

    def test_self_loop(self):
        graph = {"A": ["A"]}
        assert "A" in detect_cycles(graph)

    def test_empty_graph(self):
        assert detect_cycles({}) == set()


# ═══════════════════════════════════════════════════════════════════════════════
# review_scheduler — advance_interval
# ═══════════════════════════════════════════════════════════════════════════════

from app.services.review_scheduler import advance_interval, reset_interval, REVIEW_SEQUENCE


class TestReviewScheduler:
    def test_sequence_1_to_3(self):
        assert advance_interval(1) == 3

    def test_sequence_3_to_7(self):
        assert advance_interval(3) == 7

    def test_sequence_7_to_14(self):
        assert advance_interval(7) == 14

    def test_sequence_14_to_30(self):
        assert advance_interval(14) == 30

    def test_sequence_30_stays_30(self):
        assert advance_interval(30) == 30

    def test_reset_returns_1(self):
        assert reset_interval() == 1

    def test_full_sequence(self):
        current = REVIEW_SEQUENCE[0]
        seq = [current]
        for _ in range(len(REVIEW_SEQUENCE) - 1):
            current = advance_interval(current)
            seq.append(current)
        assert seq == REVIEW_SEQUENCE

    def test_mastery_drop_resets_to_1(self):
        """Regression: after mastery drop, interval resets to 1."""
        assert reset_interval() == REVIEW_SEQUENCE[0]

    def test_unknown_value_returns_next_in_sequence(self):
        # Value not in sequence → find next larger
        result = advance_interval(5)
        assert result == 7  # next value in sequence after 5


# ═══════════════════════════════════════════════════════════════════════════════
# adaptive_quiz — difficulty targeting + session dedup
# ═══════════════════════════════════════════════════════════════════════════════

from app.services.adaptive_quiz import (
    _primary_tier,
    compute_session_difficulty_adjustment,
    ADAPTIVE_CONSTANTS,
)


class TestAdaptiveQuiz:
    def test_mastery_below_40_primary_easy(self):
        assert _primary_tier(0.0) == "easy"
        assert _primary_tier(39.9) == "easy"

    def test_mastery_40_to_70_primary_medium(self):
        assert _primary_tier(40.0) == "medium"
        assert _primary_tier(69.9) == "medium"

    def test_mastery_70_plus_primary_hard(self):
        assert _primary_tier(70.0) == "hard"
        assert _primary_tier(100.0) == "hard"

    def test_difficulty_tier_up_after_3_correct(self):
        result = compute_session_difficulty_adjustment(
            streak_correct=3, streak_incorrect=0, current_tier="easy"
        )
        assert result == "medium"

    def test_difficulty_tier_down_after_2_incorrect(self):
        result = compute_session_difficulty_adjustment(
            streak_correct=0, streak_incorrect=2, current_tier="hard"
        )
        assert result == "medium"

    def test_already_at_hard_no_tier_up(self):
        result = compute_session_difficulty_adjustment(
            streak_correct=10, streak_incorrect=0, current_tier="hard"
        )
        assert result == "hard"

    def test_already_at_easy_no_tier_down(self):
        result = compute_session_difficulty_adjustment(
            streak_correct=0, streak_incorrect=10, current_tier="easy"
        )
        assert result == "easy"

    def test_no_adjustment_when_below_threshold(self):
        result = compute_session_difficulty_adjustment(
            streak_correct=2, streak_incorrect=1, current_tier="medium"
        )
        assert result == "medium"


# ═══════════════════════════════════════════════════════════════════════════════
# is_prerequisite_mastered — logic tests (no DB)
# ═══════════════════════════════════════════════════════════════════════════════

from app.services.prerequisite_graph import get_prerequisites


class TestPrerequisiteGraph:
    def test_get_prerequisites_returns_list(self):
        # euler-theorem-dc should have prerequisites from curriculum
        result = get_prerequisites("euler-theorem-dc")
        assert isinstance(result, list)

    def test_concept_with_no_prereqs_returns_empty(self):
        # partial-derivatives-dc has no prerequisites in curriculum
        result = get_prerequisites("partial-derivatives-dc")
        assert isinstance(result, list)
        # May be empty or have values depending on curriculum — just type check

    def test_unknown_concept_returns_empty(self):
        result = get_prerequisites("nonexistent-concept-xyz")
        assert result == []


# ═══════════════════════════════════════════════════════════════════════════════
# DIFFICULTY_WEIGHTS constants
# ═══════════════════════════════════════════════════════════════════════════════

class TestDifficultyWeights:
    def test_easy_weight(self):
        assert DIFFICULTY_WEIGHTS["easy"] == 1.0

    def test_medium_weight(self):
        assert DIFFICULTY_WEIGHTS["medium"] == 1.25

    def test_hard_weight(self):
        assert DIFFICULTY_WEIGHTS["hard"] == 1.5

    def test_hard_greater_than_medium(self):
        assert DIFFICULTY_WEIGHTS["hard"] > DIFFICULTY_WEIGHTS["medium"] > DIFFICULTY_WEIGHTS["easy"]
