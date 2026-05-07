from __future__ import annotations

from ragscaleguard.diagnostics.conflict_detection import detect_conflicts
from ragscaleguard.models import Document, SearchResult


def test_conflict_detection_flags_different_deadlines() -> None:
    results = [
        SearchResult(Document("slack", "Atlas deadline is 2026-06-01."), 1.0, "test"),
        SearchResult(Document("jira", "Atlas deadline is 2026-05-20."), 1.0, "test"),
    ]

    conflicts = detect_conflicts(results)

    assert len(conflicts) == 1
    assert conflicts[0].field == "deadline"

