"""PDF report generation endpoint."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.document import Document
from app.nlp.text_processor import compute_stats, get_clean_tokens, word_frequency
from app.nlp.sentiment import analyze_document_sentiment
from app.nlp.topics import detect_topics, extract_entities
from app.nlp.style_analyzer import classify_writing_style, compute_document_dna
from app.nlp.summarizer import generate_summaries
from app.nlp.insights import generate_insights, analyze_bias
from app.reports.pdf_generator import generate_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{doc_id}/pdf")
async def download_pdf_report(doc_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.extracted_text:
        raise HTTPException(status_code=422, detail="Document text not available")

    text = doc.extracted_text
    stats = compute_stats(text)
    sentiment = analyze_document_sentiment(text)
    topics = detect_topics(text)
    entities = extract_entities(text)
    style = classify_writing_style(text)
    dna = compute_document_dna(text, stats)
    summary = generate_summaries(text)
    insights = generate_insights(stats, sentiment, topics, style, dna, entities)
    freq = word_frequency(get_clean_tokens(text), top_n=50)

    pdf_bytes = generate_report(
        filename=doc.original_filename,
        stats=stats,
        sentiment=sentiment,
        topics=topics,
        style=style,
        dna=dna,
        insights=insights,
        summary=summary,
        word_freq=freq,
    )

    safe_name = doc.original_filename.replace(" ", "_").replace(".txt", "").replace(".pdf", "")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="LexiMind_Report_{safe_name}.pdf"'
        },
    )
