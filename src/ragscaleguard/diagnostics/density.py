from __future__ import annotations

from dataclasses import dataclass

from ragscaleguard.models import Document
from ragscaleguard.retrieval.dense import Embedder, cosine_similarity, hashing_embed


@dataclass(frozen=True)
class DensityFinding:
    document_id: str
    neighbours_above_threshold: int
    mean_similarity: float
    nearest_document_ids: tuple[str, ...]


class CorpusDensityAnalyser:
    def __init__(self, embedder: Embedder = hashing_embed, similarity_threshold: float = 0.72) -> None:
        self.embedder = embedder
        self.similarity_threshold = similarity_threshold

    def analyse(self, documents: list[Document], nearest_k: int = 5) -> list[DensityFinding]:
        embeddings = [self.embedder(document.text) for document in documents]
        findings: list[DensityFinding] = []
        for idx, document in enumerate(documents):
            similarities = [
                (other.id, cosine_similarity(embeddings[idx], embeddings[other_idx]))
                for other_idx, other in enumerate(documents)
                if other_idx != idx
            ]
            similarities.sort(key=lambda item: item[1], reverse=True)
            dense_count = sum(1 for _, score in similarities if score >= self.similarity_threshold)
            mean_similarity = (
                sum(score for _, score in similarities[:nearest_k]) / min(len(similarities), nearest_k)
                if similarities
                else 0.0
            )
            findings.append(
                DensityFinding(
                    document_id=document.id,
                    neighbours_above_threshold=dense_count,
                    mean_similarity=mean_similarity,
                    nearest_document_ids=tuple(doc_id for doc_id, _ in similarities[:nearest_k]),
                )
            )
        return sorted(
            findings,
            key=lambda finding: (finding.neighbours_above_threshold, finding.mean_similarity),
            reverse=True,
        )

