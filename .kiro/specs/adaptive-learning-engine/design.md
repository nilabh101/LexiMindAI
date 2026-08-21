# Design Document: Adaptive Learning Engine (Phase 3)

## Overview

Phase 3 adds an Adaptive Learning Intelligence layer to LexiMind AI. It is built entirely on top of the existing Phase 1 UI (React/TypeScript/Vite) and Phase 2 academic pipeline (FastAPI, SQLite via SQLAlchemy async). No Phase 1 or Phase 2 component is replaced — every change is an extension.

The adaptive loop is:

```
Student answers question
    → QuestionAttempt recorded
    → ConceptMastery updated via calculate_mastery()
    → Mastery state re-evaluated
    → Weak concepts detected
    → Prerequisites checked
    → Next recommendation generated
    → Adaptive quiz assembled
    → New attempts recorded
    → Loop repeats
```

### File Map: EXTENDED vs NEW

| Path | Action |
|---|---|
| `backend/app/models/academic.py` | **EXTENDED** — new columns on ConceptMastery, new QuestionAttempt + ReviewSchedule tables |
| `backend/app/services/mastery.py` | **EXTENDED** — existing compute_mastery() kept; new calculate_mastery() added alongside it |
| `backend/app/services/demo_seed.py` | **EXTENDED** — Phase 3 seed data appended |
| `backend/app/api/learning.py` | **EXTENDED** — new routes added to existing router |
| `backend/app/api/quizzes.py` | **EXTENDED** — POST /api/quizzes/adaptive added |
| `backend/app/api/chat.py` | **EXTENDED** — student_context added to ChatRequest |
| `backend/app/core/database.py` | **EXTENDED** — migration list for new columns |
| `frontend/src/pages/Dashboard.tsx` | **EXTENDED** — live API calls replace placeholder data |
| `frontend/src/lib/api.ts` | **EXTENDED** — new API helper functions |
| `backend/app/services/adaptive_mastery.py` | **NEW** |
| `backend/app/services/prerequisite_graph.py` | **NEW** |
| `backend/app/services/recommendation_engine.py` | **NEW** |
| `backend/app/services/adaptive_quiz.py` | **NEW** |
| `backend/app/services/review_scheduler.py` | **NEW** |
| `backend/app/services/study_plan.py` | **NEW** |
| `frontend/src/pages/ProgressPage.tsx` | **NEW** |
| `backend/tests/test_adaptive_engine.py` | **NEW** |

---

## Architecture

### Layer Diagram

```
┌───────────────────────────────────────────────────────────────┐
│                        React Frontend                         │
│  Dashboard.tsx  ProgressPage.tsx  QuizPage.tsx  Chat UI       │
└───────────────┬────────────┬────────────┬───────┬────────────┘
                │ REST/JSON  │            │       │
┌───────────────▼────────────▼────────────▼───────▼────────────┐
│                        FastAPI (main.py)                      │
│  /api/learning/*   /api/quizzes/*   /api/chat   /api/...      │
└──────┬──────────────┬──────────────┬──────────────┬──────────┘
       │              │              │              │
┌──────▼──────┐ ┌─────▼──────┐ ┌───▼────────┐ ┌──▼──────────┐
│  adaptive_  │ │  adaptive_ │ │recommend-  │ │ review_     │
│  mastery.py │ │  quiz.py   │ │ ation_     │ │ scheduler.py│
│             │ │            │ │ engine.py  │ │             │
└──────┬──────┘ └─────┬──────┘ └───┬────────┘ └──┬──────────┘
       │              │              │              │
┌──────▼──────────────▼──────────────▼──────────────▼──────────┐
│                     Phase 2 Services (UNCHANGED)              │
│  mastery.py  quiz_bank.py  llm.py  search.py  pipeline.py    │
└──────────────────────────────┬────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────┐
│                   SQLite (SQLAlchemy async)                    │
│  ConceptMastery  QuestionAttempt  ReviewSchedule  + Phase 2   │
└───────────────────────────────────────────────────────────────┘
```

### Adaptive Loop Data Flow

```
POST /api/quizzes/adaptive
        │
        ▼
adaptive_quiz.py::assemble_adaptive_quiz()
    ├── get_weak_concepts(db, user_id)         ← adaptive_mastery.py
    ├── is_prerequisite_mastered(db, user_id)  ← prerequisite_graph.py
    └── quiz_bank.py::generate_quiz()          ← Phase 2 (unchanged)
        │
        ▼ (returns quiz to frontend)
        │
POST /api/learning/quiz-attempt
        │
        ▼
learning.py::submit_quiz_attempt()
    ├── for each answer → adaptive_mastery.py::update_concept_mastery()
    │       └── calculate_mastery() → mastery_score + state
    ├── review_scheduler.py::schedule_review()  (if PROFICIENT+)
    └── recommendation_engine.py::get_next_recommendation()
        │
        ▼ (returns results + next recommendation to frontend)
```

---

## Components and Interfaces

### Phase 2 Audit Approach

Before any Phase 3 code is written, the following checklist must be verified:

