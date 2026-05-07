"""Adapters for plugging RAGScaleGuard into existing retrieval systems."""

from ragscaleguard.adapters.base import coerce_document, coerce_search_result
from ragscaleguard.adapters.generic import GuardedRetriever

__all__ = ["GuardedRetriever", "coerce_document", "coerce_search_result"]
