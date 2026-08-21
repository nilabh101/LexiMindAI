# LexiMind AI

An adaptive learning platform that turns academic PDFs into a personalised study experience — from document ingestion to concept mastery tracking and AI-powered tutoring.

Built with FastAPI, React, SQLite, and Google Gemini.

---

## What It Does

Upload a PDF of lecture notes or a past exam paper. LexiMind extracts every concept and question from it, builds a knowledge graph, tracks how well you understand each topic, and adapts every quiz and recommendation to your current mastery level.

**Core loop:**

```
Upload PDF → Extract concepts & questions → Take adaptive quiz
    → Mastery updates → Weakness detected → Personalised recommendation
    → AI Tutor explains with sources → Repeat
```

---

## Features

### Document Intelligence (Phase 2)
- Upload PDF, DOCX, or TXT files up to 500 MB
- Automatic document classification — PYQ, Study Notes, Question Bank, Reference
- Page-aware text extraction with OCR fallback for scanned PDFs
- Semantic chunking that respects heading structure
- Concept extraction and normalisation (deduplicates "Euler theorem" / "Euler's Theorem")
- Question extraction from past papers — preserves question number, marks, year
- Question-to-concept mapping with confidence scores
- Difficulty estimation (EASY / MEDIUM / HARD) per question
- Human review workflow for low-confidence extractions

### Adaptive Learning Engine (Phase 3)
- **LexiMind Mastery Score** — transparent formula combining accuracy, difficulty weighting, and recency decay
  ```
  mastery = 100 × (0.5 × base_accuracy + 0.3 × difficulty_accuracy + 0.2 × recency_score)
  ```
- **6 mastery states** — NOT_STARTED → VERY_WEAK → WEAK → DEVELOPING → PROFICIENT → MASTERED
- **Prerequisite graph** — concepts depend on each other; the engine never pushes advanced material until prerequisites are solid
- **Adaptive quiz assembly** — difficulty targeting (60% rule): mastery < 40 → EASY, 40–70 → MEDIUM, ≥70 → HARD; in-session adjustment after 3 correct/2 incorrect streaks
- **Weak concept detection** — flags by low score, consecutive incorrect streak, or no recent practice
- **Recommendation engine** — 5-level priority: overdue reviews → weak prerequisites → weak concepts → next on path → new concept
- **Spaced repetition** — review intervals: 1 → 3 → 7 → 14 → 30 days; resets on mastery regression
- **Daily study plan** — time-boxed activities based on your study goal (default 30 min)
- **Mistake analysis** — stores every wrong answer, computes pattern summaries, surfaces explanations

### AI Tutor
- Powered by Google Gemini (configurable — OpenAI-compatible APIs and Hugging Face also supported)
- Retrieval-Augmented Generation: answers are grounded in your uploaded study material
- Adapts explanation depth to your mastery state (first-principles for weak, exam-level for proficient)
- 7 action types: EXPLAIN, SIMPLIFY, EXAMPLE, HINT, TEST_ME, SIMILAR_QUESTION, EXPLAIN_MISTAKE
- Returns source citations (document name + page) — never fabricates references
- Fully functional without an API key (returns retrieved context as fallback)

### Data Pipeline (Phase 4)
- Bulk ingestion CLI for processing entire directories of PDFs
- SHA-256 duplicate detection prevents re-processing the same file
- Ingestion manifest tracks every processed file with document ID and status
- JSONL dataset export for approved questions (future model training)

