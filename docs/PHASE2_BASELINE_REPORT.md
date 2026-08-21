# Phase 2 Baseline Report

Environment used for every check below:

```
Ubuntu 22.04 · Python 3.10.12 · Node v20.18.1
backend  : /home/ubuntu/venv-leximind/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
frontend : npm run dev  (Vite)
database : SQLite (backend/leximind.db) via SQLAlchemy async + aiosqlite
```

## A1 — Application startup

| Check | Result |
|---|---|
| Backend starts | PASS (`{"status":"ok"}` from `/health`) |
| Frontend builds and starts | PASS (`npm run build`, `npm run dev`) |
| Import errors | None after dependency repair (below) |
| TypeScript errors | None (`npx tsc --noEmit`, exit 0) |
| Database connects | PASS (tables created on startup; SQLite in-place column migration added) |
| Existing API routes respond | PASS (`/api/education/health` → 17 courses, 5 subjects, 6 chapters, 7 concepts) |

**Failure found:** the pinned dependency set could not be installed — spaCy/Typer/FastAPI version conflicts, plus heavy neural packages (`torch`, `transformers`, `sentence-transformers`) in the default install.

**Fix:** widened the ranges in `backend/requirements.txt` and moved the optional neural retrieval stack into `backend/requirements-embeddings.txt`. TF-IDF retrieval remains the default path, so nothing depends on the optional install.

## A2 — Document pipeline

Verified by uploading generated TXT/PDF fixtures through `POST /api/documents/upload` and inspecting the database afterwards.

| Check | Result |
|---|---|
| PDF upload | PASS |
| Metadata stored | PASS |
| Status transitions (UPLOADED → PROCESSING → READY/FAILED) | PASS after fix |
| PDF text extraction (PyMuPDF) | PASS |
| Page information preserved | PASS (`extract_structured_pages`) |
| Text cleaning | PASS |
| Document classification | PASS |
| Chunks created | PASS |
| Topics extracted | PASS |
| Concepts extracted | PASS |
| PYQ extraction | PASS |
| Question types classified | PASS |
| Questions stored | PASS |
| Question → concept mappings stored | PASS (`QuestionConcept` with confidence) |
| Search | PASS (`/api/documents/{id}/search`, `/api/search`) |
| Document detail | PASS |

**Failure found:** processing intermittently died with `ValueError("Document not found")`. The upload route flushed the row but the background task opens its own session, so the row was not always visible.

**Fix:** `backend/app/api/documents.py` now commits and refreshes before scheduling the background task. `backend/app/services/pipeline.py` now logs the exception and rolls back its session on failure instead of leaving a poisoned transaction.

## A3 — Quiz system

| Check | Result |
|---|---|
| Quiz loads / questions come from the backend | PASS (`/api/questions`, `/api/quizzes/*`) |
| Not hardcoded frontend data | PASS |
| Answer submission, correct/incorrect state | PASS |
| Quiz completion and score | PASS |
| Attempts persisted with question id + concept id | PASS after fix |

**Failure found:** the completion payload dropped `question_id`/`concept_id` when the client sent camelCase, so attempts persisted without traceability.

**Fix:** the completion path normalises the payload and derives the concept, difficulty and correct answer from the stored `Question` row, so every attempt is traceable.

## A4 — Notes / PYQ system

Subjects, chapters, concepts, notes and PYQs all load from the backend. PYQ rows retain `source` and `year`; generated questions are stored as `source="AI_GENERATED"` with `year = None` and are never presented as authentic PYQs (asserted in `tests/test_quiz_and_config.py`).

**Failure found:** `partial-derivatives-dc` declared a prerequisite (`derivatives-dc`) that did not exist in the curriculum, breaking prerequisite traversal. **Fix:** the missing concept was added with its own prerequisite (`limits-dc`), description, difficulty and key points.

## A5 — AI tutor

| Check | Result |
|---|---|
| Tutor page loads | PASS |
| Provider configuration | PASS — `/api/ai/status` reports `{"provider":"gemini","configured":false,"available":false,"fallback":"local"}` |
| API keys backend-only | PASS |
| Provider request when configured | Not exercised — no key is provisioned in this environment |
| Fallback behaviour | PASS — deterministic, database-grounded replies |
| API failure does not crash the UI | PASS |
| Retrieval/context | PASS (TF-IDF over stored chunks/notes) |
| No secrets in bundles or logs | PASS — no key material in `frontend/dist` |

## A6 — Security

| Check | Result |
|---|---|
| `.env` ignored | PASS — it was tracked; removed from the index |
| No hardcoded keys | PASS |
| Keys never returned by the API | PASS — `/api/ai/status` returns booleans only |
| Keys never sent to the browser | PASS |
| Uploaded files unreachable by arbitrary paths | PASS — uploads are saved under `uploads/` with a UUID-prefixed sanitised name; no route accepts a client path, and deletion resolves `Path(doc.filename).name` |
| User data scoped | Repaired — see below |

**Failure found:** every document route was global; any caller could list, read, search or delete any uploaded document.

**Fix:** identity is resolved once in `backend/app/core/identity.py` and document routes now filter by owner. Documents with no recorded owner (pre-existing uploads) stay readable so existing libraries keep working; documents owned by another user return 404, and a mismatch between `X-User-Id` and an explicit `user_id` returns 403. Covered by `backend/tests/test_document_isolation.py`.

## Status

```
PHASE 2 VERIFIED: PASS
```

Verified by: `pytest` (63 tests), `npx tsc --noEmit`, `npm run build`, and live probes of the routes listed above against a running server.

Known limitation carried into Phase 3: the project still has no authentication layer. Identity is resolved from `request.state.user_id` when present and otherwise from the `X-User-Id` header / explicit id, with cross-user requests rejected. Adding real auth only requires populating `request.state.user_id` in middleware.
