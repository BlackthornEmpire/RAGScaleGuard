from __future__ import annotations

from ragscaleguard.models import Document

DEFAULT_SOURCE_AUTHORITY = {
    "confluence": 1.0,
    "google_drive": 0.9,
    "github": 0.85,
    "jira": 0.8,
    "linear": 0.8,
    "hubspot": 0.75,
    "gmail": 0.65,
    "fireflies": 0.6,
    "slack": 0.45,
}


def authority_score(
    document: Document,
    source_weights: dict[str, float] | None = None,
) -> float:
    weights = source_weights or DEFAULT_SOURCE_AUTHORITY
    source_type = (document.source_type or "").lower()
    base = weights.get(source_type, 0.5)
    status = str(document.metadata.get("status", "")).lower()
    if status in {"final", "resolved", "approved", "accepted"}:
        base += 0.1
    if document.metadata.get("is_verified") is True:
        base += 0.1
    if status in {"draft", "deprecated", "stale", "rejected"}:
        base -= 0.2
    return min(max(base, 0.0), 1.0)

