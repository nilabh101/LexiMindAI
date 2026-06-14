"""Analysis endpoints — all NLP modules."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.document import Document
from app.nlp.text_processor import get_clean_tokens, word_frequency, compute_stats
from app.nlp.sentiment import analyze_document_sentiment, analyze_emotions
from app.nlp.topics import detect_topics, extract_keywords_tfidf, extract_entities
from app.nlp.style_analyzer import classify_writing_style, compute_document_dna
from app.nlp.summarizer import generate_summaries
from app.nlp.question_gen import generate_questions, generate_quiz, generate_flashcards, generate_quiz_from_multiple
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
    use_stemming: bool = Query(False),
    use_lemmatization: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    doc, text = await _get_doc_text(doc_id, db)
    tokens = get_clean_tokens(text, remove_stopwords=True, use_stemming=use_stemming, use_lemmatization=use_lemmatization)
    tokens_sw = get_clean_tokens(text, remove_stopwords=False, use_stemming=use_stemming, use_lemmatization=use_lemmatization)
    return {
        "document_id": doc_id,
        "top_n": top_n,
        "frequency": word_frequency(tokens, top_n=top_n),
        "frequency_with_stopwords": word_frequency(tokens_sw, top_n=top_n),
        "total_tokens": len(tokens),
    }


@router.get("/{doc_id}/stats")
async def document_stats(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    return {"document_id": doc_id, **compute_stats(text)}


@router.get("/{doc_id}/wordcloud")
async def wordcloud(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    return {
        "document_id": doc_id,
        "data": get_wordcloud_data(text, top_n=150),
        "image_base64": generate_wordcloud_base64(text),
    }


@router.get("/{doc_id}/lexical_diversity")
async def lexical_diversity(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    return {"document_id": doc_id, "lexical_diversity": compute_stats(text).get("lexical_diversity")}


@router.get("/{doc_id}/unique_words")
async def unique_word_count(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    return {"document_id": doc_id, "unique_word_count": compute_stats(text).get("unique_word_count")}


@router.get("/{doc_id}/sentiment")
async def sentiment_analysis(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    return {"document_id": doc_id, **analyze_document_sentiment(text)}


@router.get("/{doc_id}/emotions")
async def emotion_analysis(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    return {"document_id": doc_id, **analyze_emotions(text)}


@router.get("/{doc_id}/topics")
async def topics_endpoint(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    return {
        "document_id": doc_id,
        "topics": detect_topics(text),
        "keywords": extract_keywords_tfidf(text, top_n=20),
    }


@router.get("/{doc_id}/entities")
async def entity_extraction(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    return {"document_id": doc_id, **extract_entities(text)}


@router.get("/{doc_id}/style")
async def writing_style(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    return {"document_id": doc_id, **classify_writing_style(text)}


@router.get("/{doc_id}/dna")
async def document_dna(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    return {"document_id": doc_id, **compute_document_dna(text, compute_stats(text))}


@router.get("/{doc_id}/summary")
async def document_summary(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    return {"document_id": doc_id, **generate_summaries(text)}


@router.get("/{doc_id}/questions")
async def question_generation(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    return {"document_id": doc_id, **generate_questions(text)}


@router.get("/{doc_id}/quiz")
async def quiz_generation(
    doc_id: int,
    num_questions: int = Query(10, ge=3, le=30),
    db: AsyncSession = Depends(get_db),
):
    doc, text = await _get_doc_text(doc_id, db)
    return {"document_id": doc_id, **generate_quiz(text, num_questions=num_questions)}


@router.get("/{doc_id}/flashcards")
async def flashcards_endpoint(
    doc_id: int,
    num_cards: int = Query(15, ge=3, le=40),
    db: AsyncSession = Depends(get_db),
):
    doc, text = await _get_doc_text(doc_id, db)
    return {"document_id": doc_id, **generate_flashcards(text, num_cards=num_cards)}


@router.get("/{doc_id}/insights")
async def ai_insights(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    stats = compute_stats(text)
    sentiment = analyze_document_sentiment(text)
    return {
        "document_id": doc_id,
        "insights": generate_insights(
            stats, sentiment,
            detect_topics(text),
            classify_writing_style(text),
            compute_document_dna(text, stats),
            extract_entities(text),
        ),
    }


@router.get("/{doc_id}/bias")
async def bias_detection(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    return {"document_id": doc_id, **analyze_bias(text, analyze_document_sentiment(text))}


@router.get("/{doc_id}/full")
async def full_analysis(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc, text = await _get_doc_text(doc_id, db)
    stats = compute_stats(text)
    sentiment = analyze_document_sentiment(text)
    topics = detect_topics(text)
    style = classify_writing_style(text)
    dna = compute_document_dna(text, stats)
    entities = extract_entities(text)
    return {
        "document_id": doc_id,
        "filename": doc.original_filename,
        "stats": stats,
        "sentiment": sentiment,
        "emotions": analyze_emotions(text),
        "topics": {"topics": topics, "keywords": extract_keywords_tfidf(text, top_n=20)},
        "entities": entities,
        "style": style,
        "dna": dna,
        "summary": generate_summaries(text),
        "insights": generate_insights(stats, sentiment, topics, style, dna, entities),
        "bias": analyze_bias(text, sentiment),
        "word_frequency": word_frequency(get_clean_tokens(text), top_n=50),
        "wordcloud_data": get_wordcloud_data(text, top_n=100),
    }


@router.post("/multi-quiz")
async def multi_document_quiz(
    doc_ids: List[int],
    num_questions: int = Query(20, ge=5, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Generate a combined quiz from multiple documents."""
    if len(doc_ids) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 document IDs")
    if len(doc_ids) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 documents at once")

    texts_with_names = []
    for did in doc_ids:
        result = await db.execute(select(Document).where(Document.id == did))
        d = result.scalar_one_or_none()
        if not d:
            raise HTTPException(status_code=404, detail=f"Document {did} not found")
        if not d.extracted_text:
            continue
        texts_with_names.append({"name": d.original_filename, "text": d.extracted_text})

    if not texts_with_names:
        raise HTTPException(status_code=422, detail="No text available in the selected documents")

    result = generate_quiz_from_multiple(texts_with_names, num_questions=num_questions)
    return {"document_ids": doc_ids, **result}


@router.post("/compare")
async def compare_docs(doc_ids: List[int], db: AsyncSession = Depends(get_db)):
    if len(doc_ids) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 document IDs")
    docs_data = []
    for did in doc_ids:
        result = await db.execute(select(Document).where(Document.id == did))
        d = result.scalar_one_or_none()
        if not d:
            raise HTTPException(status_code=404, detail=f"Document {did} not found")
        docs_data.append({"id": str(d.id), "filename": d.original_filename, "text": d.extracted_text or ""})
    return compare_documents(docs_data)
