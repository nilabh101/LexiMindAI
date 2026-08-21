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
2. WHEN the audit begins, THE Audit_Checklist SHALL verify that the frontend builds and loads without error-level console messages (warnings are permitted).
3. WHEN a PDF is uploaded, THE Document_Pipeline SHALL extract text, classify the document, chunk it, extract concepts, and set status to READY when classification confidence meets the configured threshold, or NEEDS_REVIEW otherwise, within 60 seconds for files under 5 MB.
4. WHEN a PYQ document is processed, THE Document_Pipeline SHALL retain the original source label PYQ on all extracted questions and SHALL NOT fabricate year values not present in the source document.
5. WHEN the quiz system is tested, THE Quiz_System SHALL load questions from the database, accept a submission, persist scores, and return an HTTP 2xx response containing a non-null score value.
6. WHEN the AI Tutor is loaded, THE AI_Tutor SHALL return an HTTP 2xx response from its status-check endpoint regardless of whether an LLM API key is configured.
7. WHEN a provider key is absent, THE AI_Tutor SHALL return a non-empty fallback message that does not expose any environment variable values or key names.
8. THE Audit_Checklist SHALL verify that the `.env` file is listed in `.gitignore` and that no API key values appear in any file tracked by git in the repository.
9. IF any Audit_Checklist item fails, THEN THE Adaptive_Engine implementation SHALL NOT begin until that item is fixed and re-verified.
10. WHEN all checks pass, THE Phase_2_Baseline_Report SHALL be produced recording the explicit pass/fail result for each Audit_Checklist item, the git commit hash at the time of audit, and a PHASE 2 VERIFIED: PASS declaration.

---

### Requirement 2: Concept Mastery Data Model

**User Story:** As a student, I want the system to remember my performance on every concept, so that it can personalise my study plan based on real history.

#### Acceptance Criteria

1. THE Concept_Mastery record SHALL store: `user_id`, `concept_id`, `mastery_score` (Float 0.0–100.0), `questions_attempted` (Integer ≥ 0), `questions_correct` (Integer ≥ 0), `questions_incorrect` (Integer ≥ 0), `last_attempted_at` (DateTime nullable), `last_correct_at` (DateTime nullable), `streak` (Integer ≥ 0, consecutive correct answers, reset to 0 on incorrect answer), `confidence` (Float 0.0–1.0), `state` (String enum: one of NOT_STARTED, VERY_WEAK, WEAK, DEVELOPING, PROFICIENT, MASTERED), `next_review_at` (DateTime nullable), `updated_at` (DateTime auto-updated on every write).
2. THE Concept_Mastery table SHALL enforce a unique constraint on (`user_id`, `concept_id`) so that each student has exactly one mastery record per concept.
3. WHEN a new student answers their first question for a concept, THE Adaptive_Engine SHALL create a Concept_Mastery record with `questions_attempted` = 1, `streak` = 0, and an initial `mastery_score` computed by the LexiMind_Mastery_Score algorithm.
4. IF a Concept_Mastery record creation fails due to a database error, THEN THE Adaptive_Engine SHALL return an error indicating the record could not be persisted and SHALL NOT record the question attempt as processed.
5. THE Question_Attempt table SHALL store: `id`, `user_id`, `question_id`, `concept_id`, `quiz_id`, `selected_answer`, `correct` (Boolean), `difficulty` (String: one of easy, medium, hard), `time_taken` (Float seconds ≥ 0.0, nullable, maximum 3600.0), `created_at` (DateTime).
6. THE Question_Attempt table SHALL NOT duplicate the existing `QuizAnswer` table; IF `QuizAnswer` already captures the required fields, THEN THE Adaptive_Engine SHALL extend or reuse it rather than create a parallel table.
7. WHEN the database is initialised, THE Database_Migration SHALL create all Phase 3 tables and columns without dropping or altering Phase 2 tables.

---

### Requirement 3: LexiMind Mastery Score Algorithm

**User Story:** As a student, I want my mastery score to reflect my actual performance including how recent it is and how hard the questions were, so that the score is a fair and transparent measure of my understanding.

#### Acceptance Criteria

1. THE `calculate_mastery()` function SHALL accept: `questions_correct` (int ≥ 0), `questions_attempted` (int ≥ 0, must be ≥ `questions_correct`), `difficulty_weighted_correct` (float ≥ 0.0), `difficulty_weighted_attempted` (float ≥ 0.0), `recency_score` (float 0.0–1.0, pre-computed by the caller), and SHALL return a `mastery_score` between 0.0 and 100.0 inclusive.
2. THE `calculate_mastery()` function SHALL compute `mastery_score` using the formula: `mastery_score = 100 × ((0.5 × base_accuracy) + (0.3 × difficulty_accuracy) + (0.2 × recency_score))`, where `base_accuracy = questions_correct / questions_attempted` and `difficulty_accuracy = difficulty_weighted_correct / difficulty_weighted_attempted` (both evaluated as 0.0 when their denominator is 0).
3. THE `calculate_mastery()` function SHALL be defined in a single dedicated service module and SHALL NOT be duplicated in route handlers or other service files.
4. WHEN `questions_attempted` is 0, THE `calculate_mastery()` function SHALL return `mastery_score` = 0.0 and `state` = NOT_STARTED without evaluating the formula.
5. IF `questions_correct` > `questions_attempted`, or if `difficulty_weighted_correct` > `difficulty_weighted_attempted`, or if `recency_score` is outside [0.0, 1.0], THEN THE `calculate_mastery()` function SHALL raise a ValueError identifying the invalid parameter.
6. THE difficulty adjustment SHALL apply configurable weights: EASY = 1.0, MEDIUM = 1.25, HARD = 1.5 read from a single configuration object; IF the configuration object is missing or malformed, THEN THE `calculate_mastery()` function SHALL raise a ConfigurationError.
7. THE `recency_score` passed into `calculate_mastery()` SHALL be computed externally using an exponential decay formula applied to the most recent N attempts (default N = 10), where the most recent attempt has weight 1.0 and each earlier attempt has weight multiplied by a configurable decay factor (default 0.85), normalised to the range [0.0, 1.0].
8. THE recency mechanism, decay factor, and N value SHALL be documented in an inline docstring within the function that computes `recency_score`, explaining the formula and rationale.
9. IF `mastery_score` < 30.0 AND `questions_attempted` = 0, THEN THE Adaptive_Engine SHALL assign state NOT_STARTED.
10. IF `mastery_score` < 30.0 AND `questions_attempted` ≥ 1, THEN THE Adaptive_Engine SHALL assign state VERY_WEAK.
11. IF `mastery_score` ≥ 30.0 AND `mastery_score` < 50.0, THEN THE Adaptive_Engine SHALL assign state WEAK.
12. IF `mastery_score` ≥ 50.0 AND `mastery_score` < 70.0, THEN THE Adaptive_Engine SHALL assign state DEVELOPING.
13. IF `mastery_score` ≥ 70.0 AND `mastery_score` < 85.0, THEN THE Adaptive_Engine SHALL assign state PROFICIENT.
14. IF `mastery_score` ≥ 85.0, THEN THE Adaptive_Engine SHALL assign state MASTERED.
15. THE state thresholds SHALL be stored in a single configurable constants object so they can be adjusted without modifying the algorithm logic.
16. WHEN `calculate_mastery()` receives valid inputs where `questions_correct` ≤ `questions_attempted`, THE function SHALL return `mastery_score` in [0.0, 100.0] (bounds invariant).
17. WHEN `calculate_mastery()` receives the same valid inputs on multiple invocations, THE function SHALL return the same `mastery_score` on every invocation (deterministic invariant — no random elements).

