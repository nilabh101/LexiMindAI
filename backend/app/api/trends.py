"""Trend analysis across multiple documents."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models.document import Document
from app.nlp.text_processor import get_clean_tokens, compute_stats
from app.nlp.sentiment import analyze_sentiment_text
from app.nlp.topics import detect_topics
from collections import Counter

router = APIRouter(prefix="/trends", tags=["trends"])


@router.post("/analyze")
async def trend_analysis(
    doc_ids: List[int],
    db: AsyncSession = Depends(get_db),
):
    if len(doc_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 documents for trend analysis")

    docs_data = []
    for did in doc_ids:
        result = await db.execute(
            select(Document).where(Document.id == did)
        )
        d = result.scalar_one_or_none()
        if not d:
            raise HTTPException(status_code=404, detail=f"Document {did} not found")
        docs_data.append(d)

    # Sort by upload date
    docs_data.sort(key=lambda d: d.upload_date)

    keyword_trends = []
    topic_trends = []
    sentiment_trends = []

    # Collect all top keywords across docs
    all_token_counters = []
    for d in docs_data:
        text = d.extracted_text or ""
        tokens = get_clean_tokens(text, remove_stopwords=True)
        counter = Counter(tokens)
        all_token_counters.append(counter)

    # Global top keywords
    global_counter: Counter = Counter()
    for c in all_token_counters:
        global_counter.update(c)
    top_keywords = [w for w, _ in global_counter.most_common(10)]

    for i, d in enumerate(docs_data):
        text = d.extracted_text or ""
        sentiment = analyze_sentiment_text(text)
        topics = detect_topics(text)
        stats = compute_stats(text)
        counter = all_token_counters[i]
        total = sum(counter.values()) or 1

        sentiment_trends.append({
            "document": d.original_filename,
            "date": d.upload_date.isoformat(),
            "polarity": sentiment["polarity"],
            "subjectivity": sentiment["subjectivity"],
            "label": sentiment["label"],
            "word_count": stats["word_count"],
        })

        topic_trend = {
            "document": d.original_filename,
            "date": d.upload_date.isoformat(),
        }
        for t in topics["topics"][:5]:
            topic_trend[t["topic"]] = t["score"]
        topic_trends.append(topic_trend)

        kw_row = {
            "document": d.original_filename,
            "date": d.upload_date.isoformat(),
        }
        for kw in top_keywords:
            kw_row[kw] = round(counter.get(kw, 0) / total * 1000, 2)
        keyword_trends.append(kw_row)

    return {
        "documents": [d.original_filename for d in docs_data],
        "top_keywords": top_keywords,
        "keyword_trends": keyword_trends,
        "topic_trends": topic_trends,
        "sentiment_trends": sentiment_trends,
    }
