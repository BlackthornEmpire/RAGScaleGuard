from __future__ import annotations

from dataclasses import dataclass

from ragscaleguard.models import Query, SearchResult


@dataclass(frozen=True)
class RetrievalMetrics:
    recall_at_k: float
    precision_at_k: float
    citation_accuracy: float
    evaluated_queries: int


def evaluate_retrieval(runs: dict[Query, list[SearchResult]]) -> RetrievalMetrics:
    recalls: list[float] = []
    precisions: list[float] = []
    citation_accuracies: list[float] = []
    for query, results in runs.items():
        truth = set(query.ground_truth_document_ids)
        if not truth:
            continue
        retrieved = [result.document.id for result in results]
        hits = truth & set(retrieved)
        recalls.append(len(hits) / len(truth))
        precisions.append(len(hits) / max(len(retrieved), 1))
        citation_accuracies.append(1.0 if retrieved and retrieved[0] in truth else 0.0)
    if not recalls:
        return RetrievalMetrics(0.0, 0.0, 0.0, 0)
    return RetrievalMetrics(
        recall_at_k=sum(recalls) / len(recalls),
        precision_at_k=sum(precisions) / len(precisions),
        citation_accuracy=sum(citation_accuracies) / len(citation_accuracies),
        evaluated_queries=len(recalls),
    )

