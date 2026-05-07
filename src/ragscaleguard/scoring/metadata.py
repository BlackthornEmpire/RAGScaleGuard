from __future__ import annotations

from ragscaleguard.models import Document, Query


def metadata_match_score(document: Document, query: Query, keys: tuple[str, ...] | None = None) -> float:
    keys = keys or ("project", "customer", "ticket_id", "department", "source_type", "author")
    requested = {key: query.metadata[key] for key in keys if key in query.metadata}
    if not requested:
        return 0.0
    matches = sum(1 for key, value in requested.items() if document.metadata.get(key) == value)
    return matches / len(requested)