| # | Check | How to Verify | Common Fix |
|---|---|---|---|
| 1 | Backend starts cleanly | `uvicorn app.main:app --reload` — no ImportError or exception at startup | Fix missing `__init__.py`, circular imports, missing env vars |
| 2 | Frontend builds | `npm run build` — exit code 0, no console errors | Fix TypeScript type errors, missing imports |
| 3 | PDF pipeline end-to-end | Upload a PDF ≤ 5 MB, poll `/api/documents/{id}` until `status=READY` within 60 s | Check OCR threshold setting, file permissions |
| 4 | PYQ source labels | Upload a PYQ PDF; query `/api/academic/questions?source=PYQ` — all items have `source=PYQ` | Fix classifier in pipeline.py |
| 5 | Quiz system | POST `/api/quizzes/generate` → receive questions; POST `/api/quizzes/complete` → HTTP 200 with non-null score | Seed DEMO data if question bank is empty |
| 6 | AI Tutor status | GET `/api/chat` or POST with empty key → HTTP 2xx with non-empty fallback text | Ensure fallback path in chat.py covers missing key |
| 7 | Security | `git ls-files | xargs grep -l "API_KEY"` — no key values; `.env` in `.gitignore` | Remove any committed secrets, rotate keys |

The Phase 2 Baseline Report must record: pass/fail per item, git commit hash, and a `PHASE 2 VERIFIED: PASS` declaration. Phase 3 implementation is gated on all items passing.

---

### New Service: `backend/app/services/adaptive_mastery.py`

This is the canonical home for all mastery computation logic. It must never be duplicated in route handlers.

#### Configuration Constants

```python
from enum import Enum
from dataclasses import dataclass

DIFFICULTY_WEIGHTS = {
    "easy": 1.0,
    "medium": 1.25,
    "hard": 1.5,
}

STATE_THRESHOLDS = {
    "NOT_STARTED":  (0.0, 0.0),     # questions_attempted == 0
    "VERY_WEAK":    (0.0, 30.0),    # mastery_score < 30
    "WEAK":         (30.0, 50.0),   # 30 ≤ score < 50
    "DEVELOPING":   (50.0, 70.0),   # 50 ≤ score < 70
    "PROFICIENT":   (70.0, 85.0),   # 70 ≤ score < 85
    "MASTERED":     (85.0, 100.01), # score ≥ 85
}

RECENCY_N = 10      # number of recent attempts used in recency score
RECENCY_DECAY = 0.85  # weight multiplier per step back in history

class MasteryState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    VERY_WEAK   = "VERY_WEAK"
    WEAK        = "WEAK"
    DEVELOPING  = "DEVELOPING"
    PROFICIENT  = "PROFICIENT"
    MASTERED    = "MASTERED"
```

#### Function Signatures

```python
def calculate_mastery(
    questions_correct: int,
    questions_attempted: int,
    difficulty_weighted_correct: float,
    difficulty_weighted_attempted: float,
    recency_score: float,
) -> float:
    """
    Compute the LexiMind Mastery Score.

    Formula:
        base_accuracy = questions_correct / questions_attempted  (0.0 if attempted=0)
        difficulty_accuracy = difficulty_weighted_correct / difficulty_weighted_attempted  (0.0 if attempted=0)
        mastery_score = 100 × (0.5 × base_accuracy + 0.3 × difficulty_accuracy + 0.2 × recency_score)

    Args:
        questions_correct: number of correct answers, must be ≥ 0 and ≤ questions_attempted
        questions_attempted: total attempts, must be ≥ 0
        difficulty_weighted_correct: sum of DIFFICULTY_WEIGHTS[difficulty] for correct answers
        difficulty_weighted_attempted: sum of DIFFICULTY_WEIGHTS[difficulty] for all attempts
        recency_score: pre-computed value in [0.0, 1.0] from compute_recency_score()

    Returns:
        float in [0.0, 100.0]

    Raises:
        ValueError: if questions_correct > questions_attempted, or
                    difficulty_weighted_correct > difficulty_weighted_attempted, or
                    recency_score outside [0.0, 1.0]
        ConfigurationError: if DIFFICULTY_WEIGHTS or STATE_THRESHOLDS is missing/malformed
    """


def compute_recency_score(
    attempts: list,  # list of QuestionAttempt ordered oldest→newest
    n: int = RECENCY_N,
    decay: float = RECENCY_DECAY,
) -> float:
    """
    Compute a recency-weighted correctness score using exponential decay.

    The most recent attempt has weight 1.0. Each step back in history multiplies
    the weight by `decay` (default 0.85). The weighted correct answers are divided
    by the total weighted attempts to produce a score in [0.0, 1.0].

    Formula:
        weights = [decay^(n-1-i) for i in range(len(last_n_attempts))]
        recency_score = sum(w * correct for w, attempt in zip(weights, last_n))
                      / sum(weights)

    Returns 0.0 if the attempts list is empty.
    """


def get_mastery_state(
    mastery_score: float,
    questions_attempted: int,
) -> MasteryState:
    """
    Derive MasteryState from score and attempt count using STATE_THRESHOLDS.
    Returns NOT_STARTED when questions_attempted == 0, regardless of score.
    """


async def update_concept_mastery(
    db: AsyncSession,
    user_id: str,
    concept_id: str,
    is_correct: bool,
    difficulty: str,
    time_taken: Optional[float] = None,
    quiz_id: Optional[str] = None,
    question_id: Optional[int] = None,
) -> ConceptMastery:
    """
    Atomically update or create a ConceptMastery record after a single answer.
    Steps:
    1. Fetch or create ConceptMastery row
    2. Record QuestionAttempt
    3. Recompute difficulty_weighted totals from all stored attempts
    4. Call compute_recency_score() on last RECENCY_N attempts
    5. Call calculate_mastery() with updated values
    6. Update streak (increment on correct, reset to 0 on incorrect)
    7. Update last_attempted_at and last_correct_at
    8. Derive new state via get_mastery_state()
    9. Update updated_at
    Returns the updated ConceptMastery record.
    """


async def get_weak_concepts(
    db: AsyncSession,
    user_id: str,
) -> list:
    """
    Return all weak concepts for a user using a single JOIN query (no N+1).

    A concept is weak if any of:
    - mastery_score < 60
    - state in {VERY_WEAK, WEAK, DEVELOPING}
    - last 10 attempts contain 3+ consecutive incorrect ending at most recent
    - no attempt in last 30 days (and at least 1 attempt exists)

    Returns list of WeakConceptResult dataclass instances, ordered by
    ascending mastery_score, ties broken by ascending concept_id.

    Reason field values:
    - "low mastery score"       — mastery_score < 60
    - "recent incorrect streak" — 3+ consecutive incorrect in last 10 attempts
    - "prerequisite weakness"   — a prerequisite has mastery_score < 60
    - "no recent practice"      — no attempt in last 30 days
    """
```

