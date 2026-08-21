# Requirements Document

## Introduction

LexiMind AI Phase 3 adds an Adaptive Learning Intelligence system on top of the existing Phase 1 student-facing UI and Phase 2 academic document pipeline. The system continuously personalises each student's learning experience by tracking concept mastery, detecting weaknesses, analysing prerequisite readiness, recommending next actions, and adapting quiz difficulty in real time. Phase 3 extends — never replaces — the existing document pipeline, quiz bank, mastery store, AI Tutor, and learning path already present in Phase 2. A mandatory Phase 2 audit and repair step gates entry to all Phase 3 work.

The adaptive loop is: Student answers question → question mapped to concept → concept performance updated → mastery recalculated → weaknesses detected → prerequisites checked → next action recommended → adaptive quiz assembled → new performance recorded → loop repeats.

---

## Glossary

- **Adaptive_Engine**: The Phase 3 service layer that orchestrates mastery, recommendations, and adaptive quiz assembly.
- **Concept_Mastery**: Per-user, per-concept record holding the LexiMind Mastery Score and supporting metrics.
- **LexiMind_Mastery_Score**: A 0–100 transparent deterministic score computed by `calculate_mastery()` combining accuracy, recency-weighted performance, and difficulty adjustment.
- **Mastery_State**: One of NOT_STARTED, VERY_WEAK, WEAK, DEVELOPING, PROFICIENT, or MASTERED, derived from the LexiMind Mastery Score against configurable thresholds.
- **Question_Attempt**: A single student answer record storing question, concept, selected answer, correctness, difficulty, time taken, and timestamp.
- **Adaptive_Quiz**: A quiz assembled by the Adaptive_Engine that targets weak concepts, respects prerequisites, avoids recently seen questions, and adjusts difficulty dynamically.
- **Prerequisite_Graph**: The directed acyclic graph of concept dependency relationships sourced from the Phase 2 curriculum and extracted concepts.
- **Recommendation**: A structured suggestion produced by `get_next_recommendation()` containing concept, reason, estimated study time, priority, and type (LEARN, REVIEW, PRACTICE, PYQ, or QUIZ).
- **Review_Schedule**: Per-user, per-concept spaced-repetition schedule with a `next_review_at` timestamp and an interval that grows with improving mastery.
- **Daily_Study_Plan**: A time-boxed list of recommended activities for the current day produced by the Adaptive_Engine from the review schedule, weak concepts, and learning path position.
- **Phase_2_Baseline_Report**: A written audit report confirming that all Phase 2 components pass their verification checks before any Phase 3 work begins.
- **Difficulty_Weight**: A configurable numeric multiplier applied per difficulty level when calculating mastery (EASY=1.0, MEDIUM=1.25, HARD=1.5).
- **Audit_Checklist**: The mandatory list of Phase 2 checks that must all pass before Phase 3 implementation starts.
- **AI_Tutor**: The existing `/api/chat` endpoint upgraded to accept student profile, mastery state, and retrieved academic context.
- **User_Isolation**: The guarantee that mastery, attempts, recommendations, and review schedules for User A are never visible to User B.

---

## Requirements

---

### Requirement 1: Phase 2 Audit and Baseline Verification

**User Story:** As a development team, we need to verify that all Phase 2 components work correctly before Phase 3 is built, so that Phase 3 is not layered on a broken foundation.

#### Acceptance Criteria

1. WHEN the audit begins, THE Audit_Checklist SHALL verify that the backend starts without import errors or runtime exceptions.
2. WHEN the audit begins, THE Audit_Checklist SHALL verify that the frontend builds and loads without console errors.
3. WHEN a PDF is uploaded, THE Document_Pipeline SHALL extract text, classify the document, chunk it, extract concepts, and set status to READY or NEEDS_REVIEW within 60 seconds for files under 5 MB.
4. WHEN a PYQ document is processed, THE Document_Pipeline SHALL retain the original source label PYQ on all extracted questions and SHALL NOT fabricate year values not present in the source document.
5. WHEN the quiz system is tested, THE Quiz_System SHALL load questions from the database, accept a submission, persist scores, and return a scored result without a 500 error.
6. WHEN the AI Tutor is loaded, THE AI_Tutor SHALL load without crashing regardless of whether an LLM API key is configured.
7. WHEN a provider key is absent, THE AI_Tutor SHALL return a fallback response that does not expose any environment variable values or key names.
8. THE Audit_Checklist SHALL verify that the `.env` file is listed in `.gitignore` and that no API key values appear in committed source files.
9. IF any Audit_Checklist item fails, THEN THE Adaptive_Engine implementation SHALL NOT begin until that item is fixed and re-verified.
10. WHEN all checks pass, THE Phase_2_Baseline_Report SHALL be produced recording the result of each check, the git commit hash at the time of audit, and a PHASE 2 VERIFIED: PASS declaration.

