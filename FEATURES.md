# LexiMind AI — Features & Technical Explanation

A personal deep-dive into every feature, what it does, how it works under the hood, and what libraries power it.

---

## 1. Document Upload (up to 500 MB)

**What it does:**  
Accepts TXT, PDF, and DOCX files up to 500 MB via a drag-and-drop interface. Shows a real-time upload progress bar, then redirects to analysis automatically.

**How it works:**  
- Frontend uses `react-dropzone` to handle drag-and-drop and file validation (type + size)
- File is sent as `multipart/form-data` via `axios` with an `onUploadProgress` callback to drive the progress bar
- Backend (`FastAPI`, `python-multipart`) receives the file, reads bytes, and routes to a parser:
  - `.txt` → `content.decode("utf-8")`
  - `.pdf` → `PyPDF2.PdfReader` extracts text page by page
  - `.docx` → `python-docx` reads all paragraph text
- Extracted text is cleaned (whitespace normalisation) then passed to `compute_stats()`

**Libraries:** `react-dropzone`, `axios`, `FastAPI`, `PyPDF2`, `python-docx`

---

## 2. Word & Document Statistics

**What it does:**  
Computes and displays: word count, unique word count, sentence count, paragraph count, character count, average sentence length, reading time, Flesch-Kincaid grade level, Flesch Reading Ease score, lexical diversity, and vocabulary richness.

**How it works:**  
All computed in `text_processor.py → compute_stats()`:
- **Word count** — NLTK `word_tokenize()`, filtered to alphabetic tokens
- **Sentence count** — NLTK `sent_tokenize()` with regex fallback
- **Flesch-Kincaid Grade** — `0.39 × (words/sentences) + 11.8 × (syllables/words) − 15.59`
- **Flesch Reading Ease** — `206.835 − 1.015 × (words/sentences) − 84.6 × (syllables/words)`
- **Syllable count** — custom heuristic: count vowel clusters, subtract silent trailing 'e'
- **Lexical Diversity** — `unique_words / total_words` (Type-Token Ratio)

**Libraries:** `NLTK`, `re`, pure Python math

---

## 3. Word Frequency Analysis

**What it does:**  
Ranks every word by how often it appears. Supports 4 visualisation modes: bar chart, data table (with live search filter), word cloud image, vocabulary treemap.

**How it works:**  
- `get_clean_tokens()` lowercases, removes punctuation, then applies either **lemmatization** (WordNet lemmatizer — maps "running" → "run") or **stemming** (Porter stemmer — cruder, faster)
- Stopwords removed using NLTK's English stopword list
- `word_frequency()` uses `collections.Counter`, adds rank and percentage fields
- Word cloud generated server-side using the `wordcloud` Python library + `matplotlib`, returned as base64 PNG
- Frontend renders bar chart and treemap using `recharts`

**Libraries:** `NLTK` (tokenizer, lemmatizer, stemmer, stopwords), `wordcloud`, `matplotlib`, `recharts`

---

## 4. Sentiment Analysis

**What it does:**  
Classifies the overall document as positive / negative / neutral. Shows polarity (−1 to +1), subjectivity (0 to 1), and breaks down every sentence individually with its own label and score.

**How it works:**  
Uses `TextBlob`, which internally uses a pattern-based sentiment lexicon:
- `blob.sentiment.polarity` — weighted average of word polarity scores
- `blob.sentiment.subjectivity` — proportion of subjective vs objective language
- Each sentence is individually analysed to build the sentence-level breakdown
- Thresholds: polarity > 0.15 → positive, < −0.15 → negative, else neutral

**Libraries:** `TextBlob` (backed by the Pattern library lexicon)

---

## 5. Emotion Detection

**What it does:**  
Detects 8 emotions: joy, sadness, anger, fear, surprise, disgust, trust, anticipation. Displayed as a radar chart and bar breakdown with a dominant emotion highlight.

**How it works:**  
Keyword-matching heuristic in `sentiment.py → analyze_emotions()`:
- Each emotion has a curated keyword list (e.g. joy: "happy", "excited", "delight"…)
- Uses `re.findall` with word-boundary patterns to count hits per 1,000 words
- Score is capped at 100 and normalised by document length to avoid skew in long documents
- Dominant emotion = emotion with the highest normalised score

