from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ragscaleguard.evaluation.comparison import compare_retrievers
from ragscaleguard.evaluation.reports import comparison_to_markdown
from ragscaleguard.models import Document, Query
from ragscaleguard.pipelines.hybrid_rerank import HybridRerankPipeline
from ragscaleguard.retrieval.bm25 import BM25Retriever
from ragscaleguard.retrieval.dense import DenseRetriever
from ragscaleguard.retrieval.hybrid import HybridRetriever


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--documents", required=True, type=Path)
    parser.add_argument("--questions", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--top-k", default=10, type=int)
    args = parser.parse_args()

    documents = [_document(row) for row in _read_jsonl(args.documents)]
    questions = [_query(row) for row in _read_jsonl(args.questions)]
    comparison = compare_retrievers(
        {
            "dense": DenseRetriever(documents),
            "bm25": BM25Retriever(documents),
            "hybrid": HybridRetriever(documents),
            "hybrid-rerank": HybridRerankPipeline(documents),
        },
        questions,
        top_k=args.top_k,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(comparison_to_markdown(comparison), encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _document(row: dict[str, Any]) -> Document:
    text = str(row.get("text") or row.get("content") or row.get("body") or "")
    metadata = {key: value for key, value in row.items() if key not in {"id", "text", "content", "body"}}
    return Document(id=str(row["id"]), text=text, metadata=metadata)


def _query(row: dict[str, Any]) -> Query:
    truth = row.get("ground_truth_document_ids") or row.get("answer_document_ids") or []
    return Query(
        id=str(row["id"]),
        text=str(row.get("question") or row.get("text") or ""),
        metadata={key: value for key, value in row.items() if key not in {"id", "question", "text"}},
        ground_truth_document_ids=tuple(str(item) for item in truth),
    )


if __name__ == "__main__":
    main()