---

### Requirement 4: Weak Concept Detection

**User Story:** As a student, I want the system to identify which concepts I am struggling with, so that I can focus my study time where it is most needed.

#### Acceptance Criteria

1. WHEN `get_weak_concepts(user_id)` is called, THE system SHALL return all concepts from the Concept_Mastery table for that user where `mastery_score` < 60 or `state` is one of {VERY_WEAK, WEAK, DEVELOPING}.
2. WHEN returning weak concepts, THE `get_weak_concepts()` function SHALL include for each result: `concept_id`, `concept_name`, `subject_id`, `chapter_id`, `mastery_score`, `state`, and `reason`, where `reason` is a string of at most 300 characters describing the observable data condition that caused the concept to be flagged.
3. THE `reason` field SHALL be set to one of the following values based on the primary flag condition: "low mastery score" if `mastery_score` < 60, "recent incorrect streak" if 3 or more consecutive incorrect answers are detected in the last 10 attempts, "prerequisite weakness" if a prerequisite concept has `mastery_score` < 60, or "no recent practice" if no attempt has been recorded for the concept in the last 30 days.
4. THE `reason` field SHALL contain only factual descriptions derived from `mastery_score`, attempt history, prerequisite scores, or last attempt date, and SHALL NOT reference student intelligence, learning ability, or potential.
5. WHEN a concept's last 10 recorded attempts contain 3 or more consecutive incorrect answers ending at the most recent attempt, THE `get_weak_concepts()` function SHALL include that concept regardless of its overall `mastery_score`.
6. IF a prerequisite concept for a target concept has `mastery_score` < 60, THEN THE `get_weak_concepts()` function SHALL include that prerequisite concept in the results and set its `reason` to "prerequisite weakness".
7. WHEN the `GET /api/learning/weak-concepts/{user_id}` endpoint is called, THE system SHALL call `get_weak_concepts()` and return the list ordered by ascending `mastery_score`, with ties broken by ascending `concept_id`.
8. WHEN a user has no Concept_Mastery records, THE `get_weak_concepts()` function SHALL return an empty list without raising an exception.
9. IF `user_id` does not exist in the system, THEN THE `GET /api/learning/weak-concepts/{user_id}` endpoint SHALL return an empty list with HTTP 200.

---

### Requirement 5: Prerequisite Graph and Awareness

**User Story:** As a student, I want the system to understand which concepts depend on others, so that it does not push me to advanced material before I am ready.

#### Acceptance Criteria

1. THE Prerequisite_Graph SHALL be built by merging prerequisite relationships defined in the curriculum configuration and any prerequisite relationships stored in the database, with database-stored relationships taking precedence when a conflict exists for the same concept pair.
2. THE `get_prerequisites(concept_id)` function SHALL return all direct prerequisite concept IDs for the given concept, or an empty list if none are defined.
3. THE `get_dependents(concept_id)` function SHALL return all concept IDs that directly depend on the given concept.
4. THE `is_prerequisite_mastered(user_id, concept_id)` function SHALL return True when all direct prerequisites of `concept_id` have `mastery_score` ≥ 60 for the given user, and SHALL return True when `concept_id` has no direct prerequisites.
5. WHEN `is_prerequisite_mastered()` returns False for a concept, THE Recommendation_Engine SHALL NOT recommend that concept as the next learning target while at least one concept exists for which `is_prerequisite_mastered()` returns True and whose `mastery_score` for the user is below 100.
6. WHEN a prerequisite is not mastered and a recommendation would skip it, THE Recommendation_Engine SHALL produce a `reason` string that identifies the blocked concept by name, identifies the unmastered prerequisite by name, and indicates that the prerequisite should be reviewed first.
7. THE `GET /api/education/concepts/{concept_id}` response SHALL include a `prerequisites` field listing all direct prerequisite concept IDs and a `dependents` field listing all direct dependent concept IDs for the requested concept.
8. IF `get_prerequisites()`, `get_dependents()`, `is_prerequisite_mastered()`, or `GET /api/education/concepts/{concept_id}` is called with a `concept_id` that does not exist in the Prerequisite_Graph, THEN THE System SHALL return an error response indicating the concept was not found without modifying any stored data.
9. WHEN the Prerequisite_Graph is built, THE System SHALL detect any circular dependency chains among concepts and SHALL log an error identifying the cycle, and SHALL exclude all concepts involved in the cycle from the graph so that the remaining concepts are available for recommendations.

