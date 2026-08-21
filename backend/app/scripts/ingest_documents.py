"""
Phase 4: Bulk Academic Document Ingestion CLI.

Usage:
    # Single file
    python -m app.scripts.ingest_documents --file "../data/raw/pyqs/2025_maths.pdf"

    # Directory
    python -m app.scripts.ingest_documents --path "../data/raw/pyqs/"

    # All raw data
    python -m app.scripts.ingest_documents --path "../data/raw/"

Options:
    --subject-id      em1-btech | cp1-btech | ...
    --document-type   PYQ | STUDY_NOTES | QUESTION_BANK | REFERENCE
    --education-level COLLEGE | SCHOOL
    --course          "B.Tech CSE"
    --year            2025
    --semester        1
    --dry-run         Scan files but do not ingest (reports duplicates, formats)
"""
import argparse
import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Ensure backend/ is on path when running as module
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}
MANIFEST_DIR = Path(__file__).resolve().parents[4] / "data" / "manifests"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(manifest_path: Path) -> dict:
    if manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)
    return {"ingested": {}}


def save_manifest(manifest_path: Path, manifest: dict) -> None:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)


def discover_files(path: Path) -> list[Path]:
    if path.is_file():
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            return [path]
        print(f"[SKIP] Unsupported extension: {path.suffix}")
        return []
    return sorted(
        p for p in path.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )


async def ingest_file(
    file_path: Path,
    subject_id: Optional[str],
    document_type: Optional[str],
    education_level: str,
    course: Optional[str],
    year: Optional[int],
    semester: Optional[str],
    manifest: dict,
    dry_run: bool,
) -> dict:
    """Process a single file through the Phase 2 pipeline. Returns result dict."""
    content_hash = sha256_file(file_path)

    # Duplicate check
    if content_hash in manifest["ingested"]:
        existing = manifest["ingested"][content_hash]
        return {
            "file": str(file_path),
            "status": "DUPLICATE",
            "reason": f"Already ingested as document_id={existing.get('document_id')} on {existing.get('processed_at')}",
            "hash": content_hash,
        }

    if dry_run:
        return {
            "file": str(file_path),
            "status": "DRY_RUN",
            "hash": content_hash,
            "size_kb": round(file_path.stat().st_size / 1024, 1),
        }

    try:
        # Import here to avoid slow startup when just showing --help
        from app.core.database import AsyncSessionLocal, init_db
        from app.models.document import Document
        from app.services.pipeline import process_document_by_id
        from sqlalchemy import select

        # Save file to uploads directory
        uploads_dir = Path(__file__).resolve().parents[3] / "uploads"
        uploads_dir.mkdir(exist_ok=True)

        import shutil
        dest_filename = f"{content_hash[:8]}_{file_path.name}"
        dest = uploads_dir / dest_filename
        if not dest.exists():
            shutil.copy2(file_path, dest)

        file_type = file_path.suffix.lstrip(".").lower()

        async with AsyncSessionLocal() as db:
            # Create Document record
            doc = Document(
                filename=dest_filename,
                original_filename=file_path.name,
                file_type=file_type,
                file_size=file_path.stat().st_size,
                status="UPLOADED",
                subject_id=subject_id,
                user_document_type=document_type,
                education_level=education_level,
                course=course,
                semester=str(semester) if semester else None,
            )
            db.add(doc)
            await db.flush()
            doc_id = doc.id
            await db.commit()

        # Run pipeline in background (same as API upload)
        await process_document_by_id(doc_id)

        # Read result
        async with AsyncSessionLocal() as db:
            result_doc = (await db.execute(
                select(Document).where(Document.id == doc_id)
            )).scalar_one_or_none()

            if result_doc:
                status = result_doc.status
                error = result_doc.error_message
            else:
                status = "FAILED"
                error = "Document record not found after processing"

        manifest["ingested"][content_hash] = {
            "document_id": doc_id,
            "filename": file_path.name,
            "subject_id": subject_id,
            "document_type": document_type,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
        }

        return {
            "file": str(file_path),
            "status": status,
            "document_id": doc_id,
            "hash": content_hash,
            "error": error,
        }

    except Exception as exc:
        import traceback
        traceback.print_exc()
        return {
            "file": str(file_path),
            "status": "FAILED",
            "error": str(exc),
            "hash": content_hash,
        }


async def run_ingestion(args: argparse.Namespace) -> None:
    from app.core.database import init_db
    if not args.dry_run:
        await init_db()

    manifest_path = MANIFEST_DIR / "ingestion_manifest.json"
    manifest = load_manifest(manifest_path)

    # Discover files
    target = Path(args.file) if args.file else Path(args.path)
    files = discover_files(target)

    if not files:
        print(f"No supported files found in: {target}")
        return

    print(f"\nFound {len(files)} file(s) to process.\n")

    results = {"SUCCESS": [], "FAILED": [], "DUPLICATE": [], "SKIPPED": [], "DRY_RUN": []}

    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {f.name} ...", end=" ", flush=True)
        result = await ingest_file(
            file_path=f,
            subject_id=args.subject_id,
            document_type=args.document_type,
            education_level=args.education_level or "COLLEGE",
            course=args.course,
            year=args.year,
            semester=args.semester,
            manifest=manifest,
            dry_run=args.dry_run,
        )
        status = result["status"]
        print(status)
        if result.get("error"):
            print(f"    └─ Error: {result['error']}")
        results.get(status, results["SKIPPED"]).append(result)

    if not args.dry_run:
        save_manifest(manifest_path, manifest)

    # Summary
    print("\n" + "═" * 50)
    print("INGESTION SUMMARY")
    print("═" * 50)
    for status, items in results.items():
        if items:
            print(f"  {status:12} {len(items)} file(s)")
    print("═" * 50)

    if not args.dry_run:
        print(f"\nManifest saved: {manifest_path}")

    # Data quality report
    if results["SUCCESS"]:
        print("\nDATA QUALITY NOTE:")
        print("  Run GET /api/review/questions to see low-confidence items needing review.")
        print("  Run GET /api/review/concepts   to see concepts needing verification.")


def main():
    parser = argparse.ArgumentParser(description="LexiMind AI — Bulk Academic Document Ingestion")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="Path to a single PDF/TXT/DOCX file")
    source.add_argument("--path", help="Path to a directory of files")

    parser.add_argument("--subject-id",      default=None, help="e.g. em1-btech")
    parser.add_argument("--document-type",   default=None, choices=["PYQ", "STUDY_NOTES", "QUESTION_BANK", "REFERENCE"])
    parser.add_argument("--education-level", default="COLLEGE", choices=["COLLEGE", "SCHOOL"])
    parser.add_argument("--course",          default=None, help='e.g. "B.Tech CSE"')
    parser.add_argument("--year",            type=int, default=None, help="Academic year (for PYQs)")
    parser.add_argument("--semester",        default=None, help="Semester number")
    parser.add_argument("--dry-run",         action="store_true", help="Scan only, do not ingest")

    args = parser.parse_args()
    asyncio.run(run_ingestion(args))


if __name__ == "__main__":
    main()
