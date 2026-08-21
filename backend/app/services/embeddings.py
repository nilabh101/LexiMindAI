"""Embedding + retrieval abstractions. Default TF-IDF (sklearn) — no extra infra."""
from typing import List, Dict, Optional, Any
import math
import re

from app.core.config import settings


class EmbeddingService:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = (provider or settings.EMBEDDING_PROVIDER or "tfidf").lower()
        self.model_name = model or settings.EMBEDDING_MODEL
        self._st_model = None
        self._vectorizer = None

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        texts = [t or "" for t in texts]
        if self.provider in {"huggingface", "sentence-transformers", "st"}:
            try:
                return self._embed_st(texts)
            except Exception:
                return self._embed_tfidf(texts)
        return self._embed_tfidf(texts)

    def _embed_st(self, texts: List[str]) -> List[List[float]]:
        if self._st_model is None:
            from sentence_transformers import SentenceTransformer
            self._st_model = SentenceTransformer(self.model_name)
        vecs = self._st_model.encode(texts, show_progress_bar=False)
        return [v.tolist() for v in vecs]

    def _embed_tfidf(self, texts: List[str]) -> List[List[float]]:
        from sklearn.feature_extraction.text import TfidfVectorizer
        if not any(texts):
            return [[0.0] for _ in texts]
        self._vectorizer = TfidfVectorizer(max_features=512, ngram_range=(1, 2))
        matrix = self._vectorizer.fit_transform(texts)
        return [row.toarray().ravel().tolist() for row in matrix]

    def embed_query(self, query: str, fitted_texts: Optional[List[str]] = None) -> List[float]:
        if self.provider in {"huggingface", "sentence-transformers", "st"}:
            try:
                return self._embed_st([query])[0]
            except Exception:
                pass
        corpus = (fitted_texts or []) + [query]
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(max_features=512, ngram_range=(1, 2))
        matrix = vec.fit_transform(corpus)
        return matrix[-1].toarray().ravel().tolist()


def cosine(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class RetrievalService:
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embeddings = embedding_service or EmbeddingService()

    def retrieve_context(
        self,
        query: str,
        chunks: List[Dict],
        questions: Optional[List[Dict]] = None,
        concepts: Optional[List[Dict]] = None,
        filters: Optional[Dict] = None,
        top_k: int = 6,
    ) -> Dict[str, Any]:
        filters = filters or {}
        filtered = []
        for ch in chunks:
            if filters.get("subject_id") and ch.get("subject_id") and ch.get("subject_id") != filters["subject_id"]:
                continue
            if filters.get("concept_id") and ch.get("concept_id") and ch.get("concept_id") != filters["concept_id"]:
                continue
            filtered.append(ch)
        if not filtered:
            filtered = list(chunks)

        qn = (query or "").lower()
        ranked = []
        for ch in filtered:
            text = ch.get("text") or ""
            kw = _keyword_score(qn, text.lower())
            ranked.append((kw, ch))
        ranked.sort(key=lambda x: -x[0])

        # Optional semantic rerank on top candidates
        top_for_embed = [c for _, c in ranked[:24]]
        if top_for_embed and query:
            try:
                texts = [c.get("text") or "" for c in top_for_embed]
                qvec = self.embeddings.embed_query(query, texts)
                docvecs = self.embeddings.embed_texts(texts + [query])
                # last is query if tfidf fitted together — use cosine vs qvec when lengths match
                scored = []
                for i, c in enumerate(top_for_embed):
                    scored.append((cosine(docvecs[i], qvec if len(qvec) == len(docvecs[i]) else docvecs[-1]), c))
                scored.sort(key=lambda x: -x[0])
                top_chunks = [c for s, c in scored[:top_k] if s > 0 or _keyword_score(qn, (c.get("text") or "").lower()) > 0]
            except Exception:
                top_chunks = [c for _, c in ranked[:top_k] if _ > 0]
        else:
            top_chunks = [c for s, c in ranked[:top_k] if s > 0]

        matched_concepts = []
        for c in concepts or []:
            name = (c.get("canonical_name") or c.get("name") or "").lower()
            if name and name in qn:
                matched_concepts.append(c)
        if not matched_concepts:
            matched_concepts = (concepts or [])[:3] if filters.get("concept_id") else []

        related_pyqs = []
        for q in questions or []:
            if q.get("source") not in {"PYQ", "DEMO"} and not str(q.get("source", "")).upper() == "PYQ":
                if q.get("source") != "PYQ":
                    continue
            blob = (q.get("question_text") or "").lower()
            if _keyword_score(qn, blob) > 0.05 or (filters.get("concept_id") and q.get("concept_id") == filters.get("concept_id")):
                related_pyqs.append(q)
        related_pyqs = related_pyqs[:8]

        sources = []
        for ch in top_chunks:
            sources.append({
                "document_id": ch.get("document_id"),
                "page": ch.get("page_number"),
                "chunk_id": ch.get("id"),
                "section": ch.get("section"),
            })

        return {
            "query": query,
            "chunks": top_chunks[:top_k],
            "concepts": matched_concepts,
            "pyqs": related_pyqs,
            "sources": sources,
        }


def _keyword_score(query: str, text: str) -> float:
    tokens = [t for t in re.findall(r"[a-z0-9']+", query) if len(t) > 2]
    if not tokens or not text:
        return 0.0
    hits = sum(1 for t in tokens if t in text)
    return hits / len(tokens)
