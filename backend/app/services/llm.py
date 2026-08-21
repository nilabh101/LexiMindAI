"""LLM provider abstraction. Keys stay on the backend only."""
from typing import Dict, List, Optional
import httpx

from app.core.config import settings


def provider_status() -> Dict:
    provider = (settings.LLM_PROVIDER or "gemini").lower()
    configured = False
    if provider == "gemini":
        configured = bool(settings.GEMINI_API_KEY.strip())
    elif provider in {"openai", "openai-compatible"}:
        configured = bool(settings.OPENAI_API_KEY.strip())
    elif provider in {"huggingface", "hf"}:
        configured = bool(settings.HF_TOKEN.strip())
    else:
        configured = False
    return {
        "provider": provider,
        "configured": configured,
        "available": configured,
        "fallback": "local" if not configured else None,
    }


def generate_text(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 700,
) -> Dict:
    status = provider_status()
    if not status["configured"]:
        return {
            "text": _local_fallback(prompt),
            "provider": "fallback",
            "error": None,
        }
    provider = status["provider"]
    try:
        if provider == "gemini":
            return {"text": _gemini(prompt, system, max_tokens), "provider": "gemini", "error": None}
        if provider in {"openai", "openai-compatible"}:
            return {"text": _openai(prompt, system, max_tokens), "provider": "openai", "error": None}
        if provider in {"huggingface", "hf"}:
            return {"text": _huggingface(prompt, system, max_tokens), "provider": "huggingface", "error": None}
        return {"text": _local_fallback(prompt), "provider": "fallback", "error": f"Unknown provider {provider}"}
    except Exception as exc:
        return {
            "text": _local_fallback(prompt),
            "provider": "fallback",
            "error": str(exc)[:240],
        }


def _gemini(prompt: str, system: Optional[str], max_tokens: int) -> str:
    key = settings.GEMINI_API_KEY
    model = settings.GEMINI_MODEL or "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    contents = []
    if system:
        contents.append({"role": "user", "parts": [{"text": f"System instructions:\n{system}"}]})
        contents.append({"role": "model", "parts": [{"text": "Understood."}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    payload = {
        "contents": contents,
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": max_tokens},
    }
    response = httpx.post(url, json=payload, timeout=45)
    if response.status_code != 200:
        raise RuntimeError(f"Gemini error {response.status_code}")
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _openai(prompt: str, system: Optional[str], max_tokens: int) -> str:
    url = settings.OPENAI_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}
    messages: List[Dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": settings.OPENAI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.4}
    response = httpx.post(url, headers=headers, json=payload, timeout=45)
    if response.status_code != 200:
        raise RuntimeError(f"OpenAI error {response.status_code}")
    return response.json()["choices"][0]["message"]["content"]


def _huggingface(prompt: str, system: Optional[str], max_tokens: int) -> str:
    url = f"https://api-inference.huggingface.co/models/{settings.HF_MODEL}"
    headers = {"Authorization": f"Bearer {settings.HF_TOKEN}"}
    full = f"{system}\n\n{prompt}" if system else prompt
    response = httpx.post(url, headers=headers, json={"inputs": full, "parameters": {"max_new_tokens": max_tokens}}, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"Hugging Face error {response.status_code}")
    data = response.json()
    if isinstance(data, list) and data:
        return data[0].get("generated_text") or str(data[0])
    if isinstance(data, dict):
        return data.get("generated_text") or data.get("error") or str(data)
    return str(data)


def _local_fallback(prompt: str) -> str:
    return (
        "No LLM provider is configured, so this is a local fallback — not a generated analysis.\n\n"
        "I can still use retrieved LexiMind notes and PYQs shown in the context. "
        "To enable AI answers, set LLM_PROVIDER and the matching API key in the backend .env file.\n\n"
        f"Your question: {prompt[:400]}"
    )
