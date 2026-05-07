from __future__ import annotations

import pytest

from ragscaleguard.models import Document
from ragscaleguard.retrieval.bm25 import BM25Config, BM25Retriever
from ragscaleguard.retrieval.dense import DenseRetriever, hashing_embed
from ragscaleguard.retrieval.hybrid import HybridConfig, HybridRetriever


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


def test_hashing_embed_rejects_invalid_dimensions() -> None:
    with pytest.raises(ValueError, match="dimensions"):
        hashing_embed("Atlas", dimensions=0)


def test_bm25_rejects_invalid_config_values() -> None:
    documents = [Document("doc-1", "Atlas due date is 2026-05-20.")]

    with pytest.raises(ValueError, match="k1"):
        BM25Retriever(documents, config=BM25Config(k1=0))
    with pytest.raises(ValueError, match="b"):
        BM25Retriever(documents, config=BM25Config(b=1.5))


def test_hybrid_rejects_invalid_config_values() -> None:
    documents = [Document("doc-1", "Atlas due date is 2026-05-20.")]

    with pytest.raises(ValueError, match="weights"):
        HybridRetriever(documents, config=HybridConfig(dense_weight=-0.1))
    with pytest.raises(ValueError, match="At least one"):
        HybridRetriever(documents, config=HybridConfig(dense_weight=0, bm25_weight=0))
    with pytest.raises(ValueError, match="candidate_multiplier"):
        HybridRetriever(documents, config=HybridConfig(candidate_multiplier=0))