---

### Requirement 6: Recommendation Engine

**User Story:** As a student, I want to receive a personalised next-step recommendation after each quiz or study session, so that I always know what to work on next without having to guess.

#### Acceptance Criteria

1. THE `get_next_recommendation(user_id)` function SHALL return a single Recommendation object containing: `concept_id`, `concept_name`, `reason` (string of 10–300 characters), `estimated_minutes` (int between 1 and 120 inclusive), `priority` (int 1–5, where 1 is highest), and `type` (one of LEARN, REVIEW, PRACTICE, PYQ, QUIZ).
2. THE Recommendation_Engine SHALL prioritise concepts in this order: (1) overdue spaced reviews (current timestamp > next_review_at), (2) weak prerequisites blocking progress (prerequisite mastery_score < 60), (3) weak concepts in the current subject (mastery_score < 60), (4) the next concept in the learning path, (5) a new concept to learn.
3. WHEN computing priority, THE Recommendation_Engine SHALL assign `priority` 1 to the highest-ranked applicable rule from criterion 2, using `weakness_score`, `prerequisite_readiness`, `time_since_last_attempt` (in hours), and `learning_path_position` (integer index) as tiebreakers evaluated in that order.
4. WHEN a recommended concept has type REVIEW, the `reason` field SHALL include the date of the last attempt in YYYY-MM-DD format and the current mastery score as an integer between 0 and 100.
5. THE `GET /api/learning/recommended/{user_id}` endpoint SHALL call `get_next_recommendation()` and return the Recommendation object with HTTP 200.
6. WHEN `subject_id` is provided as a query parameter, THE Recommendation_Engine SHALL only consider concepts belonging to that subject when generating the recommendation.
7. WHEN no Concept_Mastery data exists for a user, THE `get_next_recommendation()` function SHALL return a Recommendation object of type LEARN with `priority` 1 pointing to the concept at position 1 in the default subject's learning path.
8. THE Recommendation_Engine SHALL NOT recommend a concept whose mastery state is MASTERED unless that concept's scheduled next-review timestamp is less than or equal to the current timestamp.
9. IF `get_next_recommendation()` is called for a `user_id` that does not exist in the system, THEN THE endpoint SHALL return an error response indicating the user was not found.
10. IF `subject_id` is provided but no eligible concepts exist within that subject for the given user, THEN THE endpoint SHALL return an error response indicating no recommendation is available for that subject.

---

### Requirement 7: Adaptive Quiz Assembly

**User Story:** As a student, I want quizzes to be assembled based on my weak areas and adjusted to an appropriate difficulty, so that each quiz challenges me at the right level without being frustrating or too easy.

#### Acceptance Criteria

1. THE `POST /api/quizzes/adaptive` endpoint SHALL accept: `user_id`, `subject_id`, optional `chapter_id`, optional `concept_id`, and `question_count` with a minimum of 1, a default of 10, and a maximum of 30.
2. WHEN assembling an Adaptive_Quiz, THE Adaptive_Engine SHALL select `question_count` questions by applying the following ordering: (1) questions whose difficulty tier matches the student's mastery-aligned tier for the concept, (2) questions not attempted by the user in the last 7 days, (3) questions not seen in the current session, with later stages used only as tiebreakers or when higher-priority candidates are exhausted.
3. IF a student's `mastery_score` for a concept is below 40, THEN THE Adaptive_Engine SHALL select at least 60% of questions for that concept from the EASY difficulty tier, filling remaining slots with MEDIUM difficulty questions.
4. IF a student's `mastery_score` for a concept is in the range [40, 70), THEN THE Adaptive_Engine SHALL select at least 60% of questions for that concept from the MEDIUM difficulty tier, filling remaining slots from EASY or HARD tiers.
5. IF a student's `mastery_score` for a concept is 70 or above, THEN THE Adaptive_Engine SHALL select at least 60% of questions for that concept from the HARD difficulty tier, filling remaining slots with MEDIUM difficulty questions.
6. WHEN a student answers 3 consecutive questions correctly during an adaptive quiz session and the current difficulty tier is not HARD, THE Adaptive_Engine SHALL increase the difficulty tier by one level for subsequent questions in that session.
7. WHEN a student answers 2 consecutive questions incorrectly during an adaptive quiz session and the current difficulty tier is not EASY, THE Adaptive_Engine SHALL decrease the difficulty tier by one level for subsequent questions in that session.
8. THE consecutive correct/incorrect thresholds for difficulty adjustment (3 correct, 2 incorrect) SHALL be stored in a single configurable constants object.
9. THE Adaptive_Engine SHALL NOT select a question that the user has already seen in the same quiz session.
10. THE Adaptive_Engine SHALL deprioritise questions attempted by the user within the last 7 days unless no other questions are available for the required concept and difficulty.
11. IF the question bank contains fewer questions than `question_count` for the requested criteria, THEN THE Adaptive_Engine SHALL fill remaining slots by selecting from questions in the following priority order: (1) correct-difficulty questions outside the 7-day recency window, (2) correct-difficulty questions within the 7-day recency window, (3) adjacent-difficulty questions outside the recency window, and SHALL include `insufficient_bank: true` in the response.
12. WHEN no LLM provider is configured, THE Adaptive_Quiz assembly SHALL still work entirely from the database without requiring AI generation.

---

### Requirement 8: Question Attempt Tracking and Repetition Avoidance

**User Story:** As a student, I want the system to remember which questions I have already answered, so that I am not shown the same question repeatedly unless I request a review.

#### Acceptance Criteria

