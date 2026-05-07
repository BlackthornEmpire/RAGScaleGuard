from __future__ import annotations

from dataclasses import dataclass

from ragscaleguard.models import Query, SearchResult
from ragscaleguard.scoring.authority import authority_score
from ragscaleguard.scoring.freshness import freshness_score
from ragscaleguard.scoring.metadata import metadata_match_score
from ragscaleguard.text import tokenize


@dataclass(frozen=True)
class RerankWeights:
    retrieval: float = 0.55
    lexical_overlap: float = 0.2
    authority: float = 0.1
    freshness: float = 0.1
    metadata: float = 0.05


class HeuristicReranker:
    def __init__(self, weights: RerankWeights | None = None) -> None:
        self.weights = weights or RerankWeights()

    def rerank(self, query: Query, results: list[SearchResult], top_k: int | None = None) -> list[SearchResult]:
        reranked = [
            SearchResult(
                document=result.document,
                score=self._score(query, result),
                source=f"{result.source}+heuristic_rerank",
                explanation={**result.explanation, "original_score": result.score},
            )
            for result in results
        ]
        ordered = sorted(reranked, key=lambda result: result.score, reverse=True)
        return ordered[:top_k] if top_k is not None else ordered

    def _score(self, query: Query, result: SearchResult) -> float:
        weights = self.weights
        overlap = _jaccard(tokenize(query.text), tokenize(result.document.text))
        return (
            weights.retrieval * result.score
            + weights.lexical_overlap * overlap
            + weights.authority * authority_score(result.document)
            + weights.freshness * freshness_score(result.document)
            + weights.metadata * metadata_match_score(result.document, query)
        )


def _jaccard(left: list[str], right: list[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)

