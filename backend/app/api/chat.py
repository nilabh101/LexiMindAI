"""AI Chatbot endpoint — Phase 3: student_context + action-based system prompts."""
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.core.database import get_db
from app.models.document import Document
from app.core.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])

GEMINI_API_KEY = settings.GEMINI_API_KEY


# ── Schemas ────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str      # "user" or "assistant"
    content: str


class StudentContext(BaseModel):
    mastery_score: Optional[float] = None   # 0–100
    mastery_state: Optional[str] = None     # MasteryState value
    weak_concepts: Optional[List[str]] = []
    recent_mistakes: Optional[List[Dict[str, Any]]] = []


class ChatRequest(BaseModel):
    message: str
    doc_id: Optional[int] = None
    history: Optional[List[ChatMessage]] = []
    subject_id: Optional[str] = None
    concept_id: Optional[str] = None
    education_level: Optional[str] = None
    course: Optional[str] = None
    action: Optional[str] = None  # explain|simplify|example|hint|test|similar|mistake
    student_context: Optional[StudentContext] = None   # Phase 3 addition
    user_id: Optional[str] = None  # for personalised context lookup


class ChatResponse(BaseModel):
    reply: str
    model: str
    sources: Optional[List[dict]] = None
    fallback: bool = False


# ── System prompt builder ──────────────────────────────────────────────────────

def _build_tutor_prompt(
    doc_text: Optional[str],
    doc_name: Optional[str],
    request: ChatRequest,
    retrieved: dict,
) -> str:
    base = (
        "You are LexiMind AI Tutor — an expert academic assistant. "
        "Answer ONLY using the retrieved academic context when it is present. "
        "If the context is insufficient, say so honestly. "
        "Never invent PYQ years, page numbers, marks, or source titles. "
        "Cite page numbers and document names when they appear in the context."
    )

    # Personalise based on mastery state (Phase 3)
    sc = request.student_context
    if sc and sc.mastery_state:
        state = sc.mastery_state.upper()
        if state in ("VERY_WEAK", "WEAK"):
            base += (
                "\n\nThis student is at an early stage with this concept. "
                "Explain from first principles using simple language. "
                "Avoid jargon not already introduced. "
                "Focus on building intuition before formulas."
            )
        elif state == "DEVELOPING":
            base += (
                "\n\nThis student has basic understanding. "
                "Reinforce core understanding with worked examples. "
                "Point out common mistakes."
            )
        elif state in ("PROFICIENT", "MASTERED"):
            base += (
                "\n\nThis student has strong understanding. "
                "Focus on advanced applications and exam-style questions. "
                "Challenge them with harder variations."
            )

    if sc and sc.weak_concepts:
        base += f"\n\nStudent's weak areas: {', '.join(sc.weak_concepts[:5])}."

    if sc and sc.recent_mistakes:
        mistake = sc.recent_mistakes[0]
        base += (
            f"\n\nRecent mistake: question '{str(mistake.get('question_text', ''))[:200]}', "
            f"student answered '{mistake.get('selected_answer', '')}', "
            f"correct answer: '{mistake.get('correct_answer', '')}'."
        )

    # Academic profile
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
        base += "\nStudent profile: " + ", ".join(profile)

    # Document context
    if doc_text:
        excerpt = doc_text[:4000]
        base += f"\n\nActive document '{doc_name}':\n{excerpt}"

    # Retrieved academic context
    if retrieved:
        for ch in (retrieved.get("chunks") or [])[:5]:
            page = ch.get("page_number")
            doc_name_chunk = ch.get("document_name") or "Study Notes"
            base += (
                f"\n\n[Source: {doc_name_chunk}, page {page}]\n"
                f"{(ch.get('text') or '')[:800]}"
            )
        for q in (retrieved.get("pyqs") or [])[:4]:
            year = q.get("year")
            year_s = str(year) if year is not None else "unknown year"
            base += f"\n\n[PYQ {year_s}]\n{(q.get('question_text') or '')[:500]}"
        for c in (retrieved.get("concepts") or [])[:3]:
            base += f"\n\n[Concept] {c.get('canonical_name') or c.get('name')}"

    return base


def _user_prompt(request: ChatRequest) -> str:
    action = (request.action or "").lower()
    sc = request.student_context

    guides: Dict[str, str] = {
        "explain":   "Explain this concept clearly and thoroughly.",
        "simplify":  "Simplify the explanation for a beginner.",
        "example":   "Give a clear worked example.",
        "hint":      "Give a helpful hint — not the full solution.",
        "test":      "Ask one short test question about this concept.",
        "similar":   "Find and present a similar question from the retrieved study material (PYQs preferred).",
        "mistake":   (
            "Explain the student's most recent mistake using ONLY the correct answer and question text "
            "from the retrieved context. Do not fabricate explanation if context is missing."
        ) if (sc and sc.recent_mistakes) else (
            "No mistake record is available for this concept."
        ),
    }
    extra = guides.get(action, "")
    return f"{extra}\n\nStudent question: {request.message}".strip()


# ── Gemini callers ────────────────────────────────────────────────────────────

