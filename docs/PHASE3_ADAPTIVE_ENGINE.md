# Phase 3 — Adaptive Learning Engine

Phase 1 (product UI) and Phase 2 (document/academic pipeline) are unchanged apart from the repairs listed in `docs/PHASE2_BASELINE_REPORT.md`. Phase 3 adds the adaptive layer on top of them.

```
answer → question→concept → concept performance → mastery update →
weakness detection → prerequisite analysis → recommendation →
adaptive quiz → new performance → repeat
```

Every value below lives in one place: `backend/app/core/adaptive_config.py`. Nothing is random; every adaptive decision is derived from stored attempts, concept metadata, question metadata, prerequisites, the review schedule and the user's study time.

## 1. Mastery algorithm — the "LexiMind Mastery Score"

`backend/app/services/mastery.py::calculate_mastery(attempts)` is pure and deterministic (no DB, no clock unless injected).

For each attempt:

```
weight = difficulty_weight(difficulty) * recency_weight(attempted_at)
recency_weight = max(RECENCY_MIN_WEIGHT, 0.5 ** (age_days / RECENCY_HALF_LIFE_DAYS))
```

```
weighted_accuracy = Σ(weight · correct) / Σ(weight)
recent_accuracy   = accuracy over the last RECENT_WINDOW (5) attempts
blended           = (1 - 0.35)·weighted_accuracy + 0.35·recent_accuracy
evidence          = min(attempts, 8) / 8
score             = 100 · (evidence·blended + (1 - evidence)·0.5)
```

The shrinkage term means one lucky answer cannot produce `MASTERED`. Worked example — 5 attempts, 4 correct, all MEDIUM, all today:

```
weighted accuracy 0.8 · evidence 5/8 + neutral prior 0.5 · 3/8 = 0.6875 → 68.8
```

Constants: `DIFFICULTY_WEIGHTS = {EASY 1.0, MEDIUM 1.25, HARD 1.5}`, `RECENCY_HALF_LIFE_DAYS = 30`, `RECENT_WINDOW = 5`, `RECENT_PERFORMANCE_WEIGHT = 0.35`, `EVIDENCE_FULL_WEIGHT_ATTEMPTS = 8`, `NEUTRAL_PRIOR = 0.5`.

This is a transparent heuristic, deliberately not presented as a validated psychometric measurement.

### Concept states

`concept_state(score, attempts)` — `NOT_STARTED` with zero attempts, otherwise `85+ MASTERED`, `70+ PROFICIENT`, `50+ DEVELOPING`, `30+ WEAK`, else `VERY_WEAK`. The frontend never re-implements the thresholds; it renders the state the backend returns and can read `GET /api/learning/config`.

## 2. Weakness detection

`backend/app/services/weakness.py::get_weak_concepts(user_id)` returns concept, subject, chapter, mastery, state, attempt counts, prerequisites, weak prerequisites and observable reasons such as *"3 of your last 5 answers on this concept were incorrect."* Signals: low mastery (≤ 50), recent incorrect answers, repeated mistakes on the same concept, and weak prerequisites. No psychological claims — only counted performance.

## 3. Prerequisite graph

`backend/app/services/concept_graph.py` reads the Phase 2 curriculum relationships and respects their confidence: `get_prerequisites`, `get_dependents`, `get_prerequisite_chain`, `is_prerequisite_mastered(mastery_map, concept_id)`. A concept is "unlocked" when its prerequisites are at or above `PREREQUISITE_MASTERY_THRESHOLD` (70). `explain_prerequisite_gap` produces the user-facing sentence, e.g. *"Euler's Theorem depends on Partial Derivatives (Partial Derivatives 54%). Work on that concept first."*

## 4. Recommendation engine

`backend/app/services/recommendations.py` — `get_recommendations`, `get_next_recommendation`, `get_daily_plan`.

Priority: weak prerequisites first, then weak concepts, then concepts due for review, then the next unlocked syllabus concept. Each recommendation carries `type` (`LEARN | REVIEW | PRACTICE | PYQ | QUIZ`), concept, reason, `estimatedMinutes` and a numeric priority. A concept never attempted is `LEARN`, never `REVIEW`.

