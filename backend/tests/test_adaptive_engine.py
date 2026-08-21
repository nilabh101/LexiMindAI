"""Phase 3 adaptive engine tests — deterministic, no LLM, no network."""
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.adaptive_config import (
    DIFFICULTY_WEIGHTS,
    REVIEW_INTERVALS_DAYS,
    concept_state,
    difficulty_weight,
    target_difficulties,
)
from app.core.database import Base
from app.models.academic import (
    AcademicNote, ConceptMastery, Question, QuestionConcept, QuizAnswer,
)
from app.services.adaptive_quiz import build_adaptive_quiz, next_difficulty
from app.services.concept_graph import (
    get_dependents,
    get_prerequisites,
    is_prerequisite_mastered,
)
from app.services.learning_path import build_path
from app.services.mastery import (
    apply_quiz_results, calculate_mastery, recalculate_concept_mastery, recency_weight,
)
from app.services.mistakes import analyze_mistake_patterns, get_mistakes, get_question_history
from app.services.progress import compute_streak, get_progress
from app.services.recommendations import get_daily_plan, get_next_recommendation
from app.services.review import next_interval_days, schedule_next_review
from app.services.tutor import (
    build_student_context, fallback_action_reply, normalize_action, note_sources, resolve_action,
)
from app.services.weakness import get_weak_concepts

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)


def attempt(correct: bool, difficulty: str = "MEDIUM", days_ago: float = 0.0):
    return {"correct": correct, "difficulty": difficulty, "attempted_at": NOW - timedelta(days=days_ago)}


# ── Mastery calculation ───────────────────────────────────────────────────────

def test_mastery_is_deterministic_for_five_questions_four_correct():
    attempts = [attempt(True), attempt(True), attempt(True), attempt(True), attempt(False)]
    first = calculate_mastery(attempts, now=NOW)
    second = calculate_mastery(list(attempts), now=NOW)
    assert first == second
    # weighted accuracy 0.8, evidence 5/8 → 0.625*0.8 + 0.375*0.5 = 0.6875
    assert first["mastery_score"] == pytest.approx(68.8, abs=0.05)
    assert first["attempted"] == 5 and first["correct"] == 4 and first["incorrect"] == 1
    assert first["accuracy"] == 80.0


def test_no_attempts_is_not_started():
    result = calculate_mastery([], now=NOW)
    assert result["mastery_score"] == 0.0
    assert result["state"] == "NOT_STARTED"


def test_harder_correct_answers_produce_higher_mastery():
    easy = calculate_mastery([attempt(True, "EASY"), attempt(False, "HARD")], now=NOW)
    hard = calculate_mastery([attempt(True, "HARD"), attempt(False, "EASY")], now=NOW)
    assert hard["mastery_score"] > easy["mastery_score"]
    assert difficulty_weight("HARD") > difficulty_weight("EASY") == DIFFICULTY_WEIGHTS["EASY"]
    assert difficulty_weight(None) == DIFFICULTY_WEIGHTS["MEDIUM"]


def test_recent_performance_outweighs_old_performance():
    improving = calculate_mastery(
        [attempt(False, days_ago=120), attempt(False, days_ago=120), attempt(True, days_ago=1), attempt(True, days_ago=1)],
        now=NOW,
    )
    declining = calculate_mastery(
        [attempt(True, days_ago=120), attempt(True, days_ago=120), attempt(False, days_ago=1), attempt(False, days_ago=1)],
        now=NOW,
    )
    assert improving["mastery_score"] > declining["mastery_score"]


def test_recency_weight_decays_with_age():
    assert recency_weight(NOW, NOW) == pytest.approx(1.0)
    assert recency_weight(NOW - timedelta(days=30), NOW) == pytest.approx(0.5, abs=0.01)
    assert recency_weight(NOW - timedelta(days=3650), NOW) >= 0.15


def test_streak_counts_trailing_correct_answers():
    assert calculate_mastery([attempt(False), attempt(True), attempt(True)], now=NOW)["streak"] == 2
    assert calculate_mastery([attempt(True), attempt(False)], now=NOW)["streak"] == 0


