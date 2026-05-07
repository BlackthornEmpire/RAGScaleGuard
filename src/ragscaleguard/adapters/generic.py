from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from ragscaleguard.adapters.base import coerce_result_list
from ragscaleguard.integrations.guard import GuardDecision, guard_retrieval
from ragscaleguard.models import SearchResult


class GuardedRetriever:
    def __init__(self, retriever: object, search_method: str | None = None) -> None:
        self.retriever = retriever
        self.search_method = search_method

    def search(self, query: str, top_k: int = 10) -> GuardDecision:
        raw_results = self._call_retriever(query, top_k)
        results = tuple(raw_results)
        return guard_retrieval(query, results)

    def _call_retriever(self, query: str, top_k: int) -> list[SearchResult]:
        method = _resolve_method(self.retriever, self.search_method)
        return coerce_result_list(_call_with_top_k(method, query, top_k))


def _resolve_method(retriever: object, search_method: str | None) -> Callable[..., Any]:
    method_names = (
        (search_method,)
        if search_method is not None
        else ("search", "retrieve", "invoke", "get_relevant_documents", "similarity_search")
    )
    for method_name in method_names:
        if method_name and hasattr(retriever, method_name):
            method = getattr(retriever, method_name)
            if callable(method):
                return cast(Callable[..., Any], method)
    raise TypeError("Retriever must expose search, retrieve, invoke or a configured method name")


def _call_with_top_k(method: Callable[..., Any], query: str, top_k: int) -> object:
    last_error: TypeError | None = None
    try:
        return method(query, top_k=top_k)
    except TypeError as exc:
        last_error = exc
    try:
        return method(query, k=top_k)
    except TypeError as exc:
        last_error = exc
    try:
        return method(query, limit=top_k)
    except TypeError as exc:
        last_error = exc
    try:
        return method({"query": query, "top_k": top_k})
    except TypeError as exc:
        last_error = exc
    try:
        return method(query)
    except TypeError as exc:
        last_error = exc
    raise TypeError("Retriever method could not be called with supported query/top-k shapes") from last_error
