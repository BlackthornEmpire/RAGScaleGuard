from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from ragscaleguard.models import Document, SearchResult
from ragscaleguard.retrieval.validation import validate_top_k
from ragscaleguard.text import term_counts, tokenize


@dataclass(frozen=True)
class BM25Config:
    k1: float = 1.2
    b: float = 0.75


class BM25Retriever:
    def __init__(self, documents: list[Document], config: BM25Config | None = None) -> None:
        self.documents = documents
        self.config = config or BM25Config()
        self.doc_terms = [term_counts(doc.text) for doc in documents]
        self.doc_lengths = [sum(terms.values()) for terms in self.doc_terms]
        self.avg_doc_length = sum(self.doc_lengths) / max(len(self.doc_lengths), 1)
        self.document_frequency = self._document_frequency(self.doc_terms)

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        validate_top_k(top_k)
        if top_k == 0 or not query.strip():
            return []
        query_terms = tokenize(query)
        scored = [
            SearchResult(document=doc, score=self._score(query_terms, idx), source="bm25")
            for idx, doc in enumerate(self.documents)
        ]
        return sorted(scored, key=lambda result: result.score, reverse=True)[:top_k]

    def _score(self, query_terms: list[str], doc_idx: int) -> float:
        score = 0.0
        terms = self.doc_terms[doc_idx]
        doc_len = self.doc_lengths[doc_idx]
        for term in query_terms:
            frequency = terms.get(term, 0)
            if frequency == 0:
                continue
            score += self._idf(term) * self._term_saturation(frequency, doc_len)
        return score

    def _idf(self, term: str) -> float:
        doc_count = len(self.documents)
        containing_docs = self.document_frequency.get(term, 0)
        return math.log(1 + (doc_count - containing_docs + 0.5) / (containing_docs + 0.5))

    def _term_saturation(self, frequency: int, doc_len: int) -> float:
        cfg = self.config
        denominator = frequency + cfg.k1 * (1 - cfg.b + cfg.b * doc_len / self.avg_doc_length)
        return frequency * (cfg.k1 + 1) / denominator

    @staticmethod
    def _document_frequency(doc_terms: list[Counter[str]]) -> Counter[str]:
        frequency: Counter[str] = Counter()
        for terms in doc_terms:
            frequency.update(terms.keys())
        return frequency
