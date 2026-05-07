"""Adapters for plugging RAGScaleGuard into existing retrieval systems."""

from ragscaleguard.adapters.base import RetrieverAdapter, coerce_document, coerce_result_list, coerce_search_result
from ragscaleguard.adapters.frameworks import (
    HaystackRetrieverAdapter,
    LangChainRetrieverAdapter,
    LlamaIndexRetrieverAdapter,
)
from ragscaleguard.adapters.generic import GuardedRetriever
from ragscaleguard.adapters.http import HTTPRetrieverAdapter, HTTPRetrieverConfig
from ragscaleguard.adapters.jsonl import JSONLRetrievalRunAdapter

__all__ = [
    "GuardedRetriever",
    "HaystackRetrieverAdapter",
    "HTTPRetrieverAdapter",
    "HTTPRetrieverConfig",
    "JSONLRetrievalRunAdapter",
    "LangChainRetrieverAdapter",
    "LlamaIndexRetrieverAdapter",
    "RetrieverAdapter",
    "coerce_document",
    "coerce_result_list",
    "coerce_search_result",
]