---

### Requirement 2: Concept Mastery Data Model

**User Story:** As a student, I want the system to remember my performance on every concept, so that it can personalise my study plan based on real history.

#### Acceptance Criteria

1. THE Concept_Mastery record SHALL store: `user_id`, `concept_id`, `mastery_score` (Float 0.0–100.0), `questions_attempted` (Integer ≥ 0), `questions_correct` (Integer ≥ 0), `questions_incorrect` (Integer ≥ 0), `last_attempted_at` (DateTime nullable), `last_correct_at` (DateTime nullable), `streak` (Integer, consecutive correct answers), `confidence` (Float 0.0–1.0), `state` (String enum), `next_review_at` (DateTime nullable), `updated_at` (DateTime).
2. THE Concept_Mastery table SHALL enforce a unique constraint on (`user_id`, `concept_id`) so that each student has exactly one mastery record per concept.
3. WHEN a new student answers their first question for a concept, THE Adaptive_Engine SHALL create a Concept_Mastery record with `questions_attempted` = 1 and compute the initial LexiMind_Mastery_Score.
4. THE Question_Attempt table SHALL store: `id`, `user_id`, `question_id`, `concept_id`, `quiz_id`, `selected_answer`, `correct` (Boolean), `difficulty` (String), `time_taken` (Float seconds, nullable), `created_at` (DateTime).
5. THE Question_Attempt table SHALL NOT duplicate the existing `QuizAnswer` table; IF `QuizAnswer` already captures the required fields, THEN THE Adaptive_Engine SHALL extend or reuse it rather than create a parallel table.
6. WHEN the database is initialised, THE Database_Migration SHALL create all Phase 3 tables and columns without dropping or altering Phase 2 tables.

---

### Requirement 3: LexiMind Mastery Score Algorithm

**User Story:** As a student, I want my mastery score to reflect my actual performance including how recent it is and how hard the questions were, so that the score is a fair and transparent measure of my understanding.

#### Acceptance Criteria

1. THE `calculate_mastery()` function SHALL accept: `questions_correct` (int), `questions_attempted` (int), `difficulty_weighted_correct` (float), `difficulty_weighted_attempted` (float), `recency_score` (float 0.0–1.0), and return a `mastery_score` between 0.0 and 100.0.
2. THE `calculate_mastery()` function SHALL be defined in a single dedicated service module and SHALL NOT be duplicated in route handlers or other service files.
3. WHEN `questions_attempted` is 0, THE `calculate_mastery()` function SHALL return `mastery_score` = 0.0, `state` = NOT_STARTED.
4. THE difficulty adjustment SHALL apply configurable weights: EASY = 1.0, MEDIUM = 1.25, HARD = 1.5 read from a single configuration object, not hardcoded in multiple files.
5. THE recency mechanism SHALL assign higher weight to answers in the most recent N attempts (default N = 10) using an exponential decay formula where the most recent attempt has weight 1.0 and each earlier attempt has weight multiplied by a configurable decay factor (default 0.85).
6. THE recency mechanism, decay factor, and N value SHALL be documented in an inline docstring within the `calculate_mastery()` function explaining the formula and rationale.
7. WHEN `mastery_score` is in [0, 29], THE Adaptive_Engine SHALL assign state NOT_STARTED (0 attempts) or VERY_WEAK (≥1 attempt).
8. WHEN `mastery_score` is in [30, 49], THE Adaptive_Engine SHALL assign state WEAK.
9. WHEN `mastery_score` is in [50, 69], THE Adaptive_Engine SHALL assign state DEVELOPING.
10. WHEN `mastery_score` is in [70, 84], THE Adaptive_Engine SHALL assign state PROFICIENT.
11. WHEN `mastery_score` is in [85, 100], THE Adaptive_Engine SHALL assign state MASTERED.
12. THE state thresholds SHALL be stored in a single configurable constants object so they can be adjusted without modifying the algorithm logic.
13. FOR ALL inputs where `questions_correct` ≤ `questions_attempted`, the `calculate_mastery()` function SHALL return `mastery_score` in [0.0, 100.0] (invariant).
14. FOR ALL identical inputs, the `calculate_mastery()` function SHALL return identical outputs (deterministic invariant — no random elements).

---

### Requirement 4: Weak Concept Detection