#### WeakConceptResult dataclass

```python
@dataclass
class WeakConceptResult:
    concept_id: str
    concept_name: str
    subject_id: Optional[str]
    chapter_id: Optional[str]
    mastery_score: float
    state: str
    reason: str  # max 300 chars
```

---

### New Service: `backend/app/services/prerequisite_graph.py`

```python
from functools import lru_cache
from typing import Dict, List, Optional, Set

# Built from education.py CONCEPTS at module load time, then merged with DB
# The in-process cache is valid for curriculum data (immutable between requests).

@lru_cache(maxsize=1)
def build_curriculum_graph() -> Dict[str, List[str]]:
    """
    Build prerequisite mapping from education.py CONCEPTS.
    Returns dict: {concept_id: [prerequisite_concept_id, ...]}
    Detects and logs cycles; excludes all concepts involved in a cycle.
    """


def get_prerequisites(concept_id: str) -> List[str]:
    """Return direct prerequisite concept IDs. Empty list if none or concept not found."""


def get_dependents(concept_id: str) -> List[str]:
    """Return concept IDs that directly depend on concept_id."""


async def is_prerequisite_mastered(
    db: AsyncSession,
    user_id: str,
    concept_id: str,
) -> bool:
    """
    Return True when all direct prerequisites of concept_id have mastery_score ≥ 60
    for the given user, or when concept_id has no prerequisites.
    Raises ValueError if concept_id is not in the graph.
    """


def detect_cycles(graph: Dict[str, List[str]]) -> Set[str]:
    """
    DFS-based cycle detection. Returns the set of all concept IDs involved in
    any cycle so they can be excluded from the graph.
    """
```

---

### New Service: `backend/app/services/recommendation_engine.py`

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class RecommendationType(str, Enum):
    LEARN    = "LEARN"
    REVIEW   = "REVIEW"
    PRACTICE = "PRACTICE"
    PYQ      = "PYQ"
    QUIZ     = "QUIZ"

@dataclass
class Recommendation:
    concept_id: str
    concept_name: str
    reason: str              # 10–300 chars
    estimated_minutes: int   # 1–120
    priority: int            # 1 (highest) – 5
    type: RecommendationType


async def get_next_recommendation(
    db: AsyncSession,
    user_id: str,
    subject_id: Optional[str] = None,
) -> Recommendation:
    """
    Return a single Recommendation following priority order:
    1. Overdue spaced reviews (next_review_at ≤ now, priority=1)
    2. Weak prerequisites blocking progress (mastery < 60, priority=2)
    3. Weak concepts in current subject (mastery < 60, priority=3)
    4. Next concept in learning path (priority=4)
    5. New concept to learn (priority=5)

    When no mastery data exists, returns LEARN type, priority=1,
    pointing to position-1 concept in the default subject's learning path.

    Never recommends a MASTERED concept unless next_review_at ≤ now.

    Tiebreakers: weakness_score → prerequisite_readiness →
                 time_since_last_attempt (hours) → learning_path_position
    """
```

---

### New Service: `backend/app/services/adaptive_quiz.py`

```python
from dataclasses import dataclass, field
from typing import List, Optional

# Configurable constants
ADAPTIVE_CONSTANTS = {
    "CORRECT_STREAK_UP": 3,    # consecutive correct → tier up
    "INCORRECT_STREAK_DOWN": 2, # consecutive incorrect → tier down
    "RECENCY_WINDOW_DAYS": 7,
}

@dataclass
class AdaptiveQuizResult:
    quiz_id: str
    questions: List[dict]
    insufficient_bank: bool
    ai_generated_count: int
    source_counts: dict
    difficulty_distribution: dict