*Note: This is a lexicon heuristic, not a neural classifier. For production accuracy, a fine-tuned transformer (e.g. `j-hartmann/emotion-english-distilroberta-base`) would be swapped in.*

---

## 6. AI Extractive Summary

**What it does:**  
Produces an executive summary paragraph, a bullet-point list of key sentences, and a ranked list of the most important sentences with relevance scores.

**How it works:**  
Pure extractive summarisation (no generative model required):
1. Score each sentence by counting how many of the top-30 TF-IDF tokens it contains
2. Sort sentences by score, pick top N (proportional to document length)
3. Re-order selected sentences in original document order for coherent reading

This approach is fast, works offline, and requires no API key. It faithfully represents the document without hallucination.

**Libraries:** Pure Python (`collections.Counter`, `re`)

---

## 7. Topic Detection

**What it does:**  
Identifies the main themes/topics in the document and extracts the most statistically significant keywords using TF-IDF.

**How it works:**  
`topics.py → detect_topics()` and `extract_keywords_tfidf()`:
- Document is split into sentence chunks
- `TfidfVectorizer` (scikit-learn) builds a term-document matrix — words that appear often in a chunk but rarely across all chunks get high scores
- Topic labels = top-scoring keywords, capitalised
- Supports bigrams (`ngram_range=(1,2)`) to catch phrases like "machine learning"

**Libraries:** `scikit-learn (TfidfVectorizer)`, `NLTK`

---

## 8. Named Entity Recognition (NER)

**What it does:**  
Extracts real-world named entities — people, organisations, locations, dates, events, products — and counts how often each appears.

**How it works:**  
`topics.py → extract_entities()` uses spaCy's `en_core_web_sm` statistical model:
- Runs the full spaCy pipeline on the document text (capped at 100k chars for performance)
- Groups entities by label (PERSON, ORG, GPE, DATE, etc.)
- Deduplicates with `Counter.most_common()` to surface the top 8 per category
- Falls back to a capitalised-word regex heuristic if spaCy is unavailable

**Libraries:** `spaCy (en_core_web_sm)`

---

## 9. Document DNA Fingerprint

**What it does:**  
A 6-axis radar chart that gives every document a unique "fingerprint" across: Complexity, Technicality, Formality, Readability, Creativity, Emotionality.

**How it works:**  
`style_analyzer.py → compute_document_dna()` derives each axis from observable signals:
- **Complexity** — average word length + Flesch-Kincaid grade
- **Technicality** — ratio of words longer than 8 characters
- **Formality** — inverse of first-person pronoun frequency + passive voice ratio
- **Readability** — Flesch Reading Ease score directly
- **Creativity** — lexical diversity (type-token ratio)
- **Emotionality** — first-person pronoun density

Each dimension is normalised to 0–100 for the radar chart.

**Libraries:** `re`, pure Python + `recharts` RadarChart on frontend

---

## 10. Writing Style Classification

**What it does:**  
Classifies the document's dominant writing style: Academic, Conversational, Technical, Narrative, or Persuasive.

**How it works:**  
`style_analyzer.py → classify_writing_style()` computes style scores from:
- Average word/sentence length
- Passive voice ratio (regex: `(is|are|was|were|been) \w+ed`)
- First-person pronoun frequency
- Technical vocabulary ratio (words > 8 chars)

The style with the highest composite score wins. All five scores are returned for the radar display.

---

## 11. In-Document Search

**What it does:**  
Search for any word or phrase across the entire document. Returns the exact total count, every occurrence with line number + character position, a context snippet with the match highlighted, and a paragraph-level distribution map.

**How it works:**  
`documents.py → search_in_document()` runs entirely in Python:
- `re.finditer(re.escape(query), text, flags)` — supports case-sensitive/insensitive toggle
- For each match: compute line number (`text[:start].count('\n') + 1`) and char offset
- Extract ±100 char context window around each match
- Split document on `\n\n` for paragraph counts
- Results capped at 200 occurrences displayed (full count always shown)

**Libraries:** `re` (Python stdlib)

---

## 12. Quiz Generator (MCQ)

