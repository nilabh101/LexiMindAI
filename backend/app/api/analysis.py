"""Analysis endpoints — all NLP modules."""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import asyncio

from app.core.database import get_db
from app.models.document import Document, Analysis
from app.nlp.text_processor import get_clean_tokens, word_frequency, compute_stats
from app.nlp.sentiment import analyze_document_sentiment, analyze_emotions
from app.nlp.topics import detect_topics, extract_keywords_tfidf, extract_entities
from app.nlp.style_analyzer import classify_writing_style, compute_document_dna
from app.nlp.summarizer import generate_summaries
from app.nlp.question_gen import generate_questions, generate_quiz
from app.nlp.insights import generate_insights, analyze_bias
from app.nlp.comparison import compare_documents
from app.services.wordcloud_service import generate_wordcloud_base64, get_wordcloud_data

router = APIRouter(prefix="/analysis", tags=["analysis"])


async def _get_doc_text(doc_id: int, db: AsyncSession) -> tuple:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.extracted_text:
        raise HTTPException(status_code=422, detail="Document text not available")
    return doc, doc.extracted_text


@router.get("/{doc_id}/words")
async def word_analysis(
    doc_id: int,
    top_n: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    doc, text = await _get_doc_text(doc_id, db)
    tokens = get_clean_tokens(text, remove_stopwords=True)
    tokens_with_sw = get_clean_tokens(text, remove_stopwords=False)
    freq = word_frequency(tokens, top_n=top_n)
    freq_with_sw = word_frequency(tokens_with_sw, top_n=top_n)
    return {
        "document_id": doc_id,
        "top_n": top_n,
        "frequency": freq,
        "frequency_with_stopwords": freq_with_sw,
        "total_tokens": len(tokens),
    }


@router.get("/{doc_id}/wordcloud")
async def wordcloud(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    data = get_wordcloud_data(text, top_n=150)
    image_b64 = generate_wordcloud_base64(text)
    return {
        "document_id": doc_id,
        "data": data,
        "image_base64": image_b64,
    }


@router.get("/{doc_id}/sentiment")
async def sentiment_analysis(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    result = analyze_document_sentiment(text)
    return {"document_id": doc_id, **result}


@router.get("/{doc_id}/emotions")
async def emotion_analysis(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    result = analyze_emotions(text)
    return {"document_id": doc_id, **result}


@router.get("/{doc_id}/topics")
async def topic_detection(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    topics = detect_topics(text)
    keywords = extract_keywords_tfidf(text, top_n=20)
    return {"document_id": doc_id, "topics": topics, "keywords": keywords}


@router.get("/{doc_id}/entities")
async def entity_extraction(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    result = extract_entities(text)
    return {"document_id": doc_id, **result}


@router.get("/{doc_id}/style")
async def writing_style(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    result = classify_writing_style(text)
    return {"document_id": doc_id, **result}


@router.get("/{doc_id}/dna")
async def document_dna(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    stats = compute_stats(text)
    result = compute_document_dna(text, stats)
    return {"document_id": doc_id, **result}


@router.get("/{doc_id}/summary")
async def document_summary(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    result = generate_summaries(text)
    return {"document_id": doc_id, **result}


@router.get("/{doc_id}/questions")
async def question_generation(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    result = generate_questions(text)
    return {"document_id": doc_id, **result}


@router.get("/{doc_id}/quiz")
async def quiz_generation(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    result = generate_quiz(text)
    return {"document_id": doc_id, **result}


@router.get("/{doc_id}/insights")
async def ai_insights(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    stats = compute_stats(text)
    sentiment = analyze_document_sentiment(text)
    topics = detect_topics(text)
    style = classify_writing_style(text)
    dna = compute_document_dna(text, stats)
    entities = extract_entities(text)
    insights = generate_insights(stats, sentiment, topics, style, dna, entities)
    return {"document_id": doc_id, "insights": insights}


@router.get("/{doc_id}/bias")
async def bias_detection(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    sentiment = analyze_document_sentiment(text)
    result = analyze_bias(text, sentiment)
    return {"document_id": doc_id, **result}


@router.get("/{doc_id}/full")
async def full_analysis(doc_id: int, db: AsyncSession = Depends(get_db)):
    """Run all analyses and return complete result."""
    doc, text = await _get_doc_text(doc_id, db)
    stats = compute_stats(text)
    sentiment = analyze_document_sentiment(text)
    emotions = analyze_emotions(text)
    topics = detect_topics(text)
    keywords = extract_keywords_tfidf(text, top_n=20)
    entities = extract_entities(text)
    style = classify_writing_style(text)
    dna = compute_document_dna(text, stats)
    summary = generate_summaries(text)
    insights = generate_insights(stats, sentiment, topics, style, dna, entities)
    bias = analyze_bias(text, sentiment)
    freq = word_frequency(get_clean_tokens(text), top_n=50)
    wc_data = get_wordcloud_data(text, top_n=100)

    return {
        "document_id": doc_id,
        "filename": doc.original_filename,
        "stats": stats,
        "sentiment": sentiment,
        "emotions": emotions,
        "topics": {"topics": topics, "keywords": keywords},
        "entities": entities,
        "style": style,
        "dna": dna,
        "summary": summary,
        "insights": insights,
        "bias": bias,
        "word_frequency": freq,
        "wordcloud_data": wc_data,
    }


@router.post("/compare")
async def compare_docs(
    doc_ids: List[int],
    db: AsyncSession = Depends(get_db),
):
    if len(doc_ids) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 document IDs")

    docs_data = []
    for did in doc_ids:
        result = await db.execute(select(Document).where(Document.id == did))
        d = result.scalar_one_or_none()
        if not d:
            raise HTTPException(status_code=404, detail=f"Document {did} not found")
        docs_data.append({"id": str(d.id), "filename": d.original_filename, "text": d.extracted_text or ""})

    result = compare_documents(docs_data)
    return result
