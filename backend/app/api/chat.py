"""AI Chatbot endpoint — uses Google Gemini (free tier) with document context."""
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.models.document import Document
from app.core.config import settings
from app.services.tutor import (
    action_instruction,
    build_student_context,
    describe_student_context,
    fallback_action_reply,
    normalize_action,
    note_sources,
    resolve_action,
)

router = APIRouter(prefix="/chat", tags=["chat"])

GEMINI_API_KEY = settings.GEMINI_API_KEY


class ChatMessage(BaseModel):
    role: str          # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    doc_id: Optional[int] = None
    history: Optional[List[ChatMessage]] = []
    user_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    concept_id: Optional[str] = None
    education_level: Optional[str] = None
    course: Optional[str] = None
    # EXPLAIN | SIMPLIFY | EXAMPLE | HINT | TEST_ME | SIMILAR_QUESTION | EXPLAIN_MISTAKE
    action: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    model: str
    sources: Optional[List[dict]] = None
    action: Optional[str] = None
    actionData: Optional[dict] = None
    studentContext: Optional[dict] = None


def _build_system_prompt(doc_text: Optional[str], doc_name: Optional[str]) -> str:
    base = (
        "You are LexiMind AI Assistant — a helpful, concise document analysis assistant. "
        "Answer questions clearly. If you don't know something, say so honestly. "
        "Keep responses focused and under 300 words unless the user asks for more detail."
    )
    if doc_text:
        # Truncate to ~6000 chars to stay within context limits
        excerpt = doc_text[:6000].replace("\n", " ")
        return (
            f"{base}\n\n"
            f"The user has uploaded a document called '{doc_name}'.\n"
            f"Here is an excerpt from it:\n\n---\n{excerpt}\n---\n\n"
            "Answer questions based on this document when relevant."
        )
    return base


async def _call_gemini(system_prompt: str, history: List[ChatMessage], user_message: str) -> str:
    """Call Google Gemini 1.5 Flash (free tier, no API cost for low usage)."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_prompt,
        )

        # Build conversation history for Gemini
        gemini_history = []
        for msg in history[-6:]:  # keep last 6 turns to stay within limits
            role = "user" if msg.role == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg.content]})

        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(user_message)
        return response.text

    except Exception as e:
        raise RuntimeError(f"Gemini API error: {str(e)}")


def _call_gemini_rest(system_prompt: str, history: List[ChatMessage], user_message: str) -> str:
    """Fallback: call Gemini via REST (no SDK needed)."""
    import httpx
    import json

    contents = []
    for msg in history[-6:]:
        role = "user" if msg.role == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg.content}]})

    contents.append({"role": "user", "parts": [{"text": user_message}]})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 512,
        },
    }

    response = httpx.post(url, json=payload, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Gemini REST error {response.status_code}: {response.text[:200]}")

    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _fallback_response(message: str, doc_text: Optional[str]) -> str:
    """Rule-based fallback when no API key is set."""
    msg = message.lower()

    if doc_text:
        words = doc_text.split()
        word_count = len(words)
        sentences = [s.strip() for s in doc_text.split('.') if len(s.strip()) > 20]

        if any(w in msg for w in ["summarize", "summary", "about", "overview", "what is"]):
            excerpt = ". ".join(sentences[:3]) + "." if sentences else "No text available."
            return f"This document contains {word_count:,} words. Here's a brief overview:\n\n{excerpt}"

        if any(w in msg for w in ["word count", "how many words", "length"]):
            return f"This document contains **{word_count:,} words** across approximately {len(sentences)} sentences."

        if any(w in msg for w in ["topic", "about", "main subject"]):
            # Simple keyword extraction
            from collections import Counter
            import re
            clean = re.sub(r'[^\w\s]', '', doc_text.lower())
            stopwords = {"the","a","an","is","in","it","of","and","to","that","this","was","for","on","are","with","as","at","be","by","from","or","but","not","have","had","has","he","she","they","we","you","i","its","also","been","which","his","her","their","our","were","will","can","do","did","if","so","than","then","when","what","how","who"}
            words_clean = [w for w in clean.split() if w not in stopwords and len(w) > 3]
            common = Counter(words_clean).most_common(5)
            topics = ", ".join(w for w, _ in common)
            return f"The main topics appear to be: **{topics}**."

        return (
            "I can answer questions about this document. Try asking:\n"
            "• 'Summarize this document'\n"
            "• 'What are the main topics?'\n"
            "• 'How many words does it have?'"
        )

    return (
        "I'm LexiMind AI Assistant. Upload a document and I can help you:\n"
        "• Summarize it\n"
        "• Answer questions about it\n"
        "• Explain topics and concepts\n\n"
        "To enable smarter AI responses, add your Gemini API key to the `.env` file as `GEMINI_API_KEY=your_key`."
    )


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Personalized tutor turn: retrieval + student performance context."""

    # Load document context if provided
    doc_text = None
    doc_name = None
    if request.doc_id:
        result = await db.execute(select(Document).where(Document.id == request.doc_id))
        doc = result.scalar_one_or_none()
        if doc:
            doc_text = doc.extracted_text
            doc_name = doc.original_filename

    retrieved = await _retrieve_academic_context(db, request)
    student_context = await build_student_context(db, request.user_id, request.subject_id, request.concept_id)
    action_payload = await resolve_action(db, request.action, request.user_id, request.subject_id, request.concept_id)
    system_prompt = _build_tutor_prompt(doc_text, doc_name, request, retrieved, student_context)
    for note in (action_payload.get("notes") or [])[:2]:
        system_prompt += f"\n\n[stored note] {note.get('title')}\n{(note.get('content') or '')[:800]}"
    sources = list(retrieved.get("sources") or []) if retrieved else []
    sources += note_sources(action_payload.get("notes") or [])
    picked_question = action_payload.get("question")
    if picked_question:
        # Cite the stored question the action is built on — never a fabricated reference.
        entry = {"title": picked_question.get("source"), "type": "QUESTION", "questionId": picked_question.get("id")}
        if picked_question.get("year"):
            entry["year"] = picked_question["year"]
        sources.append(entry)
    action = normalize_action(request.action)

    def respond(reply: str, model: str) -> ChatResponse:
        return ChatResponse(
            reply=reply, model=model, sources=sources,
            action=action, actionData=action_payload or None, studentContext=student_context,
        )

    from app.services.llm import generate_text, provider_status
    status = provider_status()
    if status.get("configured"):
        try:
            result = generate_text(
                _user_prompt(request, action_payload),
                system=system_prompt,
            )
            if result.get("provider") != "fallback" or not GEMINI_API_KEY:
                return respond(result["text"], result.get("provider") or "llm")
        except Exception as e:
            print(f"LLM error: {e}")

    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            try:
                reply = await _async_gemini(system_prompt, request.history or [], request.message)
            except Exception:
                reply = _call_gemini_rest(system_prompt, request.history or [], request.message)
            return respond(reply, "gemini-1.5-flash")
        except Exception as e:
            print(f"Gemini error: {e}")

    # No provider: answer from stored records only.
    reply = fallback_action_reply(request.action, action_payload) or _fallback_response(request.message, doc_text)
    if retrieved and retrieved.get("chunks") and not action_payload.get("question") and not action_payload.get("notes"):
        snippets = "\n\n".join((c.get("text") or "")[:400] for c in retrieved["chunks"][:2])
        reply = (
            "I don't have an LLM provider configured, so this answer is grounded only in retrieved study material:\n\n"
            f"{snippets}\n\n"
            + reply
        )
    return respond(reply, "fallback")


