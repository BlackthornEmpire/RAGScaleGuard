from __future__ import annotations

import pytest

from ragscaleguard.models import Document
from ragscaleguard.retrieval.bm25 import BM25Retriever
from ragscaleguard.retrieval.dense import DenseRetriever
from ragscaleguard.retrieval.hybrid import HybridRetriever


@pytest.mark.parametrize("retriever_cls", [BM25Retriever, DenseRetriever, HybridRetriever])
def test_retrievers_return_no_results_for_empty_queries(
    retriever_cls: type[BM25Retriever] | type[DenseRetriever] | type[HybridRetriever],
) -> None:
    retriever = retriever_cls([Document("doc-1", "Atlas due date is 2026-05-20.")])

    assert retriever.search("", top_k=10) == []
    assert retriever.search("   ", top_k=10) == []


@pytest.mark.parametrize("retriever_cls", [BM25Retriever, DenseRetriever, HybridRetriever])
def test_retrievers_validate_top_k(
    retriever_cls: type[BM25Retriever] | type[DenseRetriever] | type[HybridRetriever],
) -> None:
    retriever = retriever_cls([Document("doc-1", "Atlas due date is 2026-05-20.")])

    assert retriever.search("Atlas", top_k=0) == []
    with pytest.raises(ValueError, match="top_k"):
        retriever.search("Atlas", top_k=-1)


def test_hybrid_retriever_rejects_duplicate_document_ids() -> None:
    with pytest.raises(ValueError, match="Document IDs must be unique"):
        HybridRetriever(
            [
                Document("duplicate", "First document."),
                Document("duplicate", "Second document."),
            ]
        )