**User Story:** As a student, I want the system to identify which concepts I am struggling with, so that I can focus my study time where it is most needed.

#### Acceptance Criteria

1. THE `get_weak_concepts(user_id)` function SHALL query the Concept_Mastery table and return a list of concepts where `mastery_score` < 60 or `state` in {VERY_WEAK, WEAK, DEVELOPING}.
2. WHEN returning weak concepts, THE `get_weak_concepts()` function SHALL include for each result: `concept_id`, `concept_name`, `subject_id`, `chapter_id`, `mastery_score`, `state`, and `reason` (a human-readable string explaining why the concept is flagged).
3. THE `reason` field SHALL be derived from observable data only: low mastery score, recent incorrect streak, prerequisite weakness, or no recent practice.
4. THE `reason` field SHALL NOT contain unsupported psychological claims or speculation about student ability beyond what the data shows.
5. WHEN a concept has 3 or more consecutive incorrect answers in the most recent attempts, THE `get_weak_concepts()` function SHALL include it regardless of overall mastery score.
6. WHEN a prerequisite concept for a target concept has `mastery_score` < 60, THE `get_weak_concepts()` function SHALL include the prerequisite concept in the results and set `reason` to indicate it is a prerequisite dependency.
7. THE `GET /api/learning/weak-concepts/{user_id}` endpoint SHALL call `get_weak_concepts()` and return the list ordered by ascending `mastery_score` (weakest first).
8. WHEN a user has no Concept_Mastery records, THE `get_weak_concepts()` function SHALL return an empty list without raising an exception.

---

### Requirement 5: Prerequisite Graph and Awareness

**User Story:** As a student, I want the system to understand which concepts depend on others, so that it does not push me to advanced material before I am ready.

#### Acceptance Criteria

1. THE Prerequisite_Graph SHALL be built from the `prerequisites` list on each concept in the curriculum (Phase 2 `CONCEPTS` in `education.py`) and from any prerequisite relationships stored in the database.
2. THE `get_prerequisites(concept_id)` function SHALL return all direct prerequisite concept IDs for the given concept, or an empty list if none are defined.
3. THE `get_dependents(concept_id)` function SHALL return all concept IDs that directly depend on the given concept.
4. THE `is_prerequisite_mastered(user_id, concept_id)` function SHALL return True only when all direct prerequisites of `concept_id` have `mastery_score` ≥ 60 for the given user.
5. WHEN `is_prerequisite_mastered()` returns False for a concept, THE Recommendation_Engine SHALL NOT recommend that concept as the next learning target unless all higher-priority options are exhausted.
6. WHEN a prerequisite is not mastered and a recommendation would skip it, THE Recommendation_Engine SHALL produce a `reason` string in the form: "[Advanced concept] depends on [Prerequisite]. Your current mastery suggests reviewing [Prerequisite] first."
7. THE `GET /api/education/concepts/{concept_id}` response SHALL include a `prerequisites` field listing direct prerequisite IDs and a `dependents` field listing direct dependent IDs.

---

### Requirement 6: Recommendation Engine

**User Story:** As a student, I want to receive a personalised next-step recommendation after each quiz or study session, so that I always know what to work on next without having to guess.

#### Acceptance Criteria

1. THE `get_next_recommendation(user_id)` function SHALL return a single Recommendation object containing: `concept_id`, `concept_name`, `reason` (string), `estimated_minutes` (int), `priority` (int 1–5, where 1 is highest), and `type` (one of LEARN, REVIEW, PRACTICE, PYQ, QUIZ).
2. THE Recommendation_Engine SHALL prioritise concepts in this order: (1) overdue spaced reviews, (2) weak prerequisites blocking progress, (3) weak concepts in the current subject, (4) the next concept in the learning path, (5) a new concept to learn.
3. WHEN computing priority, THE Recommendation_Engine SHALL consider: weakness score, prerequisite readiness, time since last attempt, and position in the learning path order.
4. WHEN a recommended concept has type REVIEW, the `reason` SHALL state the last attempt date and the current mastery score.
5. THE `GET /api/learning/recommended/{user_id}` endpoint SHALL call `get_next_recommendation()` and return the Recommendation object.
6. THE `GET /api/learning/recommended/{user_id}` endpoint SHALL accept an optional `subject_id` query parameter to scope recommendations to a single subject.
7. WHEN no Concept_Mastery data exists for a user, THE `get_next_recommendation()` function SHALL return a recommendation of type LEARN pointing to the first concept in the default subject's learning path.
8. THE Recommendation_Engine SHALL NOT recommend a concept that is already in state MASTERED unless it is overdue for spaced review.