### Document Analysis (Phase 1 — original features)
Word frequency, sentiment, emotion detection, topics/NER, document DNA fingerprint, writing style classification, quiz/flashcard generation from any document, AI insights, bias detection, PDF reports

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, Framer Motion, Recharts |
| Backend | FastAPI, Python 3.11, SQLAlchemy (async), aiosqlite |
| Database | SQLite (file-based, zero config) |
| NLP | spaCy, NLTK, TextBlob, scikit-learn (TF-IDF), sentence-transformers |
| PDF | PyMuPDF, PyPDF2, pdfminer |
| AI | Google Gemini 1.5 Flash (primary), OpenAI-compatible, Hugging Face (configurable) |
| Embeddings | TF-IDF (default, no infra needed), sentence-transformers (optional) |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Google Gemini API key (free tier — [get one here](https://aistudio.google.com))

### 1. Clone

```bash
git clone https://github.com/nilabh101/LexiMindAI.git
cd LexiMindAI
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate
# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.backend.example .env
# Edit .env — add your GEMINI_API_KEY
```

### 3. Frontend setup

```bash
cd frontend
npm install
cp ../.env.frontend.example .env.local
# .env.local already points to http://localhost:8000/api — no changes needed for local dev
```

### 4. Run

In two separate terminals:

```bash
# Terminal 1 — Backend
cd backend
.venv\Scripts\uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

The database (`leximind.db`) is created automatically on first run. Demo data (3 concepts, 12 questions, mastery records) is seeded automatically.

---

## Environment Variables

### Backend (`backend/.env`)

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here
LLM_PROVIDER=gemini

# Defaults (no changes needed for local dev)
APP_NAME=LexiMind AI
DATABASE_URL=sqlite+aiosqlite:///./leximind.db
GEMINI_MODEL=gemini-1.5-flash
EMBEDDING_PROVIDER=tfidf
MAX_FILE_SIZE_MB=50

# Optional — alternative providers
OPENAI_API_KEY=
OPENAI_BASE_URL=
HF_TOKEN=
```

### Frontend (`frontend/.env.local`)

```env
VITE_API_URL=http://localhost:8000/api
```

---

## Ingesting Your Own PDFs

Place PDFs in `data/raw/` (gitignored) and run the ingestion CLI:

```bash
cd backend

# Single file
.venv\Scripts\python -m app.scripts.ingest_documents \
  --file "../data/raw/pyqs/2025_maths.pdf" \
  --subject-id em1-btech \
  --document-type PYQ \
  --year 2025

# Entire directory
.venv\Scripts\python -m app.scripts.ingest_documents \
  --path "../data/raw/" \
  --subject-id em1-btech

# Dry run (scan only, no ingestion)
.venv\Scripts\python -m app.scripts.ingest_documents \
  --path "../data/raw/" --dry-run
```

The ingestion script:
- Detects and skips duplicates (SHA-256 content hash)
- Classifies document type automatically if not specified
- Reports SUCCESS / FAILED / DUPLICATE / SKIPPED per file
- Saves a manifest at `data/manifests/ingestion_manifest.json`

After ingestion, low-confidence items can be reviewed via the My Library page or `GET /api/review/questions`.

---

## Exporting the Dataset

```bash
cd backend
.venv\Scripts\python -m app.scripts.export_dataset \
  --output "../data/exports/dataset_v1.jsonl"
```

Exports all APPROVED questions as JSONL:
```json
{"question": "Verify Euler's theorem for u = x³ + y³.", "concept": "Euler's Theorem", "subject": "em1-btech", "difficulty": "MEDIUM", "question_type": "PROOF", "source_type": "PYQ", "year": 2025}
```

---

## Running Tests

```bash
cd backend
.venv\Scripts\python -m pytest tests/test_adaptive_engine.py -v
```

55 deterministic unit tests covering:
- `calculate_mastery` — bounds invariant, determinism, all boundary cases
- `get_mastery_state` — all 5 boundary pairs (29/30, 49/50, 69/70, 84/85)
- `compute_recency_score` — exponential decay correctness
- `detect_cycles` — DAG validation
- `advance_interval` — full 1→3→7→14→30 progression
- `compute_session_difficulty_adjustment` — tier up/down/clamping
- `_primary_tier` — mastery-to-difficulty mapping

---

## API Reference

Interactive docs available at [http://localhost:8000/api/docs](http://localhost:8000/api/docs) when the backend is running.

### Adaptive Learning Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/learning/mastery/{user_id}` | All mastery records for user |
| `GET` | `/api/learning/mastery/{user_id}/{concept_id}` | Single concept mastery |
| `GET` | `/api/learning/recommended/{user_id}` | Next personalised recommendation |
| `GET` | `/api/learning/weak-concepts/{user_id}` | Weak concepts with reasons |
| `GET` | `/api/learning/learning-path/{user_id}/{subject_id}` | Learning path with Phase 3 statuses |
| `GET` | `/api/learning/review-schedule` | Overdue spaced reviews |
| `GET` | `/api/learning/mistakes` | Mistake history with pattern summaries |
| `GET` | `/api/learning/progress/{user_id}` | Full progress summary |
| `GET` | `/api/learning/daily-plan/{user_id}` | Today's time-boxed study plan |
| `POST` | `/api/learning/quiz-attempt` | Submit quiz, update mastery + schedule reviews |
| `POST` | `/api/quizzes/adaptive` | Assemble adaptive quiz by mastery level |
| `GET` | `/api/quiz/history` | Question attempt history |
| `POST` | `/api/chat` | AI Tutor (supports `student_context` for personalisation) |

### Document Pipeline Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/documents/upload` | Upload and process a PDF/DOCX/TXT |
| `GET` | `/api/documents/` | List all documents |
| `GET` | `/api/documents/{id}/detail` | Full document detail with concepts and questions |
| `POST` | `/api/documents/{id}/retry` | Reprocess a failed document |
| `GET` | `/api/search` | Search across concepts, notes, questions, documents |
| `GET` | `/api/questions` | List questions with filters |
| `GET` | `/api/notes` | List academic notes |
| `GET` | `/api/ai/status` | AI provider status (never returns key values) |

---

## Project Structure

```
LexiMindAI/
├── backend/
│   ├── app/
│   │   ├── api/           ← FastAPI route handlers
│   │   ├── core/          ← Config, database, migrations
│   │   ├── models/        ← SQLAlchemy ORM models
│   │   ├── nlp/           ← Text processing, NLP modules
│   │   ├── scripts/       ← CLI tools (ingest, export)
│   │   └── services/      ← Business logic, adaptive engine
│   ├── tests/             ← Pytest test suite
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── data/          ← Static curriculum definitions
│   │   ├── lib/           ← API client (api.ts)
│   │   ├── pages/
│   │   │   └── app/       ← Live student-facing pages
│   │   ├── services/      ← adaptiveEngine.ts (real API calls)
│   │   └── types/         ← TypeScript types
│   └── package.json
├── data/                  ← Local academic PDFs (gitignored)
│   ├── raw/               ← Place your PDFs here
│   ├── exports/           ← JSONL dataset exports
│   └── README.md
├── .env.backend.example
├── .env.frontend.example
├── FEATURES.md            ← Deep-dive into every feature
└── README.md
```

---

## Mastery Algorithm

The LexiMind Mastery Score (0–100) combines three signals:

```
base_accuracy       = correct_answers / total_attempts
difficulty_accuracy = Σ(weight[difficulty] for correct) / Σ(weight[difficulty] for all)
recency_score       = exponential_decay_weighted_accuracy(last_10_attempts, decay=0.85)

mastery_score = 100 × (0.5 × base_accuracy
                      + 0.3 × difficulty_accuracy
                      + 0.2 × recency_score)
```

Difficulty weights: EASY = 1.0, MEDIUM = 1.25, HARD = 1.5

Mastery states:

| Score | State |
|-------|-------|
| 0 (no attempts) | NOT_STARTED |
| 0–29 | VERY_WEAK |
| 30–49 | WEAK |
| 50–69 | DEVELOPING |
| 70–84 | PROFICIENT |
| 85–100 | MASTERED |

The algorithm is intentionally transparent and deterministic — no black-box ML model. It can be replaced or tuned by editing a single function in `backend/app/services/adaptive_mastery.py`.

---

## Security Notes

- API keys are stored in `backend/.env` only — never committed to git, never sent to the browser
- `backend/.env` and `backend/leximind.db` are gitignored
- The AI status endpoint (`GET /api/ai/status`) returns `{"configured": true}` — never the key value
- Uploaded files are validated by extension and size; stored with a UUID prefix to prevent path traversal
- All per-user data queries are scoped by `user_id` — no cross-user data leakage

---

## Known Limitations

- **SQLite only** — works perfectly for development and single-user use. For multi-user production, swap `DATABASE_URL` for PostgreSQL and run `alembic upgrade head`.
- **Synchronous PDF extraction** — large PDFs (>50 MB) can take 10–30 seconds. The pipeline runs as a background task so the API response is immediate, but processing time is visible in My Library.
- **Curriculum is static** — subjects, chapters, and concepts are defined in `backend/app/api/education.py`. Uploaded PDFs add to this via the extraction pipeline, but the base curriculum is hardcoded for the current course set.
- **No authentication** — user identity is a client-provided `user_id` string. Suitable for personal use and demos. Adding JWT auth requires wiring `user_id` from the token rather than the request body.
- **Embeddings default to TF-IDF** — works well for keyword retrieval. For semantic search, set `EMBEDDING_PROVIDER=sentence-transformers` in `.env` (requires `torch` to be installed, ~2 GB).

---

## License

MIT
