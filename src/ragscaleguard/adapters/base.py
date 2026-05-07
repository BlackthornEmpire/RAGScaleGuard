from __future__ import annotations

from collections.abc import Mapping

from ragscaleguard.models import Document, SearchResult


def coerce_document(value: object, fallback_id: str = "document") -> Document:
    if isinstance(value, Document):
        return value
    if not isinstance(value, Mapping):
        return Document(fallback_id, str(value))

    doc_id = value.get("id") or value.get("doc_id") or value.get("document_id") or fallback_id
    text = value.get("text") or value.get("content") or value.get("page_content") or value.get("body") or ""
    metadata = value.get("metadata")
    if not isinstance(metadata, Mapping):
        metadata = {
            key: item
            for key, item in value.items()
            if key
            not in {
                "id",
                "doc_id",
                "document_id",
                "text",
                "content",
                "page_content",
                "body",
                "score",
                "source",
                "metadata",
            }
        }
    return Document(id=str(doc_id), text=str(text), metadata=dict(metadata))


def coerce_search_result(value: object, rank: int = 0) -> SearchResult:
    if isinstance(value, SearchResult):
        return value
    if isinstance(value, Document):
        return SearchResult(value, score=_rank_score(rank), source="adapter")
    if not isinstance(value, Mapping):
        return SearchResult(coerce_document(value, fallback_id=f"result-{rank + 1}"), _rank_score(rank), "adapter")

    raw_document = value.get("document") or value.get("doc") or value
    document = coerce_document(raw_document, fallback_id=f"result-{rank + 1}")
    score = _float_or_default(value.get("score"), _rank_score(rank))
    source = str(value.get("source") or value.get("retriever") or "adapter")
    explanation = value.get("explanation")
    return SearchResult(
        document=document,
        score=score,
        source=source,
        explanation=dict(explanation) if isinstance(explanation, Mapping) else {},
    )


def _rank_score(rank: int) -> float:
    return max(1.0 - rank * 0.05, 0.0)


def _float_or_default(value: object, default: float) -> float:
    if isinstance(value, bool):
        return default
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
