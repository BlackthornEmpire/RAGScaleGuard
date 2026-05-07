from __future__ import annotations

from dataclasses import dataclass

from ragscaleguard.models import Query, SearchResult


@dataclass(frozen=True)
class TopKFailure:
    query_id: str
    missing_ground_truth_ids: tuple[str, ...]
    retrieved_ids: tuple[str, ...]
    diagnosis: str


def diagnose_topk_failure(query: Query, results: list[SearchResult]) -> TopKFailure | None:
    if not query.ground_truth_document_ids:
        return None
    retrieved_ids = tuple(result.document.id for result in results)
    missing = tuple(doc_id for doc_id in query.ground_truth_document_ids if doc_id not in retrieved_ids)
    if not missing:
        return None
    return TopKFailure(
        query_id=query.id,
        missing_ground_truth_ids=missing,
        retrieved_ids=retrieved_ids,
        diagnosis="Ground truth document exists but was not present in the retrieved top-k set.",
    )