1. WHEN a quiz is submitted, THE Adaptive_Engine SHALL record a Question_Attempt for every question that received a selected answer, capturing the user identity, question identity, concept identity, quiz identity, selected answer, correctness, difficulty level, time taken, and timestamp.
2. WHEN question history is requested for a user, THE Adaptive_Engine SHALL return all Question_Attempt records for that user ordered from most recent to least recent; IF the user has no recorded attempts, THEN THE Adaptive_Engine SHALL return an empty list.
3. WHEN assembling an Adaptive_Quiz, THE Adaptive_Engine SHALL assign lower selection priority to questions the user has attempted within the last 7 days compared to questions the user has not attempted within that period, such that unattempted or older questions are selected first when candidates are available.
4. WHEN question history is requested for a user, THE Adaptive_Engine SHALL return each Question_Attempt enriched with the associated concept name and subject name; IF the requested user identity is not found, THEN THE Adaptive_Engine SHALL return an error indicating the user was not found without returning any attempt records.
5. WHEN `review_requested` is set to True in the Adaptive_Quiz request, THE Adaptive_Engine SHALL allow questions attempted within the last 7 days to be re-selected at normal priority for the concept specified in the review request.
6. WHEN a question being tracked has no resolvable question identity, THE Adaptive_Engine SHALL skip attempt recording for that question without raising an exception and SHALL continue processing the remaining questions in the submission.

---

### Requirement 9: Mistake Analysis and Patterns

**User Story:** As a student, I want to understand the patterns in my mistakes, so that I can identify and address systematic gaps in my understanding.

#### Acceptance Criteria

1. WHEN a student answers a question incorrectly, THE Adaptive_Engine SHALL store the mistake with: `question_id`, `concept_id`, `selected_answer`, `correct_answer`, `difficulty`, and `created_at`.
2. WHEN a request is made to `GET /api/learning/mistakes` with a valid `user_id`, THE Adaptive_Engine SHALL return up to 100 stored mistake records for that user, ordered by `created_at` descending, and SHALL accept an optional `concept_id` query parameter to filter results to that concept.
3. IF the `user_id` provided to `GET /api/learning/mistakes` does not correspond to an existing user, THEN THE Adaptive_Engine SHALL return an error response indicating the user was not found and SHALL return no mistake records.
4. WHEN a concept has 3 or more mistakes recorded for a given user, THE Adaptive_Engine SHALL compute a `pattern_summary` string that includes all of the following components: the concept name, the predominant difficulty level of the mistaken questions, the total mistake count, and the most frequently selected incorrect answer.
5. WHEN a `pattern_summary` is computed, THE Adaptive_Engine SHALL derive it exclusively from the stored fields `concept_id`, `difficulty`, mistake frequency count, and `selected_answer`, and SHALL NOT include claims about learning disabilities or psychological states.
6. WHEN a question has an `explanation` field populated, THE Adaptive_Engine SHALL include the explanation in the mistake record returned by `GET /api/learning/mistakes`.
7. WHEN a question has no `explanation` field populated and an LLM provider is configured, THE Adaptive_Engine SHALL generate an explanation grounded in the question text and correct answer, include it in the mistake record, and mark it as `explanation_source: AI_GENERATED`.
8. IF no LLM provider is configured, THEN THE Adaptive_Engine SHALL return the mistake record without an AI-generated explanation and SHALL NOT raise an exception.

---

### Requirement 10: Spaced Review Scheduling

**User Story:** As a student, I want to be reminded to review concepts at increasing intervals as my mastery improves, so that I retain knowledge without over-studying already-mastered concepts.

#### Acceptance Criteria

1. THE Review_Schedule SHALL store per-user, per-concept: `next_review_at` (DateTime), `current_interval_days` (Int), and `review_count` (Int).
2. WHEN a concept reaches PROFICIENT state for the first time, THE Adaptive_Engine SHALL schedule the first review by setting `current_interval_days` = 1 and `next_review_at` = current UTC timestamp plus 1 day.
3. THE review interval progression SHALL follow the fixed sequence: 1 day, 3 days, 7 days, 14 days, 30 days. IF `current_interval_days` is already at 30 days, THEN THE Adaptive_Engine SHALL keep `current_interval_days` at 30 days on the next successful review, unless the student's mastery level drops below PROFICIENT, in which case criterion 5 applies.
4. WHEN a student completes a review session for a concept and their resulting mastery level is equal to or higher than their mastery level at the start of that review session, THE Adaptive_Engine SHALL advance `current_interval_days` to the next value in the progression sequence and set `next_review_at` = current UTC timestamp plus the new `current_interval_days` value.
5. WHEN a student completes a review session for a concept and their resulting mastery level is lower than their mastery level at the start of that review session, THE Adaptive_Engine SHALL reset `current_interval_days` to 1 and set `next_review_at` = current UTC timestamp plus 1 day.
6. THE `GET /api/learning/review-schedule` endpoint SHALL accept `user_id` as a query parameter and return all concepts with `next_review_at` in the past, ordered by `next_review_at` ascending (most overdue first).
7. IF the `user_id` provided to `GET /api/learning/review-schedule` does not correspond to an existing user, THEN THE system SHALL return an error response indicating the user was not found.
8. WHEN a student completes a review session for a concept whose `next_review_at` is in the future (early review), THE Adaptive_Engine SHALL apply the same interval advancement and `next_review_at` update rules as an on-time review, calculated from the current UTC timestamp.
9. WHEN a concept is overdue for review, THE Recommendation_Engine SHALL assign it priority 1 (highest) in the recommendation ranking, overriding any other priority score computed for that concept.

---

### Requirement 11: Learning Path Integration

**User Story:** As a student, I want my learning path to reflect my real mastery and the adaptive engine's recommendations, so that the path shown in the UI is always current and accurate.

#### Acceptance Criteria

