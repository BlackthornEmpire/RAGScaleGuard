from __future__ import annotations

from ragscaleguard.evaluation.comparison import compare_retrievers
from ragscaleguard.evaluation.reports import comparison_to_markdown
from ragscaleguard.models import Document, Query
from ragscaleguard.retrieval.bm25 import BM25Retriever
from ragscaleguard.retrieval.dense import DenseRetriever


def test_compare_retrievers_reports_multiple_baselines() -> None:
    documents = [
        Document("jira", "Atlas due date is 2026-05-20."),
        Document("slack", "Atlas decision approved."),
    ]
    queries = [Query("q1", "Atlas due date", ground_truth_document_ids=("jira",))]

    comparison = compare_retrievers(
        {"dense": DenseRetriever(documents), "bm25": BM25Retriever(documents)},
        queries,
        top_k=1,
    )
    report = comparison_to_markdown(comparison)

    assert len(comparison.runs) == 2
    assert comparison.best_by_recall is not None
    assert "dense" in report
    assert "bm25" in report