# ── Concept states ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("score,expected", [
    (0, "VERY_WEAK"), (29.9, "VERY_WEAK"), (30, "WEAK"), (49.9, "WEAK"),
    (50, "DEVELOPING"), (69.9, "DEVELOPING"), (70, "PROFICIENT"), (84.9, "PROFICIENT"),
    (85, "MASTERED"), (100, "MASTERED"),
])
def test_concept_state_thresholds(score, expected):
    assert concept_state(score, attempted=1) == expected


def test_concept_state_without_attempts_is_not_started():
    assert concept_state(0, attempted=0) == "NOT_STARTED"


# ── Difficulty selection ──────────────────────────────────────────────────────

def test_target_difficulty_follows_mastery_band():
    assert target_difficulties(20)[0] == "EASY"
    assert target_difficulties(55)[0] == "MEDIUM"
    assert target_difficulties(90) == ["MEDIUM", "HARD"]


def test_in_quiz_difficulty_controller():
    assert next_difficulty("EASY", consecutive_correct=3, consecutive_incorrect=0) == "MEDIUM"
    assert next_difficulty("MEDIUM", consecutive_correct=3, consecutive_incorrect=0) == "HARD"
    assert next_difficulty("HARD", consecutive_correct=5, consecutive_incorrect=0) == "HARD"
    assert next_difficulty("HARD", consecutive_correct=0, consecutive_incorrect=2) == "MEDIUM"
    assert next_difficulty("EASY", consecutive_correct=0, consecutive_incorrect=5) == "EASY"
    assert next_difficulty("MEDIUM", consecutive_correct=2, consecutive_incorrect=1) == "MEDIUM"


# ── Prerequisites ─────────────────────────────────────────────────────────────

def test_prerequisite_graph_uses_curriculum_relationships():
    assert get_prerequisites("euler-theorem-dc") == ["partial-derivatives-dc"]
    assert "euler-theorem-dc" in get_dependents("partial-derivatives-dc")
    assert get_prerequisites("limits-dc") == []
    assert get_prerequisites("unknown-concept") == []


def test_is_prerequisite_mastered():
    weak = ConceptMastery(user_id="u", concept_id="partial-derivatives-dc", mastery_score=35.0,
                          questions_attempted=4, state="WEAK")
    strong = ConceptMastery(user_id="u", concept_id="partial-derivatives-dc", mastery_score=88.0,
                            questions_attempted=8, state="MASTERED")
    assert is_prerequisite_mastered({}, "limits-dc")["mastered"] is True
    blocked = is_prerequisite_mastered({"partial-derivatives-dc": weak}, "euler-theorem-dc")
    assert blocked["mastered"] is False
    assert blocked["weakPrerequisites"][0]["conceptId"] == "partial-derivatives-dc"
    assert is_prerequisite_mastered({"partial-derivatives-dc": strong}, "euler-theorem-dc")["mastered"] is True


# ── Review scheduling ─────────────────────────────────────────────────────────

def test_review_intervals_grow_and_reset():
    assert next_interval_days(None, 1.0) == REVIEW_INTERVALS_DAYS[0]
    assert next_interval_days(1, 1.0) == 3
    assert next_interval_days(3, 1.0) == 7
    assert next_interval_days(30, 1.0) == 30
    assert next_interval_days(14, 0.2) == 1
    assert next_interval_days(7, 0.6) == 7


def test_schedule_next_review_returns_future_date():
    interval, when = schedule_next_review(3, 1.0, now=NOW)
    assert interval == 7
    assert when == NOW + timedelta(days=7)


def test_streak_counts_consecutive_days():
    assert compute_streak([], today=NOW) == 0
    assert compute_streak([NOW, NOW - timedelta(days=1), NOW - timedelta(days=2)], today=NOW) == 3
    assert compute_streak([NOW - timedelta(days=5)], today=NOW) == 0


# ── Learning path ─────────────────────────────────────────────────────────────

def test_learning_path_states():
    concepts = [
        {"id": "limits-dc", "name": "Limits", "chapterId": "dc-em1", "subjectId": "em1-btech"},
        {"id": "partial-derivatives-dc", "name": "Partial Derivatives", "chapterId": "dc-em1", "subjectId": "em1-btech"},
        {"id": "euler-theorem-dc", "name": "Euler's Theorem", "chapterId": "dc-em1", "subjectId": "em1-btech"},
    ]
    rows = [
        ConceptMastery(user_id="u", concept_id="limits-dc", mastery_score=90.0, state="MASTERED", questions_attempted=8),
        ConceptMastery(user_id="u", concept_id="partial-derivatives-dc", mastery_score=35.0, state="WEAK", questions_attempted=5),
    ]
    path = build_path(concepts, rows)
    by_id = {i["conceptId"]: i for i in path["items"]}
    assert by_id["limits-dc"]["status"] == "COMPLETED"
    assert by_id["partial-derivatives-dc"]["status"] == "NEEDS_REVIEW"
    assert by_id["euler-theorem-dc"]["status"] == "LOCKED"
    assert "depends on" in by_id["euler-theorem-dc"]["note"]
    assert path["completed"] == 1


