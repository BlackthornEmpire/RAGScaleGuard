from __future__ import annotations

from ragscaleguard.adapters.base import coerce_search_result
from ragscaleguard.adapters.generic import GuardedRetriever
from ragscaleguard.integrations.guard import guard_retrieval
from ragscaleguard.models import Document, SearchResult


def test_guard_retrieval_blocks_conflicting_context_before_generation() -> None:
    results = [
        SearchResult(Document("current", "Deadline is 2026-05-20.", {"source_type": "confluence"}), 0.9, "test"),
        SearchResult(Document("old", "Deadline is 2026-06-01.", {"source_type": "slack"}), 0.8, "test"),
    ]

    decision = guard_retrieval("What is the deadline?", results)

    assert decision.severity == "error"
    assert decision.should_block_generation is True
    assert any(issue.stage == "Conflict gate" for issue in decision.issues)
    assert decision.approved_context


def test_guard_accepts_optional_suggestion_provider() -> None:
    results = [
        SearchResult(Document("doc", "Status is approved.", {"source_type": "confluence"}), 0.9, "test"),
    ]

    decision = guard_retrieval(
        "What is the status?",
        results,
        suggestion_provider=lambda query, result_set, issues: [f"Review {query.id} with {len(result_set)} candidate."],
    )

    assert "Review ad-hoc with 1 candidate." in decision.suggestions


def test_generic_adapter_wraps_existing_retriever_shapes() -> None:
    class ExistingRetriever:
        def search(self, query: str, top_k: int = 10) -> list[dict[str, object]]:
            return [
                {
                    "id": "doc-1",
                    "text": f"{query}. Status is approved.",
                    "score": 0.91,
                    "source_type": "confluence",
                }
            ][:top_k]

    decision = GuardedRetriever(ExistingRetriever()).search("Atlas", top_k=1)

    assert decision.severity == "ok"
    assert decision.approved_results[0].document.id == "doc-1"


def test_coerce_search_result_supports_plain_documents_and_mappings() -> None:
    document_result = coerce_search_result(Document("doc", "Body"), rank=0)
    mapping_result = coerce_search_result(
        {"document": {"id": "mapped", "page_content": "Mapped body"}, "score": "0.7"},
        rank=1,
    )

    assert document_result.score == 1.0
    assert mapping_result.document.text == "Mapped body"
    assert mapping_result.score == 0.7
