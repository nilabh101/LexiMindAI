"""Normalize concept names deterministically. No aggressive fuzzy matching."""
import re
import unicodedata


_STRIP_WORDS = {"the", "a", "an", "of", "on", "for", "and"}


def normalize_name(name: str) -> str:
    if not name:
        return ""
    text = unicodedata.normalize("NFKC", name).strip().lower()
    text = text.replace("’", "'").replace("`", "'")
    text = re.sub(r"['’]s\b", "", text)  # euler's -> euler
    text = re.sub(r"[^a-z0-9\s\+\-\/]", " ", text)
    tokens = [t for t in text.split() if t and t not in _STRIP_WORDS]
    # Drop trailing generic words
    while tokens and tokens[-1] in {"theorem", "formula", "rule", "method", "concept"}:
        # keep if that's the whole name besides one token
        if len(tokens) <= 2:
            break
        tokens.pop()
    return " ".join(tokens)


def slugify(name: str) -> str:
    n = normalize_name(name)
    slug = re.sub(r"\s+", "-", n)
    return slug[:140] or "concept"


def names_match(a: str, b: str) -> bool:
    return normalize_name(a) == normalize_name(b) and bool(normalize_name(a))