`get_daily_plan(user_id, study_minutes)` packs those recommendations into blocks that sum to the requested study time (default 30 min).

## 5. Adaptive quiz

`backend/app/services/adaptive_quiz.py::build_adaptive_quiz`:

1. Target concepts — the explicit `concept_id` if given, else the weakest concepts, else the start of the syllabus for a new user.
2. Prerequisite check on the primary target; if a prerequisite is weak, that prerequisite is practised first and `prerequisite_note` explains why.
3. Difficulty band from mastery: `<40 → EASY/MEDIUM`, `40–70 → MEDIUM/EASY`, `70+ → MEDIUM/HARD`.
4. Candidate questions for those concepts, excluding anything answered within `REPEAT_COOLDOWN_DAYS` (7) unless `include_recent` is set or nothing else exists.
5. Deterministic ranking: unseen first, then the primary concept, then target difficulty, then authentic source (`PYQ > UPLOADED > PREMADE > DEMO > AI_GENERATED`), then id.

The response reports `selection_reason`, `prerequisite_note`, `target_difficulties`, `source_counts`, `repeated_questions` and `insufficient_bank`, so the UI can explain the choice. When the bank is empty it says so instead of inventing questions.

In-quiz control (`next_difficulty`): 3 consecutive correct → step up the ladder, 2 consecutive incorrect → step down. Both thresholds are configurable.

## 6. Mistakes

`backend/app/services/mistakes.py` — `get_question_history`, `get_mistakes`, `analyze_mistake_patterns`. Each wrong answer stores question, concept, selected answer, correct answer, difficulty and timestamp. Patterns are descriptive counts (*"4 incorrect answers on Euler's Theorem, mostly on MEDIUM questions"*), never diagnoses.

## 7. Spaced review

`backend/app/services/review.py`: intervals `1 → 3 → 7 → 14 → 30` days. Session accuracy ≥ 0.8 promotes to the next interval, < 0.5 resets to 1 day, in between repeats the current interval. `get_review_schedule(user_id)` returns each concept's interval, `nextReviewAt` and whether it is due.

## 8. Learning path

`backend/app/services/learning_path.py::build_path` returns ordered items with `COMPLETED | CURRENT | RECOMMENDED | LOCKED | NEEDS_REVIEW`, mastery, attempts, estimated minutes, next review date and a note explaining locks. It is recomputed from mastery, so it updates as soon as a quiz is submitted.

## 9. AI tutor

`backend/app/services/tutor.py` builds context from the student profile, mastery rows, weak concepts, recent mistakes, the current subject/chapter/concept and retrieved academic material, and only states what the stored performance supports.

Actions: `EXPLAIN`, `SIMPLIFY`, `EXAMPLE`, `HINT`, `TEST_ME`, `SIMILAR_QUESTION`, `EXPLAIN_MISTAKE`. Each is backed by real records — `TEST_ME` and `SIMILAR_QUESTION` select a stored question (preferring unseen ones and matching difficulty), `EXPLAIN_MISTAKE` retrieves the student's actual incorrect attempt, and the explanation actions are grounded in stored notes. Responses expose the sources they used (note title/page, question source/year). When nothing is stored the tutor says so rather than fabricating a citation.

With no provider configured (`/api/ai/status` → `configured:false`) the same actions still work through deterministic, database-only replies.

## 10. Database

Existing models were extended; no parallel tables were introduced.

`ConceptMastery` (`backend/app/models/academic.py`): `user_id`, `concept_id`, `mastery_score`, `questions_attempted`, `questions_correct`, `questions_incorrect`, `last_attempted_at`, `last_correct_at`, `streak`, `confidence`, `state`, `subject_id`, `next_review_at`, `review_interval_days`, `updated_at`.

`QuizAnswer` (the question-attempt record): `id`, `user_id`, `question_id`, `concept_id`, `quiz_id`, `selected_answer`, `correct_answer`, `correct`, `difficulty`, `time_taken`, `created_at`.

`backend/app/core/database.py` performs an in-place SQLite migration for the added columns on startup, so existing databases keep working.

## 11. API

All routes follow the existing `/api/...` convention; no duplicates were added.

