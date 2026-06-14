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

router = APIRouter(prefix="/chat", tags=["chat"])

GEMINI_API_KEY = settings.GEMINI_API_KEY


class ChatMessage(BaseModel):
    role: str          # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    doc_id: Optional[int] = None
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    reply: str
    model: str


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
    """Chat with AI about a document or general questions."""

    # Load document context if provided
    doc_text = None
    doc_name = None
    if request.doc_id:
        result = await db.execute(select(Document).where(Document.id == request.doc_id))
        doc = result.scalar_one_or_none()
        if doc:
            doc_text = doc.extracted_text
            doc_name = doc.original_filename

    system_prompt = _build_system_prompt(doc_text, doc_name)

    # Try Gemini if API key is set
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            # Try SDK first, then REST
            try:
                reply = await _async_gemini(system_prompt, request.history or [], request.message)
            except Exception:
                reply = _call_gemini_rest(system_prompt, request.history or [], request.message)
            return ChatResponse(reply=reply, model="gemini-1.5-flash")
        except Exception as e:
            # Fall through to fallback
            print(f"Gemini error: {e}")

    # Fallback: rule-based response
    reply = _fallback_response(request.message, doc_text)
    return ChatResponse(reply=reply, model="fallback")


async def _async_gemini(system_prompt: str, history: List[ChatMessage], message: str) -> str:
    """Run Gemini SDK call in a thread pool to avoid blocking the event loop."""
    import asyncio
    return await asyncio.get_event_loop().run_in_executor(
        None, _call_gemini_rest, system_prompt, history, message
    )