async def assemble_adaptive_quiz(
    db: AsyncSession,
    user_id: str,
    subject_id: str,
    chapter_id: Optional[str] = None,
    concept_id: Optional[str] = None,
    question_count: int = 10,
) -> AdaptiveQuizResult:
    """
    Assemble an adaptive quiz:
    1. Get mastery_score for concept/subject (0 if no record)
    2. Determine difficulty tier from mastery band:
       - mastery < 40  → primary=EASY,   secondary=MEDIUM
       - mastery in [40,70) → primary=MEDIUM, secondary=EASY/HARD
       - mastery ≥ 70  → primary=HARD,   secondary=MEDIUM
    3. Fetch all eligible questions from DB via quiz_bank.py
    4. Rank questions:
       a. Primary tier, not seen in last 7 days
       b. Primary tier, seen in last 7 days
       c. Secondary tier, not seen in last 7 days
       d. Secondary tier, seen in last 7 days
    5. Select question_count questions, deduplicating within session
    6. Set insufficient_bank=True if fewer than question_count available
    Works entirely from DB when LLM is unavailable.
    question_count is clamped to [1, 30].
    """


def compute_session_difficulty_adjustment(
    streak_correct: int,
    streak_incorrect: int,
    current_tier: str,
) -> str:
    """
    Apply in-session difficulty adjustment:
    - 3+ consecutive correct and tier != HARD  → return tier_up(current_tier)
    - 2+ consecutive incorrect and tier != EASY → return tier_down(current_tier)
    - otherwise → return current_tier
    """
```

---

### New Service: `backend/app/services/review_scheduler.py`

```python
REVIEW_SEQUENCE = [1, 3, 7, 14, 30]  # days


async def schedule_review(
    db: AsyncSession,
    user_id: str,
    concept_id: str,
    mastery_state: str,
) -> None:
    """
    Called when a concept reaches PROFICIENT state for the first time,
    or after any review session.
    Creates or updates ReviewSchedule row.
    On first schedule: current_interval_days=1, review_count=0.
    """


def advance_interval(current_days: int) -> int:
    """
    Return the next interval in REVIEW_SEQUENCE.
    If current_days == 30, returns 30 (capped).
    If current_days not in sequence, returns the first value in sequence
    greater than current_days, or 30 if none.
    """


def reset_interval() -> int:
    """Return 1 (the first interval after a mastery regression)."""


async def get_overdue_reviews(
    db: AsyncSession,
    user_id: str,
) -> list:
    """
    Return ReviewSchedule rows where next_review_at < UTC now,
    ordered by next_review_at ascending (most overdue first).
    """


async def apply_review_result(
    db: AsyncSession,
    user_id: str,
    concept_id: str,
    mastery_before: float,
    mastery_after: float,
) -> None:
    """
    Advance or reset the review interval based on mastery change.
    mastery_after >= mastery_before → advance_interval()
    mastery_after < mastery_before  → reset_interval()
    Sets next_review_at = UTC now + new interval days.
    Works for both on-time and early reviews.
    """
```

---

### New Service: `backend/app/services/study_plan.py`

```python
from dataclasses import dataclass

@dataclass
class StudyActivity:
    type: str         # "REVIEW" | "PRACTICE" | "LEARN"
    concept_id: str
    concept_name: str
    duration_minutes: int


async def build_daily_plan(
    db: AsyncSession,
    user_id: str,
    study_goal_minutes: int = 30,
) -> list[StudyActivity]:
    """
    Build today's study plan, capped at study_goal_minutes total.
    Priority order:
    1. Overdue reviews — 10 minutes each (from get_overdue_reviews())
    2. Weak concept practice — 10 minutes each (from get_weak_concepts())
    3. Next-concept learning — remaining minutes
    Total never exceeds study_goal_minutes.
    Returns between 1 and 3 activities.
    """
```

---

## Data Models

### Extended: `backend/app/models/academic.py`

#### ConceptMastery (EXTENDED from existing)

The existing `ConceptMastery` model in `academic.py` is extended with new columns. All existing columns are preserved.

```python
class ConceptMastery(Base):
    __tablename__ = "concept_mastery"
    __table_args__ = (UniqueConstraint("user_id", "concept_id", name="uq_user_concept_mastery"),)

    # --- EXISTING COLUMNS (unchanged) ---
    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(String(80), nullable=False, index=True)
    concept_id          = Column(String(120), nullable=False, index=True)
    mastery_score       = Column(Float, default=0.0)
    questions_attempted = Column(Integer, default=0)
    questions_correct   = Column(Integer, default=0)
    last_attempted      = Column(DateTime, nullable=True)   # ← renamed last_attempted_at below (migration adds alias column)
    confidence          = Column(Float, default=0.0)
    status              = Column(String(30), default="not_started")  # ← existing; Phase 3 uses 'state' field

    # --- NEW COLUMNS (Phase 3 additions) ---
    questions_incorrect = Column(Integer, default=0)        # new
    last_correct_at     = Column(DateTime, nullable=True)   # new
    streak              = Column(Integer, default=0)        # consecutive correct; 0 on incorrect
    state               = Column(String(30), default="NOT_STARTED")  # MasteryState enum value
    next_review_at      = Column(DateTime, nullable=True)   # for spaced repetition
    updated_at          = Column(DateTime,
                            default=lambda: datetime.now(timezone.utc),
                            onupdate=lambda: datetime.now(timezone.utc))

    # Compatibility note: existing `status` column is kept; Phase 3 logic reads from `state`.
    # During migration, state is initialised from status using the mapping:
    # "mastered" → "MASTERED", "needs_review" → "VERY_WEAK", "in_progress" → "DEVELOPING", others → "NOT_STARTED"
