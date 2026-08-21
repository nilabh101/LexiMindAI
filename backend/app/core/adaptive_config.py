"""Single source of truth for every tunable value of the adaptive engine.

Everything here is deterministic and transparent: the LexiMind Mastery Score is
a weighted-accuracy heuristic, not a validated psychometric measurement.
"""
from typing import Dict, List

# ── Difficulty weighting ──────────────────────────────────────────────────────
# A correct HARD question is stronger evidence of mastery than an EASY one.
DIFFICULTY_WEIGHTS: Dict[str, float] = {
    "EASY": 1.0,
    "MEDIUM": 1.25,
    "HARD": 1.5,
}
DEFAULT_DIFFICULTY = "MEDIUM"

# ── Recency ───────────────────────────────────────────────────────────────────
# Every attempt carries an exponential decay weight: 0.5 ** (age_days / HALF_LIFE).
# Attempts never disappear, they just count less than fresh ones.
RECENCY_HALF_LIFE_DAYS = 30.0
RECENCY_MIN_WEIGHT = 0.15

# Number of most recent attempts used for the "recent performance" component.
RECENT_WINDOW = 5
# Blend between long-run weighted accuracy and the recent window.
RECENT_PERFORMANCE_WEIGHT = 0.35

# Shrinkage: with very little evidence the score is pulled toward the neutral
# prior so a single lucky answer cannot produce "MASTERED".
EVIDENCE_FULL_WEIGHT_ATTEMPTS = 8.0
NEUTRAL_PRIOR = 0.5

# ── Concept states ────────────────────────────────────────────────────────────
STATE_VERY_WEAK = "VERY_WEAK"
STATE_WEAK = "WEAK"
STATE_DEVELOPING = "DEVELOPING"
STATE_PROFICIENT = "PROFICIENT"
STATE_MASTERED = "MASTERED"
STATE_NOT_STARTED = "NOT_STARTED"

# (inclusive lower bound, state) — ordered high → low.
STATE_THRESHOLDS: List[tuple] = [
    (85.0, STATE_MASTERED),
    (70.0, STATE_PROFICIENT),
    (50.0, STATE_DEVELOPING),
    (30.0, STATE_WEAK),
    (0.0, STATE_VERY_WEAK),
]

WEAK_STATES = {STATE_VERY_WEAK, STATE_WEAK}
# A concept is treated as "not mastered enough to unlock dependents" below this.
PREREQUISITE_MASTERY_THRESHOLD = 70.0
# Concepts at or below this score are surfaced as weak areas.
WEAK_CONCEPT_THRESHOLD = 50.0

# ── Adaptive difficulty ───────────────────────────────────────────────────────
# mastery band → difficulty mix used when building a quiz.
DIFFICULTY_BANDS: List[tuple] = [
    # (exclusive upper bound of mastery, ordered preference of difficulties)
    (40.0, ["EASY", "MEDIUM"]),
    (70.0, ["MEDIUM", "EASY"]),
    (101.0, ["MEDIUM", "HARD"]),
]
CONSECUTIVE_CORRECT_TO_INCREASE = 3
CONSECUTIVE_INCORRECT_TO_DECREASE = 2
DIFFICULTY_LADDER = ["EASY", "MEDIUM", "HARD"]

# ── Question repetition ───────────────────────────────────────────────────────
# Questions answered within this window are avoided unless review is requested
# or nothing else is available.
REPEAT_COOLDOWN_DAYS = 7

# ── Spaced review ─────────────────────────────────────────────────────────────
REVIEW_INTERVALS_DAYS = [1, 3, 7, 14, 30]
# Accuracy (0-1) in the latest session at/above which the interval grows.
REVIEW_PROMOTE_ACCURACY = 0.8
# ... and below which it resets to the first interval.
REVIEW_DEMOTE_ACCURACY = 0.5

# ── Recommendations / study plan ──────────────────────────────────────────────
DEFAULT_DAILY_STUDY_MINUTES = 30
MIN_PLAN_BLOCK_MINUTES = 10
# Estimated minutes per recommendation type when the curriculum has no estimate.
DEFAULT_STUDY_MINUTES = {
    "LEARN": 30,
    "REVIEW": 15,
    "PRACTICE": 15,
    "PYQ": 20,
    "QUIZ": 10,
}

RECOMMENDATION_TYPES = ["LEARN", "REVIEW", "PRACTICE", "PYQ", "QUIZ"]

# Learning path item states.
PATH_COMPLETED = "COMPLETED"
PATH_CURRENT = "CURRENT"
PATH_RECOMMENDED = "RECOMMENDED"
PATH_LOCKED = "LOCKED"
PATH_NEEDS_REVIEW = "NEEDS_REVIEW"

# Phase 2 relationship confidence below which a prerequisite edge is advisory
# only (shown as context, never used to lock content).
MIN_PREREQUISITE_CONFIDENCE = 0.5


def difficulty_weight(difficulty: str | None) -> float:
    """Evidence weight of a question at the given difficulty."""
    key = (difficulty or DEFAULT_DIFFICULTY).upper()
    return DIFFICULTY_WEIGHTS.get(key, DIFFICULTY_WEIGHTS[DEFAULT_DIFFICULTY])


def concept_state(mastery_score: float | None, attempted: int = 1) -> str:
    """Map a 0–100 LexiMind Mastery Score to a concept state."""
    if not attempted:
        return STATE_NOT_STARTED
    score = float(mastery_score or 0.0)
    for lower, state in STATE_THRESHOLDS:
        if score >= lower:
            return state
    return STATE_VERY_WEAK


def target_difficulties(mastery_score: float | None) -> List[str]:
    """Preferred difficulty order for a learner at this mastery level."""
    score = float(mastery_score or 0.0)
    for upper, difficulties in DIFFICULTY_BANDS:
        if score < upper:
            return list(difficulties)
    return list(DIFFICULTY_BANDS[-1][1])