```
GET  /api/learning/config
GET  /api/learning/mastery/{user_id}
GET  /api/learning/mastery/{user_id}/{concept_id}
POST /api/learning/mastery/update
GET  /api/learning/weak-concepts/{user_id}
GET  /api/learning/prerequisites/{concept_id}
GET  /api/learning/recommendations/{user_id}
GET  /api/learning/recommendations/{user_id}/next
GET  /api/learning/daily-plan/{user_id}
GET  /api/learning/review-schedule/{user_id}
GET  /api/learning/learning-path/{user_id}/{subject_id}
POST /api/learning/learning-path/regenerate
GET  /api/learning/history/{user_id}
GET  /api/learning/mistakes/{user_id}
GET  /api/learning/progress/{user_id}
POST /api/learning/quiz-attempt
POST /api/quizzes/adaptive
POST /api/quizzes/complete
GET  /api/ai/status
POST /api/ai/tutor
```

## 12. User isolation

`backend/app/core/identity.py::resolve_user_id` is the single place identity is resolved: `request.state.user_id` (for future authentication) wins, otherwise the `X-User-Id` header / explicit id, and any mismatch is rejected with 403. Every adaptive query filters on the resolved id, and document routes refuse documents owned by someone else. The frontend attaches `X-User-Id` from the stored profile on every request.

## 13. Frontend

`frontend/src/services/adaptiveEngine.ts` now calls the backend instead of returning demo constants. Dashboard, Learning Path, Progress, Quizzes, Tutor, Subjects, Chapter, Concept and Learn read real mastery, weaknesses, recommendations, plans and path states, and show honest empty states when there is no history. Static curriculum configuration (subjects/chapters/concept metadata) is unchanged.

## 14. Running it

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# optional neural retrieval
pip install -r requirements-embeddings.txt

# frontend
cd frontend
npm install
npm run dev
```

Environment variables (all optional; the app runs fully without them):

| Variable | Where | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | backend `.env` | enables the Gemini provider; without it the tutor uses the local deterministic fallback |
| `AI_PROVIDER` | backend `.env` | provider selection (default `gemini`) |
| `DATABASE_URL` | backend `.env` | defaults to SQLite `leximind.db` |
| `VITE_API_URL` | frontend `.env` | API base URL (default `http://localhost:8000/api`) |

Keys are read only on the backend and are never returned by an endpoint or shipped in the bundle.

## 15. Tests

`backend/tests/` — 63 tests, all passing (`python -m pytest`): mastery calculation and determinism, difficulty weighting, recency decay, concept states, in-quiz difficulty control, prerequisite logic, weak-concept detection, recommendations, daily plan, adaptive selection and repetition control, review scheduling, learning-path states, quiz completion persistence, mistake patterns, tutor context/actions/grounding without an LLM, user isolation, document isolation, and edge cases (new user, question without concept, no questions available, no notes available).

Frontend: `npx tsc --noEmit` (clean) and `npm run build` (clean; only a chunk-size advisory).

## 16. Verification

```
PHASE 2 VERIFIED: PASS
PHASE 3 VERIFIED: PASS
```

Evidence: 63 backend tests passing, clean typecheck and production build, and live probes of every endpoint above against a running server with the seeded demo dataset (7 concepts, 12+ questions, 15 attempts, 1 mastered concept, 1 weak concept, 2+ prerequisite relations) returning real derived values — overall mastery 56.1, accuracy 60%, Euler's Theorem 27 (`VERY_WEAK`), Partial Derivatives 53.9 (`DEVELOPING`), Limits 87.5 (`MASTERED`), and a next recommendation of *review Partial Derivatives* because Euler's Theorem depends on it.

## 17. Remaining limitations

- No authentication layer exists yet; identity comes from the client header and cross-user access is rejected, but a determined caller can still claim another id. Wire real auth into `request.state.user_id`.
- The Gemini path could not be exercised — no API key is provisioned in this environment. The local fallback path is fully tested.
- Demo academic content is clearly prefixed `[DEMO]`; real coverage depends on uploaded documents.
- Mastery/recommendations are computed per request against SQLite. That is fine at the current scale; a cache would be needed for large classes.