# ── Database-backed behaviour ─────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        await _seed_questions(session)
        yield session
    await engine.dispose()


async def _seed_questions(session: AsyncSession):
    specs = [
        ("euler-theorem-dc", "EASY"), ("euler-theorem-dc", "MEDIUM"), ("euler-theorem-dc", "HARD"),
        ("partial-derivatives-dc", "EASY"), ("partial-derivatives-dc", "MEDIUM"),
        ("limits-dc", "EASY"), ("limits-dc", "MEDIUM"),
    ]
    for index, (concept_id, difficulty) in enumerate(specs, start=1):
        q = Question(
            question_text=f"[TEST] Question {index} on {concept_id}",
            answer="correct-option",
            options=["correct-option", "wrong-option"],
            question_type="MCQ",
            difficulty=difficulty,
            concept_id=concept_id,
            subject_id="em1-btech",
            chapter_id="dc-em1",
            source="DEMO",
            review_status="APPROVED",
        )
        session.add(q)
        await session.flush()
        session.add(QuestionConcept(question_id=q.id, concept_id=concept_id, confidence=1.0))
    await session.flush()


async def _answer(session, user_id, question_id, correct, concept_id, difficulty="MEDIUM"):
    await apply_quiz_results(
        session, user_id, f"quiz-{question_id}-{correct}",
        [{"question_id": question_id, "selected_answer": "x", "correct": correct,
          "concept_id": concept_id, "difficulty": difficulty}],
        subject_id="em1-btech",
    )


@pytest.mark.asyncio
async def test_quiz_completion_persists_attempts_and_updates_mastery(db):
    result = await apply_quiz_results(
        db, "u1", "quiz-1",
        [
            {"question_id": 1, "selected_answer": "a", "correct": True, "concept_id": "euler-theorem-dc"},
            {"question_id": 2, "selected_answer": "b", "correct": False, "concept_id": "euler-theorem-dc"},
        ],
        subject_id="em1-btech",
    )
    assert result["correct"] == 1 and result["total"] == 2 and result["accuracy"] == 50.0
    perf = result["concept_performance"][0]
    assert perf["conceptId"] == "euler-theorem-dc"
    assert perf["nextReviewAt"] is not None

    history = await get_question_history(db, "u1")
    assert len(history) == 2
    assert history[0]["difficulty"] in {"EASY", "MEDIUM", "HARD"}  # taken from the question bank


@pytest.mark.asyncio
async def test_user_isolation(db):
    await _answer(db, "user-a", 1, False, "euler-theorem-dc")
    await _answer(db, "user-a", 2, False, "euler-theorem-dc")
    await _answer(db, "user-b", 1, True, "euler-theorem-dc")

    a_history = await get_question_history(db, "user-a")
    b_history = await get_question_history(db, "user-b")
    assert len(a_history) == 2 and len(b_history) == 1
    assert all(h["correct"] is False for h in a_history)

    a_progress = await get_progress(db, "user-a")
    b_progress = await get_progress(db, "user-b")
    assert a_progress["questionsCorrect"] == 0
    assert b_progress["questionsCorrect"] == 1
    assert await get_mistakes(db, "user-b") == []


@pytest.mark.asyncio
async def test_weak_concept_detection_reports_observable_reason(db):
    for qid in (1, 2, 3):
        await _answer(db, "u2", qid, False, "euler-theorem-dc")
    weak = await get_weak_concepts(db, "u2")
    assert weak and weak[0]["conceptId"] == "euler-theorem-dc"
    assert weak[0]["mastery"] < 50
    assert "incorrect" in weak[0]["reason"]