1. THE `GET /api/learning/learning-path/{user_id}/{subject_id}` endpoint SHALL assign each learning path item exactly one status according to the following precedence (highest to lowest): NEEDS_REVIEW (spaced-repetition review date has passed and mastery < 85), COMPLETED (mastery ≥ 85 and not due for review), CURRENT (the single concept with the lowest chapter-order index among all RECOMMENDED items, or the most-recently-accessed concept if no RECOMMENDED items exist), RECOMMENDED (all prerequisites have mastery ≥ 85 and concept is not yet COMPLETED or CURRENT), or LOCKED (at least one prerequisite has mastery < 85).
2. WHEN a quiz is submitted and Concept_Mastery records are updated, THE Learning_Path status for all concepts affected by that submission SHALL be recalculated so that the updated statuses are returned on the immediately subsequent `GET /api/learning/learning-path/{user_id}/{subject_id}` call.
3. WHEN a concept's mastery score reaches 85 or above, THE Learning_Path SHALL evaluate each directly dependent concept in chapter order and transition any concept whose every prerequisite now has mastery ≥ 85 from LOCKED to RECOMMENDED, with exactly one such concept also promoted to CURRENT per the precedence rule in criterion 1.
4. THE learning path response SHALL include the fields `currentConcept` (the single concept with CURRENT status, or null if none), `completedConcepts` (array of all concepts with COMPLETED status), `weakConcepts` (array of all concepts with mastery score between 1 and 59 inclusive), and `recommendedConcepts` (array of all concepts with RECOMMENDED status), and all four fields SHALL be present in every response regardless of whether their values are empty.

---

### Requirement 12: Dashboard Personalisation

**User Story:** As a student, I want the Dashboard to show my real progress and today's plan based on my actual performance, so that the information displayed is accurate and motivating.

#### Acceptance Criteria

1. WHEN the Dashboard loads for the current user, THE Dashboard SHALL display a "Continue Learning" section showing the single concept returned by `get_next_recommendation()`, including the concept name and a brief description of no more than 150 characters.
2. WHEN the Dashboard loads for the current user, THE Dashboard SHALL display a "Today's Plan" section listing between 1 and 3 activities drawn from the Daily_Study_Plan, each showing the activity type, concept name, and assigned duration in minutes.
3. THE Daily_Study_Plan SHALL be constructed by selecting activities in priority order: (1) overdue spaced reviews assigned 10 minutes each, (2) weak concept practice assigned 10 minutes each, and (3) next-concept learning assigned the remaining time up to the user's daily study goal (default 30 minutes), and the total planned duration SHALL NOT exceed the user's daily study goal.
4. WHEN the Dashboard loads for the current user, THE Dashboard SHALL display a "Weak Areas" section showing between 1 and 3 entries returned by `get_weak_concepts()`, where each entry includes the concept name (1–100 characters), mastery score as a percentage between 0 and 100, and a reason string of no more than 200 characters.
5. THE Dashboard SHALL display mastery score values sourced exclusively from the Concept_Mastery table for the current user, and SHALL NOT display hardcoded or default placeholder numeric values.
6. WHEN a user has no Concept_Mastery records, THE Dashboard SHALL display the message "Complete your first quiz to see your personalised dashboard" in place of the "Weak Areas", "Today's Plan", and progress metric sections, and SHALL NOT display zero-value mastery scores.
7. WHEN the `GET /api/learning/progress/{user_id}` endpoint is called, THE endpoint SHALL return a response containing all of the following fields: `totalConcepts` (non-negative integer), `masteredConcepts` (non-negative integer), `inProgressConcepts` (non-negative integer), `needsReviewConcepts` (non-negative integer), `totalQuizAttempts` (non-negative integer), `totalQuestionsAnswered` (non-negative integer), `overallAccuracy` (decimal between 0.00 and 100.00), `studyStreakDays` (non-negative integer), `subjectMastery` (array of zero or more subject entries), and `recentPerformance` (array of the last 5 quiz sessions ordered by most recent first, or fewer if fewer than 5 sessions exist).
8. IF the `GET /api/learning/progress/{user_id}` endpoint is called for a `user_id` that does not exist, THEN THE endpoint SHALL return an error response indicating the user was not found, and SHALL NOT return partial progress data.
9. IF `get_next_recommendation()` returns no result for the current user, THEN THE Dashboard SHALL display a message in the "Continue Learning" section indicating that no recommendation is currently available, and SHALL NOT leave the section blank or crash.

---

### Requirement 13: Progress Page

**User Story:** As a student, I want a dedicated Progress page that shows my full learning history and performance metrics, so that I can track my improvement over time.

#### Acceptance Criteria

1. THE Progress_Page SHALL display: overall mastery score as a percentage between 0 and 100, subject-level mastery breakdown, concept-level mastery list, total quiz attempts, total questions answered, overall accuracy as a percentage between 0 and 100, study streak in days, weak concepts count, and mastered concepts count.
2. ALL metrics on the Progress_Page SHALL be computed from real database values fetched from `GET /api/learning/progress/{user_id}` and SHALL NOT substitute hardcoded fallback data when the API responds successfully.
3. WHEN a chart displays performance data, THE chart data SHALL come from the API response and SHALL NOT use hardcoded seed data.
4. WHEN a user has fewer than 2 quiz attempts, THE Progress_Page SHALL hide the performance charts and display the message "Not enough data yet. Complete more quizzes to see your progress charts." while still displaying any non-chart metrics that have valid values.
5. THE Progress_Page SHALL display a "Recent Performance" section showing the last 5 quiz sessions ordered most recent first, each entry containing date, subject, score, and accuracy.
6. THE Progress_Page SHALL display a "Weak Concepts" section populated from `GET /api/learning/weak-concepts/{user_id}` with concept name, mastery score, and a non-empty text recommendation indicating a direction for improvement.
7. IF either the `GET /api/learning/progress/{user_id}` or `GET /api/learning/weak-concepts/{user_id}` endpoint fails or does not respond within 10 seconds, THEN THE Progress_Page SHALL display an error message identifying which data failed to load and SHALL NOT display partial metric values without a clear label indicating they may be incomplete.

---

### Requirement 14: AI Tutor Personalisation and Source Grounding

**User Story:** As a student, I want the AI Tutor to know my current learning context and mastery state, so that its explanations are tailored to my needs and grounded in real academic material.

#### Acceptance Criteria

