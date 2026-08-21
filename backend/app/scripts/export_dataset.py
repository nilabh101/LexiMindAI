"""
Phase 4: Dataset Export CLI — exports APPROVED questions as JSONL.

Usage:
    python -m app.scripts.export_dataset --output "../data/exports/dataset_v1.jsonl"
    python -m app.scripts.export_dataset --output "../data/exports/dataset_v1.jsonl" --subject-id em1-btech

Each JSONL record:
{
  "question": "...",
  "concept": "...",
  "subject": "...",
  "difficulty": "...",
  "question_type": "...",
  "source_type": "PYQ",
  "year": 2025,
  "options": [...],
  "answer": "..."
}

Only APPROVED questions are exported. No user data included.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


async def run_export(args: argparse.Namespace) -> None:
    from app.core.database import init_db, AsyncSessionLocal
    from app.models.academic import Question, AcademicConcept
    from sqlalchemy import select

    await init_db()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    async with AsyncSessionLocal() as db:
        stmt = select(Question).where(Question.review_status == "APPROVED")
        if args.subject_id:
            stmt = stmt.where(Question.subject_id == args.subject_id)
        if args.source:
            stmt = stmt.where(Question.source == args.source.upper())

        questions = (await db.execute(stmt)).scalars().all()

        # Concept name lookup
        concept_slugs = list({q.concept_id for q in questions if q.concept_id})
        concept_map: dict[str, str] = {}
        if concept_slugs:
            c_rows = (await db.execute(
                select(AcademicConcept).where(AcademicConcept.slug.in_(concept_slugs))
            )).scalars().all()
            concept_map = {c.slug: c.canonical_name for c in c_rows}

        records_written = 0
        with open(output_path, "w", encoding="utf-8") as f:
            for q in questions:
                record = {
                    "question": q.question_text,
                    "concept_id": q.concept_id,
                    "concept": concept_map.get(q.concept_id or "", q.concept_id or ""),
                    "subject": q.subject_id,
                    "chapter": q.chapter_id,
                    "difficulty": q.difficulty,
                    "question_type": q.question_type,
                    "source_type": q.source,
                    "year": q.year,
                    "marks": q.marks,
                    "options": q.options,
                    "answer": q.answer,
                    "explanation": q.explanation,
                    "confidence": q.confidence,
                    "is_demo": q.is_demo,
                }
                # Remove None values to keep JSONL clean
                record = {k: v for k, v in record.items() if v is not None}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                records_written += 1

    print(f"\nExported {records_written} records to: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")

    # Dataset version record
    version_path = output_path.parent / "dataset_versions.json"
    versions = []
    if version_path.exists():
        with open(version_path) as f:
            versions = json.load(f)

    from datetime import datetime, timezone
    versions.append({
        "file": output_path.name,
        "records": records_written,
        "subject_filter": args.subject_id,
        "source_filter": args.source,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    })
    with open(version_path, "w") as f:
        json.dump(versions, f, indent=2, default=str)
    print(f"Version record updated: {version_path}")


def main():
    parser = argparse.ArgumentParser(description="LexiMind AI — Export Dataset as JSONL")
    parser.add_argument("--output", required=True, help="Output .jsonl file path")
    parser.add_argument("--subject-id", default=None, help="Filter by subject (e.g. em1-btech)")
    parser.add_argument("--source",     default=None, help="Filter by source: PYQ|UPLOADED|DEMO|PREMADE")
    args = parser.parse_args()
    asyncio.run(run_export(args))


if __name__ == "__main__":
    main()