```

#### NEW: QuestionAttempt

The existing `QuizAnswer` table lacks `difficulty` as a first-class column and is tightly coupled to quiz sessions. Phase 3 extends by adding a `QuestionAttempt` table that references `QuizAnswer.id` where possible, avoiding duplication of raw answer data.

```python
class QuestionAttempt(Base):
    """
    Records every individual question answer for adaptive engine use.
    Requirement 2.6: Reuses QuizAnswer when it covers required fields;
    QuestionAttempt stores the adaptive-specific fields only.
    """
    __tablename__ = "question_attempts"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(String(80), nullable=False, index=True)
    question_id     = Column(Integer, ForeignKey("questions.id"), nullable=True, index=True)
    concept_id      = Column(String(120), nullable=True, index=True)
    quiz_id         = Column(String(80), nullable=True, index=True)
    selected_answer = Column(Text, nullable=True)
    correct         = Column(Boolean, nullable=False)
    difficulty      = Column(String(20), nullable=True)   # easy | medium | hard
    time_taken      = Column(Float, nullable=True)        # seconds ≥ 0, max 3600
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    quiz_answer_id  = Column(Integer, ForeignKey("quiz_answers.id"), nullable=True)  # optional link to QuizAnswer
```

#### NEW: ReviewSchedule

```python
class ReviewSchedule(Base):
    """Spaced-repetition schedule per user per concept."""
    __tablename__ = "review_schedules"
    __table_args__ = (UniqueConstraint("user_id", "concept_id", name="uq_user_concept_review"),)

    id                   = Column(Integer, primary_key=True, index=True)
    user_id              = Column(String(80), nullable=False, index=True)
    concept_id           = Column(String(120), nullable=False, index=True)
    next_review_at       = Column(DateTime, nullable=False, index=True)
    current_interval_days = Column(Integer, default=1)
    review_count         = Column(Integer, default=0)
    created_at           = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at           = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                              onupdate=lambda: datetime.now(timezone.utc))
```

### Migration Strategy

Phase 3 adds columns to `concept_mastery` and creates two new tables. The existing migration helper in `database.py` is extended with a `_PHASE3_NEW_COLUMNS` list that mirrors the `_DOCUMENT_NEW_COLUMNS` pattern already in use:

```python
_PHASE3_MASTERY_COLUMNS = [
    ("questions_incorrect", "INTEGER DEFAULT 0"),
    ("last_correct_at",     "DATETIME"),
    ("streak",              "INTEGER DEFAULT 0"),
    ("state",               "VARCHAR(30) DEFAULT 'NOT_STARTED'"),
    ("next_review_at",      "DATETIME"),
    ("updated_at",          "DATETIME"),
]
```

New tables (`question_attempts`, `review_schedules`) are created by `Base.metadata.create_all()` because they are brand-new; no ALTER TABLE is needed for them.

---

## API Routes

### Extend `backend/app/api/learning.py`

All routes are appended to the existing `router` defined in the file. No existing routes are modified.

| Method | Path | Handler | Description |
|---|---|---|---|
| GET | `/api/learning/mastery/{user_id}` | `get_mastery` | All mastery records for user (already exists; returns extended fields) |
| GET | `/api/learning/mastery/{user_id}/{concept_id}` | `get_concept_mastery` | Single concept mastery (already exists; returns extended fields) |
| POST | `/api/learning/quiz-attempt` | `submit_quiz_attempt` | Existing; now also calls update_concept_mastery() per answer |
| GET | `/api/learning/recommended/{user_id}` | `get_recommended` | Existing stub; replace body with get_next_recommendation() |
| GET | `/api/learning/weak-concepts/{user_id}` | `get_weak_concepts_route` | Existing stub; replace body with get_weak_concepts() |
| GET | `/api/learning/learning-path/{user_id}/{subject_id}` | `get_learning_path` | Existing; extend with Phase 3 status precedence |
| GET | `/api/learning/review-schedule` | `get_review_schedule` | **NEW** — query param user_id |
| GET | `/api/learning/mistakes` | `get_mistakes` | **NEW** — query params user_id, concept_id (optional) |
| GET | `/api/learning/progress/{user_id}` | `get_progress` | Existing; extend with new fields |
| POST | `/api/learning/mastery/update` | `update_mastery` | Existing; now delegates to update_concept_mastery() |

### Extend `backend/app/api/quizzes.py`

```
POST /api/quizzes/adaptive   (NEW)
```

Request body:
```json
{
  "user_id": "string (required, max 128)",
  "subject_id": "string (required, max 128)",
  "chapter_id": "string (optional)",
  "concept_id": "string (optional)",
  "question_count": 10
}
```

Response:
```json
{
  "quiz_id": "string",
  "questions": [...],
  "insufficient_bank": false,
  "ai_generated_count": 0,
  "source_counts": {},
  "difficulty_distribution": {}
}
```

### Extend `backend/app/api/chat.py`

`ChatRequest` is extended with a `student_context` field:

```python
class StudentContext(BaseModel):
    mastery_score: Optional[float] = None   # 0–100
    mastery_state: Optional[str] = None     # MasteryState value
    weak_concepts: Optional[List[str]] = []
    recent_mistakes: Optional[List[dict]] = []

class ChatRequest(BaseModel):
    # ... all existing fields unchanged ...
    student_context: Optional[StudentContext] = None
