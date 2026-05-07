from __future__ import annotations

from typing import Protocol

from ragscaleguard.models import Query, SearchResult


class ModelScorer(Protocol):
    def score(self, query: Query, result: SearchResult) -> float: ...


class ModelReranker:
    """Adapter for user-supplied model or cross-encoder rerankers.

    RAGScaleGuard does not call a hosted model by default. Production users can pass
    an object implementing ``ModelScorer`` while preserving deterministic tests for
    the rest of the pipeline.
    """

    def __init__(self, scorer: ModelScorer) -> None:
        self.scorer = scorer

    def rerank(self, query: Query, results: list[SearchResult], top_k: int | None = None) -> list[SearchResult]:
        scored = [
            SearchResult(
                document=result.document,
                score=self.scorer.score(query, result),
                source=f"{result.source}+llm_rerank",
                explanation={**result.explanation, "original_score": result.score},
            )
            for result in results
        ]
        ordered = sorted(scored, key=lambda result: result.score, reverse=True)
        return ordered[:top_k] if top_k is not None else ordered