@pytest.mark.asyncio
async def test_new_user_has_empty_weak_concepts_and_progress(db):
    assert await get_weak_concepts(db, "brand-new") == []
    progress = await get_progress(db, "brand-new")
    assert progress["hasHistory"] is False
    assert progress["questionsAnswered"] == 0
    plan = await get_daily_plan(db, "brand-new", "em1-btech", 30)
    assert plan["studyMinutes"] == 30


@pytest.mark.asyncio
async def test_recommendation_prefers_weak_prerequisite(db):
    for qid in (4, 5):
        await _answer(db, "u3", qid, False, "partial-derivatives-dc")
    await _answer(db, "u3", 1, False, "euler-theorem-dc")

    rec = await get_next_recommendation(db, "u3", "em1-btech")
    assert rec is not None
    assert rec["type"] in {"LEARN", "REVIEW", "PRACTICE"}
    # Never the advanced concept while its prerequisite chain is weak.
    assert rec["conceptId"] != "euler-theorem-dc"
    assert rec["conceptId"] in {"partial-derivatives-dc", "derivatives-dc"}
    assert rec["reason"]


@pytest.mark.asyncio
async def test_daily_plan_respects_study_time(db):
    for qid in (1, 2, 4):
        await _answer(db, "u4", qid, False, "euler-theorem-dc" if qid < 4 else "partial-derivatives-dc")
    plan = await get_daily_plan(db, "u4", "em1-btech", study_minutes=30)
    assert plan["plannedMinutes"] <= 30
    assert sum(b["minutes"] for b in plan["blocks"]) == plan["plannedMinutes"]
    assert plan["blocks"]


@pytest.mark.asyncio
async def test_adaptive_quiz_targets_weak_concept_and_avoids_repeats(db):
    for qid in (1, 2):
        await _answer(db, "u5", qid, False, "euler-theorem-dc")

    quiz = await build_adaptive_quiz(db, "u5", subject_id="em1-btech", question_count=3)
    assert quiz["concept_id"] in {"euler-theorem-dc", "partial-derivatives-dc"}
    assert quiz["target_difficulties"][0] == "EASY"  # low mastery → easier questions
    answered = {1, 2}
    fresh = [q["id"] for q in quiz["questions"] if q["id"] not in answered]
    assert fresh, "adaptive quiz should prefer questions the user has not just answered"
    assert quiz["questions"][0]["id"] not in answered
    assert quiz["selection_reason"]


@pytest.mark.asyncio
async def test_adaptive_quiz_for_new_user_starts_from_syllabus(db):
    quiz = await build_adaptive_quiz(db, "new-user", subject_id="em1-btech", question_count=3)
    assert quiz["questions"]
    assert quiz["mastery"] == 0.0
    assert "syllabus" in quiz["selection_reason"] or "chapter" in quiz["selection_reason"]


@pytest.mark.asyncio
async def test_adaptive_quiz_review_mode_may_repeat_questions(db):
    await _answer(db, "u6", 1, False, "euler-theorem-dc")
    quiz = await build_adaptive_quiz(db, "u6", concept_id="euler-theorem-dc",
                                     question_count=3, include_recent=True)
    assert 1 in [q["id"] for q in quiz["questions"]]


@pytest.mark.asyncio
async def test_mistake_patterns_are_descriptive(db):
    for qid in (1, 2, 3):
        await _answer(db, "u7", qid, False, "euler-theorem-dc")
    mistakes = await get_mistakes(db, "u7")
    patterns = analyze_mistake_patterns(mistakes)
    assert patterns and patterns[0]["mistakeCount"] == 3
    assert "incorrect answers" in patterns[0]["summary"]


@pytest.mark.asyncio
async def test_tutor_context_and_actions_work_without_llm(db):
    await _answer(db, "u8", 1, False, "euler-theorem-dc")
    ctx = await build_student_context(db, "u8", "em1-btech", "euler-theorem-dc")
    assert ctx["hasHistory"] is True
    assert ctx["recentMistakes"]

    assert normalize_action("test") == "TEST_ME"
    payload = await resolve_action(db, "TEST_ME", "u8", "em1-btech", "euler-theorem-dc")
    assert payload["question"] is not None
    assert payload["question"]["id"] != 1  # prefers an unseen question

    mistake_payload = await resolve_action(db, "EXPLAIN_MISTAKE", "u8", "em1-btech", "euler-theorem-dc")
    reply = fallback_action_reply("EXPLAIN_MISTAKE", mistake_payload)
    assert reply and "euler" in reply.lower()


