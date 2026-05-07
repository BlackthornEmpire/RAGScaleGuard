from __future__ import annotations

from ragscaleguard.adapters.base import coerce_result_list
from ragscaleguard.models import SearchResult


class LangChainRetrieverAdapter:
    """Adapter for LangChain-style retrievers and vector stores."""

    def __init__(self, retriever: object) -> None:
        self.retriever = retriever

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        if hasattr(self.retriever, "invoke"):
            return coerce_result_list(self.retriever.invoke(query))
        if hasattr(self.retriever, "get_relevant_documents"):
            return coerce_result_list(self.retriever.get_relevant_documents(query))
        if hasattr(self.retriever, "similarity_search"):
            return coerce_result_list(self.retriever.similarity_search(query, k=top_k))
        raise TypeError("LangChain adapter expects invoke, get_relevant_documents or similarity_search")


class LlamaIndexRetrieverAdapter:
    """Adapter for LlamaIndex retrievers returning nodes or NodeWithScore objects."""

    def __init__(self, retriever: object) -> None:
        self.retriever = retriever

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        if hasattr(self.retriever, "retrieve"):
            return coerce_result_list(self.retriever.retrieve(query))
        if hasattr(self.retriever, "query"):
            return coerce_result_list(self.retriever.query(query))
        raise TypeError("LlamaIndex adapter expects retrieve or query")


class HaystackRetrieverAdapter:
    """Adapter for Haystack components returning documents or {'documents': [...]}."""

    def __init__(self, retriever: object) -> None:
        self.retriever = retriever

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        if hasattr(self.retriever, "run"):
            return coerce_result_list(self.retriever.run(query=query, top_k=top_k))
        if hasattr(self.retriever, "retrieve"):
            return coerce_result_list(self.retriever.retrieve(query=query, top_k=top_k))
        raise TypeError("Haystack adapter expects run or retrieve")