1. WHEN a tutor message is sent, THE AI_Tutor SHALL accept in its request body: `subject_id`, `concept_id`, `education_level`, `course`, `action`, and a `student_context` object containing `mastery_score` (numeric value in the range 0 to 100 inclusive), `mastery_state`, `weak_concepts` (list), and `recent_mistakes` (list).
2. THE AI_Tutor system prompt SHALL incorporate the student's `mastery_state` and `weak_concepts` such that the response addresses only terminology and concepts appropriate to the student's `education_level` and avoids introducing concepts absent from `weak_concepts` when `mastery_state` is VERY_WEAK or WEAK.
3. WHEN `mastery_state` is VERY_WEAK or WEAK for the queried concept, THE AI_Tutor system prompt SHALL include an instruction to explain the topic from first principles.
4. WHEN `mastery_state` is AVERAGE or STRONG for the queried concept, THE AI_Tutor system prompt SHALL include an instruction to reinforce core understanding with worked examples relevant to the concept.
5. WHEN `mastery_state` is PROFICIENT or MASTERED, THE AI_Tutor system prompt SHALL include an instruction to focus on advanced applications and exam-style questions.
6. THE AI_Tutor SHALL support these named actions: EXPLAIN, SIMPLIFY, EXAMPLE, HINT, TEST_ME, SIMILAR_QUESTION, EXPLAIN_MISTAKE.
7. WHEN action is EXPLAIN_MISTAKE and `recent_mistakes` is non-empty, THE AI_Tutor SHALL ground the explanation in the specific wrong answer and correct answer from the mistake record.
8. IF action is EXPLAIN_MISTAKE and `recent_mistakes` is empty, THEN THE AI_Tutor SHALL return an error response indicating that no mistake record is available and SHALL NOT proceed to generate an explanation.
9. WHEN action is SIMILAR_QUESTION, THE AI_Tutor SHALL retrieve PYQs or questions from the database for the current concept and present one question grounded in the retrieved source material.
10. IF action is SIMILAR_QUESTION and no matching questions exist in the database for the current concept, THEN THE AI_Tutor SHALL return a response indicating that no similar question is available for the concept and SHALL NOT fabricate a question.
11. WHEN the AI_Tutor response references a document, note, or PYQ, THE response SHALL include a `sources` field containing: `document_name`, `page_number` (included only when present in the retrieved source metadata), and `year` (included only when the source is a PYQ and the year is present in the retrieved source metadata).
12. THE AI_Tutor SHALL NEVER fabricate document names, page numbers, PYQ years, or marks values not present in the retrieved academic context.
13. WHEN no LLM provider is configured, THE AI_Tutor SHALL return a fallback response assembled from retrieved academic context without claiming it is AI-generated.
14. THE existing `/api/chat` endpoint SHALL be extended, NOT replaced, to support the personalised student context fields.

---

### Requirement 15: API Endpoint Design

**User Story:** As a frontend developer, I want a clean, non-duplicated set of API endpoints that expose all adaptive learning capabilities, so that the UI can be built without inconsistency or confusion.

#### Acceptance Criteria

1. THE Adaptive_Engine SHALL expose the following endpoints, each returning a JSON response with HTTP 200 on success:
   - `GET /api/learning/mastery/{user_id}` — all mastery records for a user
   - `GET /api/learning/mastery/{user_id}/{concept_id}` — single concept mastery record
   - `GET /api/learning/recommended/{user_id}` — next recommended concept
   - `GET /api/learning/weak-concepts/{user_id}` — weak concept list
   - `GET /api/learning/learning-path/{user_id}/{subject_id}` — ordered learning path
   - `GET /api/learning/review-schedule?user_id={user_id}` — overdue review items
   - `POST /api/quizzes/adaptive` — adaptive quiz assembly
   - `GET /api/quiz/history?user_id={user_id}` — question attempt history
   - `GET /api/learning/mistakes?user_id={user_id}` — mistake records
   - `GET /api/learning/progress/{user_id}` — full progress summary
   - `POST /api/chat` (extended with adaptive context) — AI Tutor responses informed by the user's current mastery and weak concepts
2. IF an endpoint providing the same HTTP method and resource already exists in Phase 2, THEN THE Adaptive_Engine SHALL extend that existing route to include adaptive learning data rather than register a new duplicate route at the same or semantically equivalent path.
3. ALL endpoints that return per-user data SHALL accept `user_id` as a path parameter or query parameter; THE Adaptive_Engine SHALL reject any `user_id` value that is empty, contains only whitespace, or exceeds 128 characters with a 422 response.
4. WHEN a valid `user_id` is provided but no data exists for that user, THE Adaptive_Engine SHALL return HTTP 200 with an empty array (`[]`) for endpoints that return lists (mastery list, weak concepts, learning path, review schedule, quiz history, mistakes) and an empty object (`{}`) for endpoints that return a single record (single concept mastery, progress summary, next recommendation).
5. IF any required parameter is missing or fails validation, THEN THE Adaptive_Engine SHALL return HTTP 422 with a JSON error body that identifies the name of the invalid or missing parameter and states the reason it was rejected.
6. WHEN `POST /api/quizzes/adaptive` is called, THE Adaptive_Engine SHALL require a request body containing a `user_id` (non-empty string, maximum 128 characters) and a `subject_id` (non-empty string, maximum 128 characters), and SHALL return HTTP 422 if either field is absent or invalid.
7. WHEN `POST /api/chat` is called with a valid `user_id`, THE Adaptive_Engine SHALL include the user's current mastery levels and weak concept list as context when generating the AI Tutor response, such that the response reflects the user's identified knowledge gaps rather than providing generic answers.

---

### Requirement 16: User Data Isolation

**User Story:** As a student, I want my mastery, quiz history, and recommendations to be completely private, so that no other student can see or influence my data.

#### Acceptance Criteria