@pytest.mark.asyncio
async def test_tutor_action_empty_state_when_no_questions(db):
    payload = await resolve_action(db, "TEST_ME", "u9", "em1-btech", "concept-with-no-questions")
    # Falls back to subject-level questions rather than inventing one.
    assert payload["question"] is None or payload["question"]["source"] == "DEMO"


@pytest.mark.asyncio
async def test_question_without_concept_is_still_recorded(db):
    result = await apply_quiz_results(
        db, "u10", "quiz-x",
        [{"question_id": None, "selected_answer": "a", "correct": True}],
        subject_id="em1-btech",
    )
    assert result["total"] == 1
    assert result["concept_performance"] == []
    assert (await get_progress(db, "u10"))["questionsAnswered"] == 1


@pytest.mark.asyncio
async def test_explain_action_is_grounded_in_stored_notes(db):
    db.add(AcademicNote(
        title="[TEST] Euler's Theorem",
        subject_id="em1-btech",
        concept_id="euler-theorem-dc",
        content="Euler's theorem relates partial derivatives of a homogeneous function to its degree.",
        summary="x fx + y fy = n f for homogeneous f of degree n.",
        key_points=["Check homogeneity first"],
        formulas=["x*fx + y*fy = n*f"],
        source="SOURCE_DERIVED",
    ))
    await db.flush()

    payload = await resolve_action(db, "EXPLAIN", "u11", "em1-btech", "euler-theorem-dc")
    assert payload["notes"], "EXPLAIN must be backed by stored notes"
    reply = fallback_action_reply("EXPLAIN", payload)
    assert "homogeneous" in reply.lower()
    assert note_sources(payload["notes"])[0]["title"] == "[TEST] Euler's Theorem"


@pytest.mark.asyncio
async def test_explain_action_admits_when_no_notes_exist(db):
    payload = await resolve_action(db, "EXPLAIN", "u12", "em1-btech", "concept-with-no-notes")
    assert payload["notes"] == []
    assert fallback_action_reply("EXPLAIN", payload) == "No stored notes cover this concept yet."


@pytest.mark.asyncio
async def test_mastery_recalculation_backfills_review_date(db):
    await _answer(db, "u13", 1, True, "euler-theorem-dc")
    row = await recalculate_concept_mastery(db, "u13", "euler-theorem-dc", subject_id="em1-btech")
    assert row.next_review_at is not None
    assert row.review_interval_days in REVIEW_INTERVALS_DAYS


@pytest.mark.asyncio
async def test_adaptive_quiz_leads_with_primary_concept(db):
    for _ in range(3):
        await _answer(db, "u14", 1, False, "euler-theorem-dc")
    quiz = await build_adaptive_quiz(db, "u14", subject_id="em1-btech", question_count=3)
    assert quiz["questions"]
    assert quiz["questions"][0]["concept_id"] == quiz["concept_id"]


@pytest.mark.asyncio
async def test_explicit_concept_without_questions_returns_honest_empty_state(db):
    quiz = await build_adaptive_quiz(
        db, "u15", subject_id="programming-btech",
        concept_id="c-basics", question_count=3,
    )
    assert quiz["questions"] == []
    assert quiz["widened_beyond_targets"] is False
    assert quiz["concept_id"] == "c-basics"
    assert "No questions are stored for C Basics" in quiz["message"]


@pytest.mark.asyncio
async def test_explicit_concept_falls_back_to_prerequisite_with_disclosure(db):
    quiz = await build_adaptive_quiz(
        db, "u17", subject_id="em1-btech",
        concept_id="total-derivatives-dc", question_count=3,
    )
    # Total Derivatives has no stored questions; its unmastered prerequisite is
    # practised instead and the swap is stated explicitly.
    assert quiz["concept_id"] == "euler-theorem-dc"
    assert "Total Derivatives" in quiz["prerequisite_note"]
    assert quiz["widened_beyond_targets"] is False


@pytest.mark.asyncio
async def test_similar_question_differs_from_test_me_question(db):
    test_me = await resolve_action(db, "TEST_ME", "u16", "em1-btech", "euler-theorem-dc")
    similar = await resolve_action(db, "SIMILAR_QUESTION", "u16", "em1-btech", "euler-theorem-dc")
    assert test_me["question"] and similar["question"]
    assert similar["question"]["id"] != test_me["question"]["id"]
