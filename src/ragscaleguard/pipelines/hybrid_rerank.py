from __future__ import annotations

from ragscaleguard.models import Document, Query, SearchResult
from ragscaleguard.rerankers.cross_encoder import HeuristicReranker
from ragscaleguard.retrieval.hybrid import HybridRetriever


class HybridRerankPipeline:
    def __init__(self, documents: list[Document]) -> None:
        self.retriever = HybridRetriever(documents)
        self.reranker = HeuristicReranker()

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        candidates = self.retriever.search(query, top_k=max(top_k * 5, top_k))
        return self.reranker.rerank(Query(id="ad-hoc", text=query), candidates, top_k=top_k)


def main() -> None:
    documents = [
        Document("slack-1", "Project Atlas deadline is 2026-06-01", {"source_type": "slack"}),
        Document("jira-1", "Project Atlas due date is 2026-05-20", {"source_type": "jira"}),
        Document("conf-1", "Project Atlas technical spec covers streaming retries", {"source_type": "confluence"}),
    ]
    pipeline = HybridRerankPipeline(documents)
    for result in pipeline.search("What is the Project Atlas due date?", top_k=2):
        print(f"{result.document.id}\t{result.score:.3f}\t{result.document.text}")