1. WHEN the backend receives a read request for Concept_Mastery records, THE backend SHALL return only records whose `user_id` matches the `user_id` path parameter of the request, and SHALL NOT include records belonging to any other user.
2. WHEN the backend receives a read request for Question_Attempt records, THE backend SHALL return only records whose `user_id` matches the `user_id` path parameter of the request, and SHALL NOT include records belonging to any other user.
3. WHEN the backend receives a read request for Recommendation or Review_Schedule records, THE backend SHALL return only records whose `user_id` matches the `user_id` path parameter of the request, and SHALL NOT include records belonging to any other user.
4. IF the `user_id` path parameter is absent or empty on any learning data endpoint, THEN THE backend SHALL reject the request with a 422 error response indicating a missing or invalid user identifier, and SHALL NOT return any records.
5. IF the `user_id` path parameter does not match any existing user in the system, THEN THE backend SHALL return an empty result set with HTTP 200 and SHALL NOT return records belonging to any other user.
6. WHEN a write request is received for Concept_Mastery, Question_Attempt, Recommendation, or Review_Schedule records, THE backend SHALL reject the request with a 422 error response if the `user_id` in the request body does not match the `user_id` path parameter, and SHALL NOT persist the record.

---

### Requirement 17: AI Provider Reliability and Fallback

**User Story:** As a student, I want all core learning features to work even when the AI provider is unavailable, so that my study session is never blocked by an external API failure.

#### Acceptance Criteria

1. WHEN the configured LLM provider returns an error response or does not respond within 10 seconds, THE Adaptive_Engine SHALL record the failure event and fall back to database-only operation for quiz generation, mastery calculation, recommendations, and progress display.
2. THE `provider_status()` function from Phase 2 SHALL be the only mechanism through which any component checks LLM availability; no component SHALL invoke LLM availability checks by any other means.
3. WHEN the AI provider is unavailable, THE adaptive quiz assembly SHALL select questions from the database by ordering candidates first by ascending difficulty tier matching the learner's current mastery band, then by ascending last-answered timestamp, without calling any LLM, such that identical mastery band and history inputs always produce the same ordered question set.
4. WHEN the AI provider is unavailable, THE Recommendation_Engine SHALL generate recommendations using only rule-based logic without requiring any LLM output.
5. WHEN the AI provider is unavailable and a student requests an explanation for a mistake, THE AI_Tutor SHALL return the question text and correct answer as the explanation body and SHALL include an `explanation_source: FALLBACK` indicator in the response.
6. WHEN the Adaptive_Engine falls back to database-only operation, THE system SHALL surface a degraded-mode indicator to the student confirming that AI-enhanced features are temporarily unavailable and that core study features remain active.
7. THE existing LLM provider abstraction in `services/llm.py` SHALL be reused; Phase 3 SHALL NOT introduce a parallel provider abstraction.

---

### Requirement 18: Performance and Query Efficiency

**User Story:** As a student, I want dashboard and quiz pages to load quickly, so that the adaptive features do not create noticeable delays compared to Phase 2.

#### Acceptance Criteria

1. THE `get_weak_concepts()` function SHALL use a single database query with JOINs rather than issuing one query per concept (N+1 avoidance).
2. THE `build_learning_path()` function SHALL batch-load all required Concept_Mastery records for a user in a single query rather than querying per concept.
3. WHEN a user requests `POST /api/quizzes/adaptive` for a 10-question adaptive quiz and the database contains between 10 and 999 questions, THE System SHALL return a complete quiz response within 3 seconds.
4. IF the `POST /api/quizzes/adaptive` endpoint does not return a response within 3 seconds, THEN THE System SHALL return an error response indicating that the request timed out, without partially committing quiz state.
5. THE `GET /api/learning/progress/{user_id}` endpoint SHALL use aggregate database queries (COUNT, AVG) rather than loading all records into Python memory for counting.
6. THE Adaptive_Engine SHALL NOT introduce any external caching infrastructure (no Redis, Memcached, or external cache servers). In-process caching scoped to a single request lifecycle, such as with `functools.lru_cache`, is acceptable only for Concept and Curriculum data that does not change between requests within a session.

---

### Requirement 19: Demo and Seed Data for Testing

**User Story:** As a developer, I want a minimum viable seed data set so that the adaptive features can be exercised end-to-end in a fresh environment, so that testing does not require manual data entry.

#### Acceptance Criteria

1. THE seed data SHALL include at least 3 concepts with at least 1 prerequisite relationship defined between them, at least 10 questions spanning at least 2 distinct difficulty levels (where difficulty is one of easy, medium, hard), at least 1 concept with a mastery record in WEAK state, and at least 1 concept with a mastery record in MASTERED state.
2. THE seed data SHALL be loaded by the existing `demo_seed.py` mechanism during `init_db()` and SHALL NOT insert any seed records if a seed concept record with a designated seed identifier already exists in the database.
3. WHEN the seed is loaded, THE system SHALL produce at least 1 quiz assembly result, at least 1 mastery update record, and at least 1 recommendation entry when the adaptive loop is exercised using only the seeded concepts, questions, and mastery records — without requiring any additional manual data entry.
4. THE seed questions SHALL each include a `concept_id` referencing a seeded concept, a `difficulty` value of easy, medium, or hard, and a non-empty `source` field so that the adaptive engine can filter and weight them during quiz assembly.

---

### Requirement 20: Automated Tests

**User Story:** As a developer, I want automated tests for the adaptive engine's core algorithms, so that mastery calculations, recommendations, and quiz assembly can be verified to be correct and deterministic.

#### Acceptance Criteria