def _call_gemini_rest(system_prompt: str, history: List[ChatMessage], user_message: str) -> str:
    """Call Gemini via REST (no SDK required)."""
    import httpx, json
    contents = []
    for msg in history[-6:]:
        role = "user" if msg.role == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg.content}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
    }
    response = httpx.post(url, json=payload, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Gemini REST error {response.status_code}: {response.text[:300]}")
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


async def _async_gemini(system_prompt: str, history: List[ChatMessage], message: str) -> str:
    import asyncio
    return await asyncio.get_event_loop().run_in_executor(
        None, _call_gemini_rest, system_prompt, history, message
    )


def _fallback_response(message: str, retrieved: dict) -> str:
    """Assemble a useful fallback from retrieved academic context (no LLM)."""
    chunks = (retrieved or {}).get("chunks") or []
    if chunks:
        snippets = "\n\n".join((c.get("text") or "")[:400] for c in chunks[:3])
        return (
            "[AI provider unavailable — showing retrieved study material]\n\n"
            + snippets
        )
    return (
        "I don't have an AI provider configured. "
        "Please add GEMINI_API_KEY to backend/.env to enable AI responses.\n\n"
        "I can still help with document analysis and quiz generation from your uploaded material."
    )


# ── Context retrieval ─────────────────────────────────────────────────────────

async def _retrieve_academic_context(db: AsyncSession, request: ChatRequest) -> dict:
    try:
        from app.models.academic import DocumentChunk, Question, AcademicConcept
        from app.services.embeddings import RetrievalService

        chunks = (await db.execute(
            select(DocumentChunk).limit(300)
        )).scalars().all()
        questions = (await db.execute(
            select(Question).where(
                Question.source.in_(["PYQ", "DEMO", "UPLOADED"])
            ).limit(150)
        )).scalars().all()
        concepts = (await db.execute(select(AcademicConcept).limit(150))).scalars().all()

        # Enrich chunks with document name
        from app.models.document import Document as Doc
        doc_ids = list({c.document_id for c in chunks if c.document_id})
        doc_name_map: Dict[int, str] = {}
        if doc_ids:
            doc_rows = (await db.execute(
                select(Doc).where(Doc.id.in_(doc_ids))
            )).scalars().all()
            doc_name_map = {d.id: (d.original_filename or d.filename or "Document") for d in doc_rows}

        svc = RetrievalService()
        result = svc.retrieve_context(
            request.message,
            chunks=[{
                "id": c.id,
                "document_id": c.document_id,
                "page_number": c.page_number,
                "section": c.section,
                "text": c.text,
                "subject_id": c.subject_id,
                "concept_id": c.concept_id,
                "document_name": doc_name_map.get(c.document_id, ""),
            } for c in chunks],
            questions=[{
                "question_text": q.question_text,
                "year": q.year,
                "source": q.source,
                "concept_id": q.concept_id,
            } for q in questions],
            concepts=[{
                "canonical_name": c.canonical_name,
                "slug": c.slug,
                "name": c.canonical_name,
            } for c in concepts],
            filters={
                "subject_id": request.subject_id,
                "concept_id": request.concept_id,
            },
        )
        # Build source list for response
        sources = []
        for ch in (result.get("chunks") or [])[:5]:
            src = {
                "document_name": ch.get("document_name") or "Study Notes",
                "page_number": ch.get("page_number"),
            }
            sources.append(src)
        for q in (result.get("pyqs") or [])[:3]:
            if q.get("year"):
                sources.append({"document_name": "PYQ", "year": q["year"]})
        result["sources"] = sources
        return result
    except Exception as e:
        print(f"[chat] context retrieval error: {e}")
        return {}


# ── Main endpoint ─────────────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """AI Tutor endpoint with academic context retrieval and student mastery personalisation."""

    # Load document context if provided
    doc_text = None
    doc_name = None
    if request.doc_id:
        result = await db.execute(select(Document).where(Document.id == request.doc_id))
        doc = result.scalar_one_or_none()
        if doc:
            doc_text = doc.extracted_text
            doc_name = doc.original_filename

    # Retrieve academic context
    retrieved = await _retrieve_academic_context(db, request)
    sources = retrieved.get("sources") if retrieved else None

    system_prompt = _build_tutor_prompt(doc_text, doc_name, request, retrieved)
    user_prompt = _user_prompt(request)

    # Try LLM service (from llm.py provider abstraction)
    from app.services.llm import generate_text, provider_status
    status = provider_status()
    if status.get("configured"):
        try:
            result = generate_text(user_prompt, system=system_prompt)
            if result.get("provider") != "fallback":
                return ChatResponse(
                    reply=result["text"],
                    model=result.get("provider") or "llm",
                    sources=sources,
                )
        except Exception as e:
            print(f"[chat] LLM service error: {e}")

    # Direct Gemini fallback
    if GEMINI_API_KEY and GEMINI_API_KEY.startswith("AIza"):
        try:
            reply = await _async_gemini(system_prompt, request.history or [], user_prompt)
            return ChatResponse(reply=reply, model="gemini-1.5-flash", sources=sources)
        except Exception as e:
            print(f"[chat] Gemini direct error: {e}")

    # Final fallback: retrieved context only
    reply = _fallback_response(request.message, retrieved)
    return ChatResponse(reply=reply, model="fallback", sources=sources, fallback=True)