---

### Requirement 7: Adaptive Quiz Assembly

**User Story:** As a student, I want quizzes to be assembled based on my weak areas and adjusted to an appropriate difficulty, so that each quiz challenges me at the right level without being frustrating or too easy.

#### Acceptance Criteria

1. THE `POST /api/quizzes/adaptive` endpoint SHALL accept: `user_id`, `subject_id`, optional `chapter_id`, optional `concept_id`, and `question_count` (default 10, maximum 30).
2. WHEN assembling an Adaptive_Quiz, THE Adaptive_Engine SHALL query weak concepts for the user, check prerequisites, retrieve candidate questions from the question bank, and order by suitability before selecting `question_count` questions.
3. WHEN a student's `mastery_score` for a concept is below 40, THE Adaptive_Engine SHALL prefer EASY and lower-difficulty MEDIUM questions for that concept.
4. WHEN a student's `mastery_score` for a concept is in [40, 70), THE Adaptive_Engine SHALL prefer MEDIUM difficulty questions for that concept.
5. WHEN a student's `mastery_score` for a concept is 70 or above, THE Adaptive_Engine SHALL prefer MEDIUM and HARD questions for that concept.
6. WHEN a student answers 3 consecutive questions correctly during an adaptive quiz session, THE Adaptive_Engine SHALL increase the difficulty tier for subsequent questions in that session.
7. WHEN a student answers 2 consecutive questions incorrectly during an adaptive quiz session, THE Adaptive_Engine SHALL decrease the difficulty tier for subsequent questions in that session.
8. THE consecutive correct/incorrect thresholds for difficulty adjustment (3 correct, 2 incorrect) SHALL be stored in a single configurable constants object.
9. THE Adaptive_Engine SHALL NOT select a question that the user has already seen in the same quiz session.
10. THE Adaptive_Engine SHALL deprioritise questions attempted by the user within the last 7 days unless no other questions are available for the required concept and difficulty.
11. WHEN the question bank has fewer questions than `question_count` for the requested criteria, THE Adaptive_Engine SHALL fill remaining slots from lower-priority questions rather than fail, and SHALL include `insufficient_bank: true` in the response.
12. WHEN no LLM provider is configured, THE Adaptive_Quiz assembly SHALL still work entirely from the database without requiring AI generation.

---

### Requirement 8: Question Attempt Tracking and Repetition Avoidance

**User Story:** As a student, I want the system to remember which questions I have already answered, so that I am not shown the same question repeatedly unless I request a review.

#### Acceptance Criteria

1. WHEN a quiz is submitted, THE Adaptive_Engine SHALL record a Question_Attempt for every answered question, storing `user_id`, `question_id`, `concept_id`, `quiz_id`, `selected_answer`, `correct`, `difficulty`, `time_taken`, and `created_at`.
2. THE `get_question_history(user_id)` function SHALL return all Question_Attempt records for a user, ordered by `created_at` descending.
3. WHEN assembling an Adaptive_Quiz, THE Adaptive_Engine SHALL retrieve the user's question history and assign a recency penalty to questions attempted within the last 7 days.
4. THE `GET /api/quiz/history` endpoint SHALL accept `user_id` as a query parameter and return the question history with concept and subject context.
5. WHEN `review_requested` is set to True in the adaptive quiz request, THE Adaptive_Engine SHALL allow recently seen questions to be re-selected for the concept being reviewed.
6. WHEN a question has no `question_id` (AI-generated questions without a DB row), THE Adaptive_Engine SHALL skip attempt tracking for that question without raising an exception.

---

### Requirement 9: Mistake Analysis and Patterns

**User Story:** As a student, I want to understand the patterns in my mistakes, so that I can identify and address systematic gaps in my understanding.

#### Acceptance Criteria

1. WHEN a student answers a question incorrectly, THE Adaptive_Engine SHALL store the mistake with: `question_id`, `concept_id`, `selected_answer`, `correct_answer`, `difficulty`, and `created_at`.
2. THE `GET /api/mistakes` endpoint SHALL accept `user_id` and optional `concept_id` query parameters and return all stored mistake records for that user, ordered by `created_at` descending.
3. WHEN a concept has 3 or more mistakes recorded, THE Adaptive_Engine SHALL compute a `pattern_summary` string describing the observable pattern (e.g., "Repeated incorrect answers on HARD questions for Euler's Theorem").
4. THE `pattern_summary` SHALL be derived from measurable fields (concept, difficulty, frequency, answer type) and SHALL NOT contain unsupported claims about learning disabilities or psychological states.
5. WHEN a question has an `explanation` field populated, THE Adaptive_Engine SHALL include the explanation in the mistake record returned by `GET /api/mistakes`.
6. WHEN a question has no explanation and an LLM provider is configured, THE Adaptive_Engine SHALL optionally generate an explanation grounded in the question text and correct answer and mark it as `explanation_source: AI_GENERATED`.
7. WHEN no LLM provider is configured, THE Adaptive_Engine SHALL return the mistake record without an AI-generated explanation and SHALL NOT raise an exception.

