from __future__ import annotations

from ragscaleguard.models import Document
from ragscaleguard.retrieval.dense import DenseRetriever


def build_dense_baseline(documents: list[Document]) -> DenseRetriever:
    return DenseRetriever(documents)

