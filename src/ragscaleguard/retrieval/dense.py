from __future__ import annotations

import hashlib
import math
from collections.abc import Callable

from ragscaleguard.models import Document, SearchResult
from ragscaleguard.retrieval.validation import validate_top_k
from ragscaleguard.text import tokenize

Vector = tuple[float, ...]
Embedder = Callable[[str], Vector]


def hashing_embed(text: str, dimensions: int = 128) -> Vector:
    if dimensions <= 0:
        raise ValueError("dimensions must be greater than zero")
    vector = [0.0] * dimensions
    for token in tokenize(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign
    return _normalise(tuple(vector))


class DenseRetriever:
    def __init__(self, documents: list[Document], embedder: Embedder = hashing_embed) -> None:
        self.documents = documents
        self.embedder = embedder
        self.embeddings = [embedder(doc.text) for doc in documents]

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        validate_top_k(top_k)
        if top_k == 0 or not query.strip():
            return []
        query_embedding = self.embedder(query)
        scored = [
            SearchResult(document=doc, score=cosine_similarity(query_embedding, embedding), source="dense")
            for doc, embedding in zip(self.documents, self.embeddings, strict=True)
        ]
        return sorted(scored, key=lambda result: result.score, reverse=True)[:top_k]


def cosine_similarity(left: Vector, right: Vector) -> float:
    if len(left) != len(right):
        raise ValueError("Vectors must have the same dimensionality")
    return sum(a * b for a, b in zip(left, right, strict=True))


def _normalise(vector: Vector) -> Vector:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return tuple(value / norm for value in vector)
