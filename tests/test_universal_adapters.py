from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import pytest

from ragscaleguard.adapters import (
    GuardedRetriever,
    HTTPRetrieverAdapter,
    HTTPRetrieverConfig,
    HaystackRetrieverAdapter,
    JSONLRetrievalRunAdapter,
    LangChainRetrieverAdapter,
    LlamaIndexRetrieverAdapter,
)
from ragscaleguard.cli import main as cli_main


class FrameworkDocument:
    def __init__(
        self,
        page_content: str,
        metadata: dict[str, object] | None = None,
        doc_id: str = "framework-doc",
        score: float = 0.9,
    ) -> None:
        self.page_content = page_content
        self.metadata = metadata or {}
        self.id = doc_id
        self.score = score


def test_generic_adapter_auto_detects_invoke_shape() -> None:
    class ExistingRetriever:
        def invoke(self, query: str) -> list[FrameworkDocument]:
            return [FrameworkDocument(f"{query} approved.", {"source_type": "confluence"}, "lc-1")]

    decision = GuardedRetriever(ExistingRetriever()).search("Atlas", top_k=1)

    assert decision.approved_results[0].document.id == "lc-1"
    assert decision.should_block_generation is False


def test_langchain_adapter_supports_document_objects() -> None:
    class Retriever:
        def similarity_search(self, query: str, k: int = 4) -> list[FrameworkDocument]:
            return [FrameworkDocument(query, {"source_type": "drive"}, "langchain-1")][:k]

    results = LangChainRetrieverAdapter(Retriever()).search("deadline", top_k=1)

    assert results[0].document.id == "langchain-1"
    assert results[0].document.source_type == "drive"


def test_llamaindex_adapter_supports_node_with_score_objects() -> None:
    class Node:
        node_id = "llama-1"
        metadata = {"source_type": "wiki"}

        def get_content(self) -> str:
            return "Implementation deadline is approved."

    class NodeWithScore:
        node = Node()
        score = 0.87

    class Retriever:
        def retrieve(self, query: str) -> list[NodeWithScore]:
            assert query == "deadline"
            return [NodeWithScore()]

    results = LlamaIndexRetrieverAdapter(Retriever()).search("deadline", top_k=1)

    assert results[0].document.id == "llama-1"
    assert results[0].score == 0.87


def test_haystack_adapter_supports_run_output() -> None:
    class HaystackDocument:
        def __init__(self) -> None:
            self.id = "haystack-1"
            self.content = "Support ticket contains the current customer request."
            self.meta = {"source_type": "ticket"}
            self.score = 0.78

    class Retriever:
        def run(self, query: str, top_k: int) -> dict[str, list[HaystackDocument]]:
            assert query == "customer request"
            assert top_k == 3
            return {"documents": [HaystackDocument()]}

    results = HaystackRetrieverAdapter(Retriever()).search("customer request", top_k=3)

    assert results[0].document.id == "haystack-1"
    assert results[0].document.source_type == "ticket"


def test_jsonl_adapter_uses_exported_retrieval_runs(tmp_path: Path) -> None:
    runs_path = tmp_path / "runs.jsonl"
    runs_path.write_text(
        json.dumps(
            {
                "query": "What is the deadline?",
                "results": [
                    {
                        "id": "jira-1",
                        "text": "Deadline is 2026-06-01.",
                        "score": 0.91,
                        "source_type": "jira",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    results = JSONLRetrievalRunAdapter(runs_path).search("What is the deadline?", top_k=1)

    assert results[0].document.id == "jira-1"


def test_http_adapter_posts_query_and_coerces_response() -> None:
    received: dict[str, Any] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            content_length = int(self.headers["Content-Length"])
            received.update(json.loads(self.rfile.read(content_length).decode("utf-8")))
            body = json.dumps(
                {
                    "results": [
                        {
                            "id": "http-1",
                            "text": "HTTP retriever returned the approved source.",
                            "score": 0.88,
                            "source_type": "api",
                        }
                    ]
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/retrieve"
        results = HTTPRetrieverAdapter(HTTPRetrieverConfig(url=url)).search("approved source", top_k=4)
    finally:
        server.shutdown()
        thread.join(timeout=2)

    assert received == {"query": "approved source", "top_k": 4}
    assert results[0].document.id == "http-1"


def test_http_adapter_rejects_relative_urls() -> None:
    with pytest.raises(ValueError, match="absolute"):
        HTTPRetrieverAdapter(HTTPRetrieverConfig(url="/retrieve"))


def test_http_adapter_rejects_header_injection() -> None:
    with pytest.raises(ValueError, match="headers"):
        HTTPRetrieverAdapter(
            HTTPRetrieverConfig(
                url="http://127.0.0.1:8080/retrieve",
                headers={"Authorization": "Bearer token\nInjected: yes"},
            )
        )


def test_cli_tests_jsonl_exported_results(tmp_path: Path) -> None:
    questions = tmp_path / "questions.jsonl"
    runs = tmp_path / "runs.jsonl"
    report = tmp_path / "report.md"
    questions.write_text(
        json.dumps(
            {
                "id": "q1",
                "question": "What is the deadline?",
                "ground_truth_document_ids": ["jira-1"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    runs.write_text(
        json.dumps(
            {
                "query": "What is the deadline?",
                "results": [{"id": "jira-1", "text": "Deadline is 2026-06-01.", "score": 1.0}],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    cli_main(
        [
            "--adapter",
            "jsonl",
            "--questions",
            str(questions),
            "--retrieval-runs",
            str(runs),
            "--report",
            str(report),
        ]
    )

    assert "Recall@k: 1.000" in report.read_text(encoding="utf-8")


def test_cli_supports_config_file_paths_relative_to_config(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    questions = fixture_dir / "questions.jsonl"
    runs = fixture_dir / "runs.jsonl"
    report = tmp_path / "out" / "report.md"
    config = tmp_path / "ragscaleguard.json"
    questions.write_text(
        json.dumps(
            {
                "id": "q1",
                "question": "What is the deadline?",
                "ground_truth_document_ids": ["jira-1"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    runs.write_text(
        json.dumps(
            {
                "query": "What is the deadline?",
                "results": [{"id": "jira-1", "text": "Deadline is 2026-06-01.", "score": 1.0}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    config.write_text(
        json.dumps(
            {
                "adapter": "jsonl",
                "questions": "fixtures/questions.jsonl",
                "retrieval_runs": "fixtures/runs.jsonl",
                "report": "out/report.md",
                "top_k": 5,
            }
        ),
        encoding="utf-8",
    )

    cli_main(["--config", str(config)])

    assert "Recall@k: 1.000" in report.read_text(encoding="utf-8")
