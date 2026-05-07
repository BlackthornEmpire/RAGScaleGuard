from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ragscaleguard.adapters.base import coerce_search_result
from ragscaleguard.integrations.guard import GuardDecision, guard_retrieval
from ragscaleguard.models import SearchResult


class GuardedRetriever:
    def __init__(self, retriever: object, search_method: str = "search") -> None:
        self.retriever = retriever
        self.search_method = search_method

    def search(self, query: str, top_k: int = 10) -> GuardDecision:
        raw_results = self._call_retriever(query, top_k)
        results = tuple(coerce_search_result(item, rank) for rank, item in enumerate(raw_results))
        return guard_retrieval(query, results)

    def _call_retriever(self, query: str, top_k: int) -> Sequence[SearchResult | dict[str, Any] | str]:
        method = getattr(self.retriever, self.search_method)
        try:
            raw = method(query, top_k=top_k)
        except TypeError:
            raw = method(query)
        if isinstance(raw, Sequence) and not isinstance(raw, str):
            return raw
        raise TypeError("Retriever must return a sequence of documents or search results")
