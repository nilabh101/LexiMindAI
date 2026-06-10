# LexiMind AI — Document Intelligence Platform

> Transform any document into deep, actionable intelligence using NLP and AI.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178c6?logo=typescript)](https://www.typescriptlang.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3-38bdf8?logo=tailwindcss)](https://tailwindcss.com)

---

## What is LexiMind AI?

LexiMind AI is a full-stack document intelligence platform. Upload a PDF, Word document, or plain text file (up to **500 MB**) and instantly get:

- **Word & sentence statistics** — word count, sentence count, paragraphs, reading time, grade level, Flesch ease score
- **Word frequency analysis** — bar charts, sortable tables, word cloud, vocabulary treemap
- **Sentiment analysis** — sentence-level polarity, subjectivity, emotion radar (8 emotions)
- **AI extractive summary** — executive summary, bullet points, key sentences
- **Topic detection** — TF-IDF keyword extraction, named entity recognition (people, places, organisations)
- **Document DNA** — 6-dimension linguistic fingerprint (complexity, formality, creativity, etc.)
- **In-document search** — find any word or phrase, see every line number, char position, and context snippet
- **Quiz generator** — AI-generated MCQs with explanations, instant grading, review screen
- **Flashcard study** — flip mode (mark known/unknown), practice mode (side-by-side answers)
- **Reports** — downloadable PDF analysis reports

---

## Project Structure

```
LexiMindAI/
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── api/
│   │   │   ├── documents.py  # Upload, list, delete, search endpoints
│   │   │   └── analysis.py   # All NLP analysis endpoints
│   │   ├── nlp/
│   │   │   ├── text_processor.py   # Tokenization, stats, frequency
│   │   │   ├── sentiment.py        # TextBlob sentiment + emotions
│   │   │   ├── topics.py           # TF-IDF topics + spaCy NER
│   │   │   ├── style_analyzer.py   # Writing style + Document DNA
│   │   │   ├── summarizer.py       # Extractive summarization
│   │   │   ├── question_gen.py     # MCQ + flashcard generation
│   │   │   ├── insights.py         # AI insight synthesis
│   │   │   └── comparison.py       # Multi-document comparison
│   │   ├── models/
│   │   │   └── document.py         # SQLAlchemy models
│   │   ├── database/
│   │   │   └── connection.py       # SQLite connection
│   │   └── main.py                 # FastAPI app + CORS
│   ├── requirements.txt
│   └── .env.backend.example
│
├── frontend/                 # React + TypeScript frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx       # Home with KPIs + recent docs
│   │   │   ├── Upload.tsx          # Drag-drop uploader (500 MB)
│   │   │   ├── AnalysisPage.tsx    # Word + Sentiment + Summary tabs
│   │   │   ├── TopicsPage.tsx      # Topics + entities
│   │   │   ├── DNAPage.tsx         # Document DNA radar
│   │   │   ├── SearchPage.tsx      # In-document search
│   │   │   ├── QuizPage.tsx        # MCQ quiz + flashcards
│   │   │   ├── ReportsPage.tsx     # PDF report download
│   │   │   └── CorePage.tsx        # Core of the Project
│   │   ├── components/
│   │   │   ├── Layout.tsx          # Sidebar navigation
│   │   │   ├── DocSelector.tsx     # Document picker dropdown
│   │   │   ├── PageHeader.tsx      # Reusable page header
│   │   │   ├── LoadingSpinner.tsx  # Loading state
│   │   │   └── KpiCard.tsx         # Metric card
│   │   ├── lib/
│   │   │   ├── api.ts              # Axios API client
│   │   │   └── utils.ts            # Helpers (formatBytes, cn, etc.)
│   │   └── main.tsx                # App entry + routing
│   ├── package.json
│   └── .env.frontend.example
│
├── .gitignore
├── README.md
└── FEATURES.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### 1. Clone the repo

```bash
git clone https://github.com/your-username/LexiMindAI.git
cd LexiMindAI
```

### 2. Backend setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Download NLTK data (auto-downloads on first run, or manually)
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

# Copy env file
copy .env.backend.example .env

# Start the server
python -m uvicorn app.main:app --reload --port 8000
```

Backend runs at **http://localhost:8000**  
API docs at **http://localhost:8000/docs**

### 3. Frontend setup

```bash
cd frontend

# Copy env file
copy .env.frontend.example .env

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs at **http://localhost:5173**

---

## API Endpoints

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/documents/upload` | Upload TXT, PDF, or DOCX (max 500 MB) |
| `GET`  | `/api/documents/` | List all documents |
| `GET`  | `/api/documents/{id}` | Get document metadata |
| `DELETE` | `/api/documents/{id}` | Delete a document |
| `GET`  | `/api/documents/{id}/search?query=...` | Search word/phrase in document |

### Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/analysis/{id}/stats` | Word/sentence/paragraph/readability stats |
| `GET` | `/api/analysis/{id}/words` | Word frequency analysis |
| `GET` | `/api/analysis/{id}/wordcloud` | Word cloud image (base64) |
| `GET` | `/api/analysis/{id}/sentiment` | Sentiment + sentence breakdown |
| `GET` | `/api/analysis/{id}/emotions` | 8-emotion detection |
| `GET` | `/api/analysis/{id}/topics` | Topic detection + TF-IDF keywords |
| `GET` | `/api/analysis/{id}/entities` | Named entity recognition |
| `GET` | `/api/analysis/{id}/dna` | Document DNA fingerprint |
| `GET` | `/api/analysis/{id}/summary` | Extractive AI summary |
| `GET` | `/api/analysis/{id}/quiz` | Generate MCQ quiz |
| `GET` | `/api/analysis/{id}/flashcards` | Generate flashcards |
| `GET` | `/api/analysis/{id}/insights` | AI-synthesised insights |
| `GET` | `/api/analysis/{id}/bias` | Bias detection |
| `GET` | `/api/analysis/{id}/full` | All analyses in one call |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend framework | FastAPI |
| Database ORM | SQLAlchemy + SQLite |
| NLP | spaCy, TextBlob, NLTK, scikit-learn |
| Frontend framework | React 18 + TypeScript |
| Styling | TailwindCSS v3 |
| Charts | Recharts |
| Animations | Framer Motion |
| State management | TanStack Query |
| HTTP client | Axios |
| File upload | react-dropzone |

---

## Environment Variables

Copy the example files and never commit real `.env` files:

```bash
# Backend
copy .env.backend.example backend/.env

# Frontend  
copy .env.frontend.example frontend/.env
```

See `.env.backend.example` and `.env.frontend.example` for all available variables.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.