1. THE test suite SHALL include deterministic unit tests for `calculate_mastery()` covering: zero attempts (expected score: 0.0), all-correct attempts, all-incorrect attempts, mixed attempts with difficulty weights applied, and mixed attempts with recency decay applied, where each test asserts the exact floating-point output to 4 decimal places using fixed input values for attempt timestamps, difficulty coefficients, and decay constants.
2. THE test suite SHALL include unit tests for concept state thresholds verifying that scores of 0, 29, and 30 map to distinct states at the 29/30 boundary, scores of 49 and 50 map to distinct states at the 49/50 boundary, scores of 69 and 70 map to distinct states at the 69/70 boundary, and scores of 84 and 85 map to distinct states at the 84/85 boundary.
3. THE test suite SHALL include unit tests for `get_weak_concepts()` verifying: empty input returns an empty list, concepts with scores strictly below 60 are included, concepts with scores at or above 60 are excluded, and the function returns an empty list (not an exception) when called for a user with no recorded data.
4. THE test suite SHALL include unit tests for `is_prerequisite_mastered()` verifying: a concept with no prerequisites returns True, a concept whose every prerequisite has mastery_score ≥ 60 returns True, and a concept with at least one prerequisite whose mastery_score is below 60 returns False.
5. THE test suite SHALL include unit tests for adaptive question selection verifying: questions attempted within the last 7 days are ranked lower than questions not attempted within that period, difficulty targeting selects at least 60% of questions from the mastery-aligned difficulty tier, and when the eligible question bank contains fewer than the requested count the response includes `insufficient_bank: true` without raising an exception.
6. THE test suite SHALL include unit tests for review interval progression verifying the sequence 1 → 3 → 7 → 14 → 30 days across five consecutive successful reviews, and that a mastery level drop at any step resets the next interval to 1 day.
7. ALL unit tests SHALL be deterministic: fixed inputs SHALL produce identical outputs on every run, no external API calls SHALL be made, and each test case SHALL set up and tear down its own in-memory state so that no shared database or file state persists between test cases.
8. THE test files SHALL be placed in a `backend/tests/` directory and SHALL be runnable with `pytest backend/tests/` from the repository root without additional configuration, completing within 60 seconds for the full suite.
9. IF any unit test imports an application module that performs I/O or network access at import time, THEN THE test suite SHALL use dependency injection or patching to replace those calls with in-memory stubs so that the test remains runnable without a live database or network connection.

---

### Requirement 21: Complete End-to-End User Journey

**User Story:** As a student, I want a complete, unbroken journey from the Dashboard through studying, taking an adaptive quiz, reviewing mistakes, and receiving the next recommendation, so that every step connects logically to the next.

#### Acceptance Criteria

1. WHEN a user opens the Dashboard, THE system SHALL display their current learning path position, today's recommended study plan, and all concepts with a mastery score below 60, sourced from the live database at request time.
2. WHEN a user navigates to a concept and takes an adaptive quiz, THE system SHALL assemble the quiz via the Adaptive_Engine using questions whose difficulty band matches the student's current mastery score for that concept: easy (mastery 0–39), medium (mastery 40–69), or hard (mastery 70–100).
3. WHEN a user submits the adaptive quiz, THE system SHALL persist all Question_Attempt records, recalculate mastery for each answered concept, update the Learning_Path states, generate a new recommendation via `get_next_recommendation()`, and schedule any new spaced reviews, completing all five operations as a single atomic transaction before returning the results response.
4. IF any operation in the quiz submission chain fails, THEN THE system SHALL return an error response indicating which operation failed, leave all previously committed data unchanged, and not display the quiz results screen.
5. WHEN the quiz results are displayed, THE system SHALL show the total score as a percentage, per-question correctness indicators, an explanation for each question that has one stored in the database, and a navigable link to the concept returned by `get_next_recommendation()`.
6. WHEN a user sends a message to the AI Tutor about a concept after completing a quiz on that concept, THE AI_Tutor SHALL include the student's current mastery score and the titles of any questions answered incorrectly in that quiz session as part of the context sent to the AI model.
7. THE end-to-end journey SHALL complete without any HTTP 5xx responses, unhandled JavaScript exceptions, or screens that render with no visible content when all Phase 2 integration checks pass.

---

### Requirement 22: Edge Case Handling

**User Story:** As a developer, I want all edge cases handled gracefully, so that the system never crashes or displays misleading information due to missing or unusual data.

#### Acceptance Criteria

1. WHEN a new user with no quiz history opens the system, THE system SHALL display a non-error empty state for each dashboard section that would otherwise show quiz metrics, containing explanatory text indicating no activity has been recorded yet, with no numeric values displayed as zero without a label clarifying they represent no data.
2. WHEN a concept has no questions in the question bank, THE `POST /api/quizzes/adaptive` endpoint SHALL return a response body containing `questions` as an empty array, `insufficient_bank` as true, and `reason` as a non-empty string indicating no questions are available for the concept, with HTTP 200.
3. WHEN a concept has no prerequisites defined, THE `is_prerequisite_mastered()` function SHALL return True without querying the database or raising an exception.
4. WHEN a question record does not contain an `explanation` field, THE mistake record response SHALL include `explanation` with a null value rather than omitting the field or raising an unhandled exception.
5. WHEN all concepts for a subject are in MASTERED state, THE Recommendation_Engine SHALL return a recommendation identifying the concept whose `last_attempted_at` timestamp is the earliest among all mastered concepts for that subject.
6. WHEN a user has answered every concept with a mastery score below the mastery threshold, THE Recommendation_Engine SHALL return a recommendation identifying the concept with the highest numeric mastery score among all concepts for that subject.
7. WHEN the database is unavailable, THE API endpoints SHALL return HTTP 503 with a response body containing a human-readable message indicating service unavailability, and SHALL NOT propagate an unhandled 500 response.
8. WHEN `question_count` in a `POST /api/quizzes/adaptive` request is 0 or a negative integer, THE endpoint SHALL treat the value as 1 and return exactly 1 question without returning a validation error response.
9. WHEN a student's streak counter value is NULL in the database, THE `calculate_mastery()` function SHALL substitute the value 0 for the NULL streak counter and complete the mastery calculation without raising an exception.
10. IF two or more concepts share the same earliest `last_attempted_at` timestamp when all concepts are in MASTERED state, THEN THE Recommendation_Engine SHALL select the concept with the lowest alphabetical concept name among the tied concepts as the recommendation.
11. IF two or more concepts share the highest mastery score when all concepts are below the mastery threshold, THEN THE Recommendation_Engine SHALL select the concept with the lowest alphabetical concept name among the tied concepts as the recommendation.
