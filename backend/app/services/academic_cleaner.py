"""Academic-preserving text cleaning. Keeps formulas, symbols, Greek letters."""
import re
import unicodedata
from collections import Counter
from typing import List, Tuple


def clean_academic_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\x00", "")
    text = re.sub(r"\r\n|\r", "\n", text)
    text = _unwrap_lines(text)
    text = _strip_repeated_headers(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _unwrap_lines(text: str) -> str:
    """Join broken wrapping while preserving paragraph and math breaks."""
    lines = text.split("\n")
    out: List[str] = []
    buf = ""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if buf:
                out.append(buf)
                buf = ""
            out.append("")
            continue
        if not buf:
            buf = stripped
            continue
        if _should_join(buf, stripped):
            buf = buf.rstrip("-") + (" " if not buf.endswith("-") else "") + stripped
        else:
            out.append(buf)
            buf = stripped
    if buf:
        out.append(buf)
    return "\n".join(out)


def _should_join(prev: str, nxt: str) -> bool:
    if prev.endswith(("-", "–")):
        return True
    if prev.endswith((".", ":", "?", "!", "।")):
        return False
    if re.match(r"^(chapter|unit|section|topic|question|q\s*\d)\b", nxt, re.I):
        return False
    if re.match(r"^(\d+[.)]|Q\s*\d+|[A-D][).]|[\(\[]?[a-ivx]+[\)\]])\s", nxt, re.I):
        return False
    if len(prev) < 40:
        return False
    return nxt[:1].islower() or prev[-1:].islower()


def _strip_repeated_headers(text: str) -> str:
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if len(lines) < 8:
        return text
    counts = Counter(lines)
    repeated = {ln for ln, c in counts.items() if c >= 3 and len(ln) < 80}
    if not repeated:
        return text
    kept = []
    for ln in text.split("\n"):
        if ln.strip() in repeated:
            continue
        kept.append(ln)
    return "\n".join(kept)


def extract_formulas(text: str) -> List[str]:
    candidates = []
    for line in text.split("\n"):
        s = line.strip()
        if not s or len(s) > 180:
            continue
        if re.search(r"[∂∑∫√πθαβγλμσΩ∞≤≥≠≈±]|\\frac|_\{|\^\{|∂f/∂", s):
            candidates.append(s)
        elif re.search(r"=\s*.+", s) and re.search(r"[xyzn]|dx|dy|f\(", s) and len(s) < 120:
            if not s.lower().startswith(("figure", "table", "page")):
                candidates.append(s)
    seen = set()
    out = []
    for c in candidates:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out[:20]