async def _async_gemini(system_prompt: str, history: List[ChatMessage], message: str) -> str:
    """Run Gemini SDK call in a thread pool to avoid blocking the event loop."""
    import asyncio
    return await asyncio.get_event_loop().run_in_executor(
        None, _call_gemini_rest, system_prompt, history, message
    )


def _user_prompt(request: ChatRequest, action_payload: dict) -> str:
    extra = action_instruction(request.action, action_payload or {})
    return f"{extra}\n\nStudent question: {request.message}".strip()


def _build_tutor_prompt(doc_text, doc_name, request: ChatRequest, retrieved: dict,
                        student_context: Optional[dict] = None) -> str:
    base = (
        "You are LexiMind AI Tutor. Answer using ONLY the retrieved academic context when it is present. "
        "If the context is insufficient, say so. Never invent PYQ years, marks, or sources. "
        "Cite page numbers when available."
    )
    profile = []
    if request.education_level:
        profile.append(f"education level: {request.education_level}")
    if request.course:
        profile.append(f"course: {request.course}")
    if request.subject_id:
        profile.append(f"subject: {request.subject_id}")
    if request.concept_id:
        profile.append(f"concept: {request.concept_id}")
    if profile:
        base += "\nStudent context: " + ", ".join(profile)
    if student_context:
        base += (
            "\n\nStudent performance (only make claims supported by this data):\n"
            + describe_student_context(student_context)
        )
    if doc_text:
        excerpt = doc_text[:4000]
        base += f"\n\nActive document '{doc_name}':\n{excerpt}"
    if retrieved:
        for ch in (retrieved.get("chunks") or [])[:5]:
            page = ch.get("page_number")
            base += f"\n\n[notes page {page}]\n{(ch.get('text') or '')[:800]}"
        for q in (retrieved.get("pyqs") or [])[:4]:
            year = q.get("year")
            year_s = str(year) if year is not None else "unknown year"
            base += f"\n\n[PYQ {year_s}]\n{(q.get('question_text') or '')[:500]}"
        for c in (retrieved.get("concepts") or [])[:3]:
            base += f"\n\n[concept] {c.get('canonical_name') or c.get('name')}"
    return base


async def _retrieve_academic_context(db: AsyncSession, request: ChatRequest) -> dict:
    try:
        from sqlalchemy import select as sel
        from app.models.academic import DocumentChunk, Question, AcademicConcept
        from app.services.embeddings import RetrievalService
        chunks = (await db.execute(sel(DocumentChunk).limit(300))).scalars().all()
        questions = (await db.execute(sel(Question).where(Question.source.in_(["PYQ", "DEMO", "UPLOADED"])).limit(150))).scalars().all()
        concepts = (await db.execute(sel(AcademicConcept).limit(150))).scalars().all()
        svc = RetrievalService()
        return svc.retrieve_context(
            request.message,
            chunks=[{"id": c.id, "document_id": c.document_id, "page_number": c.page_number, "section": c.section, "text": c.text, "subject_id": c.subject_id, "concept_id": c.concept_id} for c in chunks],
            questions=[{"question_text": q.question_text, "year": q.year, "source": q.source, "concept_id": q.concept_id} for q in questions],
            concepts=[{"canonical_name": c.canonical_name, "slug": c.slug, "name": c.canonical_name} for c in concepts],
            filters={"subject_id": request.subject_id, "concept_id": request.concept_id},
        )
    except Exception:
        return {}