---

### Requirement 10: Spaced Review Scheduling

**User Story:** As a student, I want to be reminded to review concepts at increasing intervals as my mastery improves, so that I retain knowledge without over-studying already-mastered concepts.

#### Acceptance Criteria

1. THE Review_Schedule SHALL store per-user, per-concept: `next_review_at` (DateTime), `current_interval_days` (Int), and `review_count` (Int).
2. WHEN a concept reaches PROFICIENT state for the first time, THE Adaptive_Engine SHALL schedule the first review with `current_interval_days` = 1.
3. THE review interval progression SHALL follow: 1 day, 3 days, 7 days, 14 days, 30 days. After 30 days the interval SHALL remain 30 days unless mastery drops.
4. WHEN a student successfully completes a review (mastery maintained or improved), THE Adaptive_Engine SHALL advance `current_interval_days` to the next value in the progression.
5. WHEN a student's mastery drops below their previous state after a review, THE Adaptive_Engine SHALL reset `current_interval_days` to 1 day.
6. THE `GET /api/learning/review-schedule` endpoint SHALL accept `user_id` as a query parameter and return all concepts with `next_review_at` in the past, ordered by `next_review_at` ascending (most overdue first).
7. WHEN a concept is overdue for review, THE Recommendation_Engine SHALL assign it priority 1 (highest) in the recommendation ranking.

---

### Requirement 11: Learning Path Integration

**User Story:** As a student, I want my learning path to reflect my real mastery and the adaptive engine's recommendations, so that the path shown in the UI is always current and accurate.

#### Acceptance Criteria

1. THE `GET /api/learning/learning-path/{user_id}/{subject_id}` endpoint SHALL integrate with Concept_Mastery data to assign each learning path item one of: COMPLETED (mastery ≥ 85), CURRENT (current focus item), RECOMMENDED (next unlocked), LOCKED (prerequisite not mastered), or NEEDS_REVIEW (overdue spaced review).
2. WHEN a quiz is submitted and mastery is updated, THE Learning_Path state for affected concepts SHALL be recalculated and returned on the next `GET /api/learning/learning-path` call without requiring a manual refresh.
3. WHEN a concept transitions to MASTERED state, THE Learning_Path SHALL automatically unlock the next concept in the chapter order if its prerequisites are now satisfied.
4. THE learning path response SHALL include `currentConcept`, `completedConcepts`, `weakConcepts`, and `recommendedConcepts` fields consistent with the existing Phase 2 response shape.
5. THE Learning_Path calculation SHALL reuse the existing `build_learning_path()` function in `mastery.py` rather than replacing it with a parallel implementation.

---

### Requirement 12: Dashboard Personalisation

**User Story:** As a student, I want the Dashboard to show my real progress and today's plan based on my actual performance, so that the information displayed is accurate and motivating.

#### Acceptance Criteria