```

The `_build_tutor_prompt()` function is extended to incorporate `mastery_state` in the system instruction, following the logic:
- VERY_WEAK / WEAK → "Explain from first principles. Avoid terminology not already in the student's weak concept list."
- DEVELOPING → "Reinforce core understanding with worked examples."
- PROFICIENT / MASTERED → "Focus on advanced applications and exam-style questions."

The `EXPLAIN_MISTAKE` action validates that `recent_mistakes` is non-empty before generating a response.

---

## Learning Path Integration

The existing `build_learning_path()` in `mastery.py` is kept and used as a subroutine. The `get_learning_path` route handler in `learning.py` is extended to apply the Phase 3 status precedence on top of the existing output:

```
Status precedence (highest to lowest):
  NEEDS_REVIEW  → next_review_at < UTC now AND mastery < 85
  COMPLETED     → mastery ≥ 85 AND NOT overdue for review
  CURRENT       → lowest chapter-order index among RECOMMENDED items
                  (or most-recently-accessed if no RECOMMENDED items)
  RECOMMENDED   → all prerequisites mastery ≥ 85, not COMPLETED/CURRENT
  LOCKED        → at least one prerequisite mastery < 85
```

The response shape is extended to always include all four fields:
```json
{
  "userId": "...",
  "subjectId": "...",
  "items": [...],
  "currentConcept": "concept_id or null",
  "completedConcepts": [...],
  "weakConcepts": [...],        // mastery 1–59
  "recommendedConcepts": [...]
}
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Mastery Score Bounds Invariant

*For any* valid inputs where `questions_correct ≤ questions_attempted`, `difficulty_weighted_correct ≤ difficulty_weighted_attempted`, and `recency_score ∈ [0.0, 1.0]`, calling `calculate_mastery()` SHALL return a value in `[0.0, 100.0]`.

**Validates: Requirements 3.1, 3.2, 3.16**

---

### Property 2: Mastery Score Determinism

*For any* valid set of inputs, calling `calculate_mastery()` twice with the same arguments SHALL produce the same `mastery_score` on both invocations (no random elements).

**Validates: Requirements 3.17**

---

### Property 3: Invalid Input Raises ValueError

*For any* input combination where `questions_correct > questions_attempted`, or `difficulty_weighted_correct > difficulty_weighted_attempted`, or `recency_score` is outside `[0.0, 1.0]`, calling `calculate_mastery()` SHALL raise a `ValueError` identifying the invalid parameter.

**Validates: Requirements 3.5**

---

### Property 4: Weak Concept Filter Correctness

*For any* set of `ConceptMastery` records for a user, every item returned by `get_weak_concepts(user_id)` SHALL have `mastery_score < 60` or `state ∈ {VERY_WEAK, WEAK, DEVELOPING}`, and every record that meets this condition SHALL be present in the returned list.

**Validates: Requirements 4.1, 4.7**

---

### Property 5: User Data Isolation

*For any* two distinct users A and B, a request for user A's mastery, attempts, recommendations, or review schedule SHALL return only records whose `user_id` equals A's identifier, and SHALL contain no records belonging to user B.

**Validates: Requirements 16.1, 16.2, 16.3**

---

### Property 6: Difficulty Targeting Proportion

*For any* assembled `Adaptive_Quiz` where the student's `mastery_score` is below 40, at least 60% of selected questions SHALL come from the EASY difficulty tier. Equivalently, for `mastery_score ∈ [40, 70)` the MEDIUM tier proportion SHALL be ≥ 60%, and for `mastery_score ≥ 70` the HARD tier proportion SHALL be ≥ 60%.

**Validates: Requirements 7.3, 7.4, 7.5**

---

### Property 7: Session Question Uniqueness

*For any* assembled `Adaptive_Quiz`, the list of question IDs SHALL contain no duplicates — no question SHALL appear more than once in a single quiz session.

**Validates: Requirements 7.9, 8.3**

---

### Property 8: Prerequisite Mastery Correctness

*For any* user and concept, `is_prerequisite_mastered()` SHALL return `True` if and only if all direct prerequisites of that concept have `mastery_score ≥ 60` for that user, or the concept has no direct prerequisites.

**Validates: Requirements 5.4**

---

### Property 9: Review Interval Progression

*For any* current interval value in the sequence `[1, 3, 7, 14, 30]`, calling `advance_interval(current_days)` SHALL return the next value in that sequence, and calling it when `current_days = 30` SHALL return 30 (capped). *For any* review session where `mastery_after < mastery_before`, the resulting `current_interval_days` SHALL be 1.

**Validates: Requirements 10.3, 10.5**

---

### Property 10: Learning Path Unique Status

*For any* user mastery state and subject, every learning path item returned by the learning path endpoint SHALL be assigned exactly one status (no item with zero statuses, no item with two conflicting statuses), and the assignment SHALL follow the documented precedence order.

**Validates: Requirements 11.1**

---

### Property 11: Prerequisite Graph is a DAG

*For any* curriculum concept graph (including inputs with cycles), the graph built by `build_curriculum_graph()` SHALL be a directed acyclic graph — the set of concepts returned after cycle exclusion SHALL contain no circular dependency chains.

**Validates: Requirements 5.9**

---

## Error Handling

