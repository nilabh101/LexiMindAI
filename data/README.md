# LexiMind AI — Academic Data Directory

This directory holds all local academic PDFs and processed output.
**This entire directory is gitignored.** Never commit real academic files.

---

## Directory Structure

```
data/
├── raw/
│   ├── pyqs/          ← Previous Year Question papers (PDF)
│   ├── notes/         ← Study notes / lecture notes (PDF, DOCX, TXT)
│   ├── question_banks/ ← Question banks (PDF)
│   └── reference/     ← Reference material (PDF)
│
├── processed/         ← Auto-generated output (chunked, extracted)
├── exports/           ← JSONL dataset exports for training
└── manifests/         ← Ingestion manifest JSON files
```

---

## How to Ingest PDFs

### Single file
```bash
cd backend
python -m app.scripts.ingest_documents --file "../data/raw/pyqs/2025_maths.pdf" \
  --subject-id em1-btech --document-type PYQ --year 2025
```

### Entire directory
```bash
cd backend
python -m app.scripts.ingest_documents --path "../data/raw/pyqs/" \
  --subject-id em1-btech --document-type PYQ
```

### All raw files (auto-classify)
```bash
cd backend
python -m app.scripts.ingest_documents --path "../data/raw/"
```

---

## Metadata You Can Provide

| Flag               | Values                          | Default      |
|--------------------|---------------------------------|--------------|
| `--subject-id`     | em1-btech, cp1-btech, ...       | auto-detect  |
| `--document-type`  | PYQ, STUDY_NOTES, QUESTION_BANK, REFERENCE | auto |
| `--education-level`| COLLEGE, SCHOOL                 | COLLEGE      |
| `--course`         | B.Tech CSE, BCA, ...            | —            |
| `--year`           | 2024, 2025, ...                 | null         |
| `--semester`       | 1, 2, 3, ...                    | null         |

If metadata is missing the classifier will attempt to detect it.
Low-confidence results are marked `NEEDS_REVIEW`.

---

## Duplicate Detection

The ingestion script computes a SHA-256 hash of each file.
If the same file is submitted twice, it is skipped with a `DUPLICATE` report.

---

## Dataset Export

```bash
cd backend
python -m app.scripts.export_dataset --output "../data/exports/dataset_v1.jsonl"
```

Only `APPROVED` questions are exported.
Each record contains: question, concept, subject, difficulty, question_type, source_type, year.

---

## What NOT to put here

- Real student personal data
- API keys or tokens
- Model weights or embeddings
- Any file you don't own or have rights to process
