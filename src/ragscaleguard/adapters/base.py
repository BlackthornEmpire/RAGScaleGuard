from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from ragscaleguard.models import Document, SearchResult


class RetrieverAdapter(Protocol):
    """Minimal retrieval contract used by evaluation and guard pipelines."""

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]: ...


def coerce_document(value: object, fallback_id: str = "document") -> Document:
    if isinstance(value, Document):
        return value
    if not isinstance(value, Mapping) and not isinstance(value, str):
        object_document = _document_from_object(value, fallback_id)
        if object_document is not None:
            return object_document
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
    if not isinstance(value, Mapping) and not isinstance(value, str):
        object_result = _search_result_from_object(value, rank)
        if object_result is not None:
            return object_result
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


def coerce_result_list(value: object) -> list[SearchResult]:
    """Coerce common retriever outputs into a list of SearchResult objects."""

    raw_results = _extract_result_sequence(value)
    return [coerce_search_result(item, rank) for rank, item in enumerate(raw_results)]


def _extract_result_sequence(value: object) -> Sequence[object]:
    if isinstance(value, Mapping):
        for key in ("results", "documents", "data", "matches", "nodes"):
            nested = value.get(key)
            if isinstance(nested, Sequence) and not isinstance(nested, str):
                return nested
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, str):
        return value
    raise TypeError("Retriever must return a sequence, mapping, or supported framework response")


def _document_from_object(value: object, fallback_id: str) -> Document | None:
    node = getattr(value, "node", None)
    if node is not None:
        return coerce_document(node, fallback_id=fallback_id)

    doc_id = _first_attr(value, ("id", "doc_id", "document_id", "node_id", "ref_doc_id"))
    text = _first_attr(value, ("text", "content", "page_content"))
    if text is None and hasattr(value, "get_content"):
        text = value.get_content()
    if text is None:
        return None

    metadata = _first_attr(value, ("metadata", "meta"))
    if not isinstance(metadata, Mapping):
        metadata = {}
    return Document(id=str(doc_id or fallback_id), text=str(text), metadata=dict(metadata))


def _search_result_from_object(value: object, rank: int) -> SearchResult | None:
    node = getattr(value, "node", None)
    score = _float_or_default(_first_attr(value, ("score", "similarity", "distance")), _rank_score(rank))
    if node is not None:
        return SearchResult(coerce_document(node, fallback_id=f"result-{rank + 1}"), score, "adapter")

    document = _document_from_object(value, fallback_id=f"result-{rank + 1}")
    if document is None:
        return None
    return SearchResult(document, score, "adapter")


def _first_attr(value: object, names: tuple[str, ...]) -> Any:
    for name in names:
        if hasattr(value, name):
            attr = getattr(value, name)
            if attr is not None:
                return attr
    return None
