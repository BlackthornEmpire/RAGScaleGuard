from __future__ import annotations

from ragscaleguard.evaluation.comparison import compare_retrievers
from ragscaleguard.evaluation.reports import comparison_to_markdown
from ragscaleguard.models import Document, Query
from ragscaleguard.pipelines.hybrid_rerank import HybridRerankPipeline
from ragscaleguard.retrieval.bm25 import BM25Retriever
from ragscaleguard.retrieval.dense import DenseRetriever
from ragscaleguard.retrieval.hybrid import HybridRetriever


documents = [
    Document("slack-1", "Atlas launch decision is approved. Deadline is 2026-06-01.", {"source_type": "slack"}),
    Document("jira-1", "Atlas implementation ticket. Due date is 2026-05-20.", {"source_type": "jira"}),
    Document("conf-1", "Atlas technical spec for streaming retries.", {"source_type": "confluence"}),
]

queries = [
    Query("q1", "What is the Atlas implementation due date?", ground_truth_document_ids=("jira-1",)),
]

comparison = compare_retrievers(
    {
        "dense": DenseRetriever(documents),
        "bm25": BM25Retriever(documents),
        "hybrid": HybridRetriever(documents),
        "hybrid-rerank": HybridRerankPipeline(documents),
    },
    queries,
    top_k=2,
)
print(comparison_to_markdown(comparison))