| Scenario | HTTP Status | Response Body |
|---|---|---|
| Database unavailable | 503 | `{"detail": "Service temporarily unavailable. Database connection failed."}` |
| Missing required parameter | 422 | `{"detail": [{"loc": ["field_name"], "msg": "reason"}]}` |
| user_id empty/whitespace/>128 chars | 422 | identifies `user_id` and reason |
| user_id valid but no data | 200 | `[]` for lists, `{}` for objects |
| question_count ≤ 0 | — | clamped to 1, no error |
| NULL streak in DB | — | treated as 0 in calculate_mastery() |
| LLM provider unavailable | 200 | fallback response with `explanation_source: FALLBACK` |
| EXPLAIN_MISTAKE with empty recent_mistakes | 400 | `{"detail": "No mistake record available for this concept."}` |
| SIMILAR_QUESTION with no DB questions | 200 | response indicating no similar question available |
| Concept not found in prerequisite graph | 404 | identifies concept_id |
| Write request user_id mismatch | 422 | identifies the mismatch |

All unhandled exceptions fall through to the existing `global_exception_handler` in `main.py` which returns 500. The DB unavailability 503 is caught by a middleware or try/except in the route handlers before the global handler sees it.

---

## Testing Strategy

### Unit Tests — `backend/tests/test_adaptive_engine.py`

All tests use in-memory SQLite via `aiosqlite` with `pytest-asyncio`. No external API calls. Each test creates its own database state and tears it down.