1. THE Dashboard SHALL display a "Continue Learning" section that shows the concept returned by `get_next_recommendation()` for the current user.
2. THE Dashboard SHALL display a "Today's Plan" section listing up to 3 activities from the Daily_Study_Plan for the current user.
3. THE Daily_Study_Plan SHALL be constructed from: overdue spaced reviews (assigned 10 minutes each), weak concept practice (assigned 10 minutes each), and next-concept learning (assigned remaining time up to the user's study goal, default 30 minutes).
4. THE Dashboard SHALL display a "Weak Areas" section populated from `get_weak_concepts()` showing at most 3 entries with concept name, mastery score, and reason.
5. THE Dashboard SHALL display actual `mastery_score` values from the Concept_Mastery table, not hardcoded placeholder values.
6. WHEN a user has no Concept_Mastery data, THE Dashboard SHALL display an empty state message: "Complete your first quiz to see your personalised dashboard" rather than showing zero values.
7. THE `GET /api/learning/progress/{user_id}` endpoint SHALL return: `totalConcepts`, `masteredConcepts`, `inProgressConcepts`, `needsReviewConcepts`, `totalQuizAttempts`, `totalQuestionsAnswered`, `overallAccuracy`, `studyStreakDays`, `subjectMastery` (array), and `recentPerformance` (last 5 quiz sessions).

---

### Requirement 13: Progress Page

**User Story:** As a student, I want a dedicated Progress page that shows my full learning history and performance metrics, so that I can track my improvement over time.

#### Acceptance Criteria

1. THE Progress_Page SHALL display: overall mastery score (average across all concepts attempted), subject-level mastery breakdown, concept-level mastery list, total quiz attempts, total questions answered, overall accuracy percentage, study streak in days, weak concepts count, and mastered concepts count.
2. ALL metrics on the Progress_Page SHALL be computed from real database values fetched from `GET /api/learning/progress/{user_id}`.
3. WHEN a chart displays performance data, THE chart data SHALL come from the API response and SHALL NOT use hardcoded seed data.
4. WHEN a user has fewer than 2 quiz attempts, THE Progress_Page SHALL display an honest empty state: "Not enough data yet. Complete more quizzes to see your progress charts."
5. THE Progress_Page SHALL display a "Recent Performance" section showing the last 5 quiz sessions with date, subject, score, and accuracy.
6. THE Progress_Page SHALL display a "Weak Concepts" section populated from `GET /api/learning/weak-concepts/{user_id}` with concept name, mastery score, and suggested action.

---

### Requirement 14: AI Tutor Personalisation and Source Grounding

**User Story:** As a student, I want the AI Tutor to know my current learning context and mastery state, so that its explanations are tailored to my needs and grounded in real academic material.

#### Acceptance Criteria

1. WHEN a tutor message is sent, THE AI_Tutor SHALL accept in its request body: `subject_id`, `concept_id`, `education_level`, `course`, `action`, and a `student_context` object containing `mastery_score`, `mastery_state`, `weak_concepts` (list), and `recent_mistakes` (list).
2. THE AI_Tutor system prompt SHALL incorporate the student's mastery state and weak concepts to tailor the explanation level.
3. WHEN `mastery_state` is VERY_WEAK or WEAK for the queried concept, THE AI_Tutor system prompt SHALL include an instruction to explain the topic from first principles.
4. WHEN `mastery_state` is PROFICIENT or MASTERED, THE AI_Tutor system prompt SHALL include an instruction to focus on advanced applications and exam-style questions.
5. THE AI_Tutor SHALL support these named actions: EXPLAIN, SIMPLIFY, EXAMPLE, HINT, TEST_ME, SIMILAR_QUESTION, EXPLAIN_MISTAKE.
6. WHEN action is EXPLAIN_MISTAKE and `recent_mistakes` is non-empty, THE AI_Tutor SHALL ground the explanation in the specific wrong answer and correct answer from the mistake record.
7. WHEN action is SIMILAR_QUESTION, THE AI_Tutor SHALL retrieve PYQs or questions from the database for the current concept and present one grounded in real source material.
8. WHEN the AI_Tutor response references a document, note, or PYQ, THE response SHALL include a `sources` field containing: `document_name`, `page_number` (if available), and `year` (if PYQ).
9. THE AI_Tutor SHALL NEVER fabricate document names, page numbers, PYQ years, or marks values not present in the retrieved academic context.
10. WHEN no LLM provider is configured, THE AI_Tutor SHALL return a fallback response assembled from retrieved academic context without claiming it is AI-generated.
11. THE existing `/api/chat` endpoint SHALL be extended, NOT replaced, to support the personalised student context fields.

---

### Requirement 15: API Endpoint Design

**User Story:** As a frontend developer, I want a clean, non-duplicated set of API endpoints that expose all adaptive learning capabilities, so that the UI can be built without inconsistency or confusion.

#### Acceptance Criteria

1. THE Adaptive_Engine SHALL expose the following endpoints, each returning JSON:
   - `GET /api/learning/mastery/{user_id}` — all mastery records for a user
   - `GET /api/learning/mastery/{user_id}/{concept_id}` — single concept mastery
   - `GET /api/learning/recommended/{user_id}` — next recommendation
   - `GET /api/learning/weak-concepts/{user_id}` — weak concept list
   - `GET /api/learning/learning-path/{user_id}/{subject_id}` — learning path
   - `GET /api/learning/review-schedule` with `user_id` query param — overdue reviews
   - `POST /api/quizzes/adaptive` — adaptive quiz assembly
   - `GET /api/quiz/history` with `user_id` query param — question attempt history
   - `GET /api/learning/mistakes` with `user_id` query param — mistake records
   - `GET /api/learning/progress/{user_id}` — full progress summary
   - `POST /api/chat` (extended) — personalised AI Tutor
2. IF an equivalent endpoint already exists in Phase 2, THE Adaptive_Engine SHALL extend it rather than create a duplicate route.
3. ALL endpoints that return per-user data SHALL require `user_id` as a path parameter or validated query parameter.
4. ALL endpoints SHALL return a 200 response with an empty array or empty object when no data exists for the user, and SHALL NOT return 404 for a valid user with no data.
5. ALL endpoints SHALL return a 422 response with a descriptive error message when required parameters are missing or malformed.

---

### Requirement 16: User Data Isolation

**User Story:** As a student, I want my mastery, quiz history, and recommendations to be completely private, so that no other student can see or influence my data.

#### Acceptance Criteria

1. THE Concept_Mastery table SHALL enforce that all queries are scoped by `user_id`; no query SHALL return data for a user other than the one specified.
2. THE Question_Attempt table SHALL enforce `user_id` scoping on all read queries.
3. THE Recommendation and Review_Schedule records SHALL be scoped by `user_id`.
4. WHEN `user_id` is supplied as a query parameter, THE backend SHALL treat it as the authoritative filter and SHALL NOT return records for any other user.
5. THE `GET /api/learning/mastery/{user_id}` endpoint SHALL return only the records where `user_id` matches the path parameter, never a cross-user join.
6. IF the application adds authentication in future, THE User_Isolation mechanism SHALL be compatible with token-based user identification without requiring a database schema change.

---

### Requirement 17: AI Provider Reliability and Fallback

**User Story:** As a student, I want all core learning features to work even when the AI provider is unavailable, so that my study session is never blocked by an external API failure.

#### Acceptance Criteria

1. WHEN the configured LLM provider returns an error or times out, THE Adaptive_Engine SHALL log the error and fall back to database-only operation for quiz generation, mastery calculation, recommendations, and progress display.
2. THE `provider_status()` function from Phase 2 SHALL remain the single source of truth for LLM availability checks.
3. WHEN AI provider is unavailable, THE adaptive quiz assembly SHALL select questions from the database using the deterministic difficulty and recency rules without calling any LLM.
4. WHEN AI provider is unavailable, THE recommendations SHALL still be generated using the rule-based Recommendation_Engine without requiring LLM output.
5. WHEN AI provider is unavailable and an explanation is requested for a mistake, THE AI_Tutor SHALL return the question text and correct answer as the explanation with an `explanation_source: FALLBACK` flag.
6. THE existing LLM provider abstraction in `services/llm.py` SHALL be reused; Phase 3 SHALL NOT introduce a parallel provider abstraction.

---

### Requirement 18: Performance and Query Efficiency

**User Story:** As a student, I want dashboard and quiz pages to load quickly, so that the adaptive features do not create noticeable delays compared to Phase 2.

#### Acceptance Criteria

1. THE `get_weak_concepts()` function SHALL use a single database query with JOINs rather than issuing one query per concept (N+1 avoidance).
2. THE `build_learning_path()` function SHALL batch-load all required Concept_Mastery records for a user in a single query rather than querying per concept.
3. THE `POST /api/quizzes/adaptive` endpoint SHALL respond within 3 seconds for a 10-question adaptive quiz when the database contains fewer than 1000 questions.
4. THE `GET /api/learning/progress/{user_id}` endpoint SHALL use aggregate database queries (COUNT, AVG) rather than loading all records into Python memory for counting.
5. THE Adaptive_Engine SHALL NOT introduce any external caching infrastructure (no Redis, Memcached, or external cache servers). Simple in-process request-level caching with `functools.lru_cache` or similar is acceptable for read-only curriculum data.

---

### Requirement 19: Demo and Seed Data for Testing

**User Story:** As a developer, I want a minimum viable seed data set so that the adaptive features can be exercised end-to-end in a fresh environment, so that testing does not require manual data entry.

#### Acceptance Criteria

1. THE seed data SHALL include at least 3 concepts with prerequisite relationships, at least 10 questions spanning at least 2 difficulty levels, at least 1 concept with an artificial mastery record in WEAK state, and at least 1 concept with a mastery record in MASTERED state.
2. THE seed data SHALL be loaded by the existing `demo_seed.py` mechanism during `init_db()` and SHALL NOT run if seed data already exists.
3. WHEN the seed is loaded, THE system SHALL support a complete end-to-end test of the adaptive loop: concept mastery lookup → quiz assembly → answer submission → mastery update → recommendation generation.
4. THE seed questions SHALL include `concept_id`, `difficulty`, and `source` fields so that the adaptive engine can filter and weight them correctly.

---

### Requirement 20: Automated Tests

**User Story:** As a developer, I want automated tests for the adaptive engine's core algorithms, so that mastery calculations, recommendations, and quiz assembly can be verified to be correct and deterministic.

#### Acceptance Criteria

1. THE test suite SHALL include deterministic unit tests for `calculate_mastery()` covering: zero attempts, all-correct, all-incorrect, mixed with difficulty weights, and mixed with recency decay.
2. THE test suite SHALL include unit tests for concept state thresholds verifying that each score boundary (29/30, 49/50, 69/70, 84/85) maps to the correct state.
3. THE test suite SHALL include unit tests for `get_weak_concepts()` verifying: empty input returns empty list, concepts below threshold are returned, concepts above threshold are not returned, and the function does not raise when called for a user with no data.
4. THE test suite SHALL include unit tests for `is_prerequisite_mastered()` verifying: concept with no prerequisites returns True, concept with all prerequisites mastered returns True, concept with one unmastered prerequisite returns False.
5. THE test suite SHALL include unit tests for adaptive question selection verifying: recently attempted questions are deprioritised, difficulty targeting matches mastery score ranges, and insufficient bank returns `insufficient_bank: true` rather than raising.
6. THE test suite SHALL include unit tests for review interval progression verifying the sequence 1 → 3 → 7 → 14 → 30 and that a mastery drop resets the interval to 1.
7. ALL unit tests SHALL be deterministic: no random seeds, no external API calls, no database state dependencies between test cases.
8. THE test files SHALL be placed in a `backend/tests/` directory and SHALL be runnable with `pytest` without additional configuration.

---

### Requirement 21: Complete End-to-End User Journey

**User Story:** As a student, I want a complete, unbroken journey from the Dashboard through studying, taking an adaptive quiz, reviewing mistakes, and receiving the next recommendation, so that every step connects logically to the next.

#### Acceptance Criteria

1. WHEN a user opens the Dashboard, THE system SHALL display their current learning path position, today's plan, and weak areas based on real database state.
2. WHEN a user navigates to a concept and takes an adaptive quiz, THE quiz SHALL be assembled by the Adaptive_Engine with questions appropriate to their mastery level.
3. WHEN a user submits the adaptive quiz, THE system SHALL: persist all Question_Attempt records, recalculate mastery for each concept answered, update the Learning_Path states, generate a new recommendation, and schedule any new spaced reviews.
4. WHEN the quiz results are displayed, THE system SHALL show: score, per-question correctness, explanations where available, and a "Next Recommended" call-to-action pointing to the concept returned by `get_next_recommendation()`.
5. WHEN a user asks the AI Tutor about a concept after a quiz, THE AI_Tutor SHALL have access to the student's mastery state and recent mistakes for that concept and SHALL reflect this in its response.
6. THE end-to-end journey SHALL complete without any 500 errors, uncaught exceptions, or blank screen states when all Phase 2 checks pass.

---

### Requirement 22: Edge Case Handling

**User Story:** As a developer, I want all edge cases handled gracefully, so that the system never crashes or displays misleading information due to missing or unusual data.

#### Acceptance Criteria

1. WHEN a new user with no quiz history opens the system, THE system SHALL display useful empty states rather than errors or zero values without explanation.
2. WHEN a concept has no questions in the question bank, THE `POST /api/quizzes/adaptive` endpoint SHALL return `{"questions": [], "insufficient_bank": true, "reason": "No questions available for this concept"}` with HTTP 200.
3. WHEN a concept has no prerequisites defined, THE `is_prerequisite_mastered()` function SHALL return True.
4. WHEN a question has no `explanation` field, THE mistake record SHALL return `explanation: null` rather than raising a NullPointerError.
5. WHEN all concepts for a subject are in MASTERED state, THE Recommendation_Engine SHALL recommend a review of the concept with the oldest `last_attempted_at` date.
6. WHEN a user has answered many questions incorrectly for every concept, THE Recommendation_Engine SHALL still return a valid recommendation pointing to the concept with the highest mastery score (least weak) as the entry point.
7. WHEN the database is unavailable, THE API endpoints SHALL return HTTP 503 with a human-readable error message rather than an unhandled 500 exception.
8. WHEN `question_count` is requested as 0 or negative, THE `POST /api/quizzes/adaptive` endpoint SHALL clamp the value to 1 and return 1 question rather than raising a validation error.
9. WHEN a student's streak counter is NULL in the database, THE `calculate_mastery()` function SHALL treat it as 0 and proceed without raising.
