from __future__ import annotations

from ragscaleguard.models import Document
from ragscaleguard.retrieval.hybrid import HybridRetriever


def test_hybrid_retrieval_combines_keyword_and_dense_candidates() -> None:
    documents = [
        Document("slack", "Atlas decision approved after customer escalation."),
        Document("jira", "Atlas implementation due date is 2026-05-20."),
        Document("notes", "Roadmap discussion for unrelated billing work."),
    ]

    results = HybridRetriever(documents).search("Atlas due date", top_k=2)

    assert "jira" in [result.document.id for result in results]
    assert results[0].score >= results[1].score

