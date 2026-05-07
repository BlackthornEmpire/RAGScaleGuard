from __future__ import annotations

from ragscaleguard.evaluation.metrics import evaluate_retrieval
from ragscaleguard.models import Document, Query, SearchResult


def test_retrieval_metrics_measure_recall_precision_and_citation_accuracy() -> None:
    query = Query("q1", "When is Atlas due?", ground_truth_document_ids=("jira",))
    runs = {
        query: [
            SearchResult(Document("jira", "Due date is 2026-05-20."), 1.0, "test"),
            SearchResult(Document("slack", "Decision approved."), 0.5, "test"),
        ]
    }

    metrics = evaluate_retrieval(runs)

    assert metrics.recall_at_k == 1.0
    assert metrics.precision_at_k == 0.5
    assert metrics.citation_accuracy == 1.0