Property-based tests use [**Hypothesis**](https://hypothesis.readthedocs.io/en/latest/) (pure-Python, no external services, runs 100+ examples per property by default).

```
pytest backend/tests/
```

must complete within 60 seconds on a standard developer machine.

#### Unit test cases (example-based)

| Test | Input | Expected Output |
|---|---|---|
| `test_calculate_mastery_zero_attempts` | attempted=0 | score=0.0, state=NOT_STARTED |
| `test_calculate_mastery_all_correct_easy` | correct=5, attempted=5, diff_correct=5.0, diff_attempted=5.0, recency=1.0 | 100.0 |
| `test_calculate_mastery_all_incorrect` | correct=0, attempted=5, diff_correct=0, diff_attempted=6.25, recency=0.0 | 0.0 |
| `test_calculate_mastery_mixed_with_weights` | Fixed known values | exact to 4 decimal places |
| `test_mastery_state_boundaries` | scores: 0,29,30,49,50,69,70,84,85 | distinct states at each boundary |
| `test_get_weak_concepts_empty` | user with no records | `[]` |
| `test_get_weak_concepts_includes_below_60` | scores: 30,59,60,90 | returns 30 and 59 only |
| `test_get_weak_concepts_excludes_above_60` | score=60 | not in result |
| `test_is_prerequisite_mastered_no_prereqs` | concept with empty prerequisites | `True` |
| `test_is_prerequisite_mastered_all_above_60` | prereqs all ≥ 60 | `True` |
| `test_is_prerequisite_mastered_one_below_60` | one prereq at 55 | `False` |
| `test_question_selection_recency_penalty` | questions: some in last 7 days | older questions ranked first |
| `test_difficulty_targeting_mastery_below_40` | mastery=30, 10 questions | ≥ 6 from EASY tier |
| `test_insufficient_bank_flag` | bank has 3 questions, request 10 | `insufficient_bank=True` |
| `test_review_interval_progression` | 5 consecutive successful reviews | 1→3→7→14→30 |
| `test_review_interval_reset_on_regression` | mastery drops mid-sequence | interval resets to 1 |

#### Property-based tests (Hypothesis)

```python
# Feature: adaptive-learning-engine, Property 1: Mastery Score Bounds Invariant
@given(
    questions_correct=st.integers(min_value=0, max_value=1000),
    questions_attempted=st.integers(min_value=0, max_value=1000),
    recency_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_mastery_score_bounds(questions_correct, questions_attempted, recency_score):
    assume(questions_correct <= questions_attempted)
    # derive difficulty weighted values consistently
    score = calculate_mastery(
        questions_correct, questions_attempted,
        float(questions_correct), float(questions_attempted),
        recency_score
    )
    assert 0.0 <= score <= 100.0

# Feature: adaptive-learning-engine, Property 2: Mastery Score Determinism
@given(valid_mastery_inputs())
def test_mastery_determinism(inputs):
    s1 = calculate_mastery(**inputs)
    s2 = calculate_mastery(**inputs)
    assert s1 == s2

# Feature: adaptive-learning-engine, Property 3: Invalid Input Raises ValueError
@given(invalid_mastery_inputs())
def test_invalid_inputs_raise_value_error(inputs):
    with pytest.raises(ValueError):
        calculate_mastery(**inputs)

# Feature: adaptive-learning-engine, Property 5: User Data Isolation
@given(user_a_id=valid_user_ids(), user_b_id=valid_user_ids())
async def test_user_isolation(user_a_id, user_b_id):
    assume(user_a_id != user_b_id)
    # seed records for both users, request user A's data
    # verify no user B records appear

# Feature: adaptive-learning-engine, Property 6: Difficulty Targeting Proportion
@given(mastery=st.floats(min_value=0, max_value=100), bank=st.lists(...))
async def test_difficulty_proportion(mastery, bank):
    quiz = await assemble_adaptive_quiz(...)
    tier = expected_primary_tier(mastery)
    proportion = sum(1 for q in quiz.questions if q["difficulty"] == tier) / len(quiz.questions)
    assert proportion >= 0.6 or len(quiz.questions) == 0

# Feature: adaptive-learning-engine, Property 7: Session Question Uniqueness
@given(bank=st.lists(..., min_size=1), count=st.integers(min_value=1, max_value=30))
async def test_no_duplicate_questions_in_session(bank, count):
    quiz = await assemble_adaptive_quiz(...)
    ids = [q["id"] for q in quiz.questions]
    assert len(ids) == len(set(ids))

# Feature: adaptive-learning-engine, Property 9: Review Interval Progression
@given(starting_index=st.integers(min_value=0, max_value=4))
def test_review_interval_sequence(starting_index):
    current = REVIEW_SEQUENCE[starting_index]
    expected_next = REVIEW_SEQUENCE[min(starting_index + 1, len(REVIEW_SEQUENCE) - 1)]
    assert advance_interval(current) == expected_next

# Feature: adaptive-learning-engine, Property 11: Prerequisite Graph is a DAG
@given(concept_graph=valid_concept_graphs_with_possible_cycles())
def test_built_graph_is_dag(concept_graph):
    built = build_curriculum_graph_from(concept_graph)
    assert not detect_cycles(built)  # empty set = no cycles
```

**Hypothesis configuration:** `settings.suppress_health_check = [HealthCheck.too_slow]` is not needed; all tests run in-memory. Minimum examples per property: 100 (Hypothesis default).

### Integration Tests

Not part of the automated test suite (require running server + DB). Documented in the Phase 2 Audit Approach section above.

---

## Frontend: Dashboard and Progress Page

### Extend `Dashboard.tsx`

Replace existing placeholder stats with live API calls using `@tanstack/react-query`:

```typescript
// Continue Learning section
const { data: recommendation } = useQuery({
  queryKey: ["recommended", userId],
  queryFn: () => api.get(`/api/learning/recommended/${userId}`).then(r => r.data),
});

// Today's Plan section
const { data: reviewSchedule } = useQuery({
  queryKey: ["review-schedule", userId],
  queryFn: () => api.get(`/api/learning/review-schedule?user_id=${userId}`).then(r => r.data),
});

// Weak Areas section
const { data: weakConcepts } = useQuery({
  queryKey: ["weak-concepts", userId],
  queryFn: () => api.get(`/api/learning/weak-concepts/${userId}`).then(r => r.data),
});

// Progress metrics
const { data: progress } = useQuery({
  queryKey: ["progress", userId],
  queryFn: () => api.get(`/api/learning/progress/${userId}`).then(r => r.data),
});
```

Empty-state rules:
- If `weakConcepts` is empty and `progress` has no attempts → display "Complete your first quiz to see your personalised dashboard"
- Never render zero-value mastery scores without a "no data yet" label

### New `ProgressPage.tsx`

Displays full progress history using the same query hooks. Hides performance charts when `totalQuizAttempts < 2` and shows "Not enough data yet. Complete more quizzes to see your progress charts." Error states from either `progress` or `weak-concepts` API are shown as named error messages rather than silent failures.

---

## Demo Seed Data (Phase 3 Extension to `demo_seed.py`)

The existing `seed_demo_if_needed()` idempotency check is extended: Phase 3 also checks for the presence of a `ReviewSchedule` seed record before inserting. If it already exists, Phase 3 seeding is skipped.

Phase 3 seed adds:
- **Prerequisite relationships** defined between the 3 existing DEMO concepts:
  - `partial-derivatives-dc` has no prerequisites (entry concept)
  - `homogeneous-functions` prerequisites: `["partial-derivatives-dc"]`
  - `euler-theorem-dc` prerequisites: `["partial-derivatives-dc", "homogeneous-functions"]`
- **10 additional questions** covering easy/medium/hard across the 3 concepts (these augment the existing 7 DEMO questions to reach ≥ 10 and ensure all 3 difficulty levels are present)
- **1 ConceptMastery record** for `user_id="demo-user-1"`, `concept_id="partial-derivatives-dc"`, `state=MASTERED`, `mastery_score=88.0`, `questions_attempted=10`, `questions_correct=9`
- **1 ConceptMastery record** for `user_id="demo-user-1"`, `concept_id="homogeneous-functions"`, `state=WEAK`, `mastery_score=35.0`, `questions_attempted=4`, `questions_correct=1`
- **1 QuestionAttempt history** of 4 attempts for the WEAK concept, with the last 3 being incorrect (to trigger the streak detection rule)
- **1 ReviewSchedule record** for the MASTERED concept, `next_review_at=UTC now - 1 day` (overdue, to exercise the review flow)

---

## Security

- Every query in adaptive services includes a `WHERE user_id = :user_id` predicate. No query ever fetches all users' data.
- Write requests that include `user_id` in the body are validated against the `user_id` path parameter; mismatch returns 422.
- API keys remain in `backend/.env` only. The `.env` file is confirmed to be in `.gitignore` during the Phase 2 audit.
- The `provider_status()` function from `services/llm.py` is the sole LLM availability check mechanism. No other component performs its own LLM availability check.
- No new external caching infrastructure (no Redis, Memcached, or distributed cache). In-process `functools.lru_cache` is acceptable only for the prerequisite graph (read-only curriculum data).
