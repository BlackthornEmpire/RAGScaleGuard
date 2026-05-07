from __future__ import annotations

from dataclasses import dataclass

from ragscaleguard.models import Document, SearchResult
from ragscaleguard.retrieval.bm25 import BM25Retriever
from ragscaleguard.retrieval.dense import DenseRetriever, Embedder, hashing_embed
from ragscaleguard.retrieval.validation import validate_top_k, validate_unique_document_ids


@dataclass(frozen=True)
class HybridConfig:
    dense_weight: float = 0.5
    bm25_weight: float = 0.5
    candidate_multiplier: int = 5


class HybridRetriever:
    def __init__(
        self,
        documents: list[Document],
        config: HybridConfig | None = None,
        embedder: Embedder = hashing_embed,
    ) -> None:
        validate_unique_document_ids(documents)
        self.documents = documents
        self.config = config or HybridConfig()
        self.dense = DenseRetriever(documents, embedder=embedder)
        self.bm25 = BM25Retriever(documents)

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        validate_top_k(top_k)
        if top_k == 0 or not query.strip():
            return []
        candidate_k = max(top_k, top_k * self.config.candidate_multiplier)
        dense_results = self.dense.search(query, candidate_k)
        bm25_results = self.bm25.search(query, candidate_k)
        dense_scores = _normalised_scores(dense_results)
        bm25_scores = _normalised_scores(bm25_results)
        document_by_id = {doc.id: doc for doc in self.documents}
        candidate_ids = set(dense_scores) | set(bm25_scores)
        merged = [
            SearchResult(
                document=document_by_id[doc_id],
                score=(
                    self.config.dense_weight * dense_scores.get(doc_id, 0.0)
                    + self.config.bm25_weight * bm25_scores.get(doc_id, 0.0)
                ),
                source="hybrid",
                explanation={
                    "dense": dense_scores.get(doc_id, 0.0),
                    "bm25": bm25_scores.get(doc_id, 0.0),
                },
            )
            for doc_id in candidate_ids
        ]
        return sorted(merged, key=lambda result: result.score, reverse=True)[:top_k]


def _normalised_scores(results: list[SearchResult]) -> dict[str, float]:
    if not results:
        return {}
    scores = [result.score for result in results]
    min_score = min(scores)
    max_score = max(scores)
    if max_score == min_score:
        return {result.document.id: 1.0 for result in results}
    return {
        result.document.id: (result.score - min_score) / (max_score - min_score)
        for result in results
    }