**What it does:**  
Generates multiple-choice questions from the document content. Configurable count (3–30 questions). Each MCQ has 4 options (A/B/C/D), the correct answer, and an explanation. Quiz shows one question at a time, gives instant feedback, then shows a graded score at the end.

**How it works:**  
`question_gen.py → generate_quiz()` uses two strategies:
1. **Definition-based MCQs** — regex patterns detect "X is Y" / "X refers to Y" definitions, uses the definition as the correct answer, and other definitions in the document as distractors
2. **Fill-in-the-blank MCQs** — picks a keyword from TF-IDF, blanks it out in a sentence, uses other keywords as distractors

Frontend quiz engine:
- State machine: `idle → question → answered → next → results`
- Correct option highlighted green, wrong highlighted red
- Explanation panel animates in after answering
- Results screen shows % score, per-question review, confetti on 80%+

**Libraries:** `re`, TF-IDF keywords, `canvas-confetti` (frontend)

---

## 13. Flashcard Generator

**What it does:**  
Generates study flashcards — term/question on the front, definition/context on the back. Two study modes:
- **Flip mode** — 3D card flip animation, mark "Got It" vs "Still Learning", tracks mastery progress
- **Practice mode** — question and answer side by side for quick review

**How it works:**  
`question_gen.py → generate_flashcards()`:
- Extracts definition pairs using the same regex as quiz generation
- Builds context cards by finding the most relevant sentence for each TF-IDF keyword
- Returns cards sorted: definition cards first, then context cards

Frontend flip animation uses `framer-motion` with `rotateY` and `backface-visibility: hidden` for the 3D effect. Known/unknown sets tracked in React state.

---

## 14. AI Insight Generator

**What it does:**  
Synthesises all analysis results into plain-English insights: reading level assessment, vocabulary richness commentary, tone description, content objectivity, dominant style, top topics summary.

**How it works:**  
`insights.py → generate_insights()` takes pre-computed stats, sentiment, topics, style, DNA, and entities as inputs and applies conditional logic to produce natural-language observations:
- Word count → reading time estimate
- Lexical diversity → vocabulary richness comment
- Flesch-Kincaid grade → audience level
- Sentiment label + subjectivity → tone description
- Entity count → proper noun richness

No generative AI required — deterministic rule-based synthesis.

---

## 15. Bias Detection

**What it does:**  
Flags loaded/emotive language and hedging language, provides a bias score (0–100) and level (Low / Moderate / High), and gives a recommendation.

**How it works:**  
`insights.py → analyze_bias()`:
- **Loaded language** — regex matches absolute/emotive words: "clearly", "obviously", "always", "never", "terrible", "amazing", etc.
- **Hedging language** — regex matches uncertainty markers: "perhaps", "might", "suggests", "appears", etc.
- **Bias score** — weighted combination of |polarity|, subjectivity, and loaded word count

---

## 16. Reports Page

**What it does:**  
Allows downloading a full PDF analysis report for any uploaded document.

**How it works:**  
Backend `reports/pdf_generator.py` uses `ReportLab` to compose a multi-page PDF with stats tables, sentiment scores, topic lists, and extracted insights. Returned as a binary blob, downloaded by the browser via `URL.createObjectURL`.

---

## Architecture Overview

```
Browser (React + TypeScript)
        │
        │ HTTP / REST (Axios)
        ▼
FastAPI (Python)
  ├── /api/documents/*   → Upload, CRUD, Search
  ├── /api/analysis/*    → All NLP modules
  └── /api/reports/*     → PDF generation
        │
        │ SQLAlchemy ORM
        ▼
SQLite database (leximind.db)
  ├── documents          → Metadata + extracted text
  ├── flashcards         → Generated flashcards
  └── quiz_questions     → Generated MCQs
```

The architecture is intentionally simple: no message queue, no background tasks, no external AI APIs required. Everything runs locally, making it fully offline-capable.

---

## Performance Notes

- **Large files (>50 MB):** Text extraction with PyPDF2/python-docx is synchronous and can take 5–30 seconds for very large PDFs. A future improvement would be background task processing with Celery.
- **spaCy NER:** Capped at 100,000 characters to avoid memory issues on very large documents.
- **Word cloud:** Generated server-side using matplotlib (Agg backend), no display required.
- **Quiz generation:** Falls back to keyword-based MCQs when the document has few explicit definitions.
