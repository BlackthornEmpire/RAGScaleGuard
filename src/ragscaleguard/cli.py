from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from ragscaleguard.adapters import HTTPRetrieverAdapter, HTTPRetrieverConfig, JSONLRetrievalRunAdapter
from ragscaleguard.evaluation.runner import EvaluationRunner
from ragscaleguard.evaluation.reports import to_json, to_markdown
from ragscaleguard.models import Query


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Test an existing RAG retriever with RAGScaleGuard.")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--adapter", choices=("jsonl", "http"))
    parser.add_argument("--questions", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--report-format", choices=("markdown", "json"))
    parser.add_argument("--top-k", type=int)
    parser.add_argument("--retrieval-runs", type=Path)
    parser.add_argument("--url")
    parser.add_argument("--header", action="append", default=[])
    parser.add_argument("--timeout", type=float)
    args = _merge_config(parser.parse_args(argv))

    if args.adapter not in {"jsonl", "http"}:
        raise SystemExit("--adapter must be jsonl or http")
    if args.questions is None:
        raise SystemExit("--questions is required")
    if args.report is None:
        raise SystemExit("--report is required")
    if args.top_k < 1:
        raise SystemExit("--top-k must be at least 1")

    retriever = _build_retriever(args)
    queries = [_query(row) for row in _read_jsonl(args.questions)]
    run = EvaluationRunner(retriever, name=f"{args.adapter}-adapter").run(queries, top_k=args.top_k)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    if args.report_format == "json":
        args.report.write_text(to_json(run), encoding="utf-8")
    else:
        args.report.write_text(to_markdown(run), encoding="utf-8")


def _build_retriever(args: argparse.Namespace) -> HTTPRetrieverAdapter | JSONLRetrievalRunAdapter:
    if args.adapter == "jsonl":
        if args.retrieval_runs is None:
            raise SystemExit("--retrieval-runs is required for the jsonl adapter")
        return JSONLRetrievalRunAdapter(args.retrieval_runs)
    if args.adapter == "http":
        if not args.url:
            raise SystemExit("--url is required for the http adapter")
        return HTTPRetrieverAdapter(
            HTTPRetrieverConfig(
                url=args.url,
                headers=args.headers,
                timeout_seconds=args.timeout,
            )
        )
    raise SystemExit(f"Unsupported adapter: {args.adapter}")


def _merge_config(args: argparse.Namespace) -> argparse.Namespace:
    config: dict[str, Any] = {}
    base_dir = Path.cwd()
    if args.config is not None:
        config = _read_config(args.config)
        base_dir = args.config.resolve().parent

    return argparse.Namespace(
        adapter=_pick(args.adapter, config.get("adapter")),
        questions=_path(_pick(args.questions, config.get("questions")), base_dir),
        report=_path(_pick(args.report, config.get("report")), base_dir),
        report_format=_pick(args.report_format, config.get("report_format"), "markdown"),
        top_k=_int_config(_pick(args.top_k, config.get("top_k"), 10), "top_k"),
        retrieval_runs=_path(_pick(args.retrieval_runs, config.get("retrieval_runs")), base_dir),
        url=_pick(args.url, config.get("url")),
        headers={**_config_headers(config.get("headers")), **_headers(args.header)},
        timeout=_float_config(_pick(args.timeout, config.get("timeout_seconds"), 10.0), "timeout_seconds"),
    )


def _read_config(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Config file is not valid JSON: {path}") from exc
    if not isinstance(loaded, dict):
        raise SystemExit("Config file must contain a JSON object")
    return loaded


def _pick(*values: object) -> object:
    for value in values:
        if value is not None and value != []:
            return value
    return None


def _path(value: object, base_dir: Path) -> Path | None:
    if value is None:
        return None
    path = value if isinstance(value, Path) else Path(str(value))
    if path.is_absolute():
        return path
    return base_dir / path


def _int_config(value: object, name: str) -> int:
    if isinstance(value, bool):
        raise SystemExit(f"{name} must be an integer")
    try:
        return int(str(value))
    except ValueError as exc:
        raise SystemExit(f"{name} must be an integer") from exc


def _float_config(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise SystemExit(f"{name} must be a number")
    try:
        return float(str(value))
    except ValueError as exc:
        raise SystemExit(f"{name} must be a number") from exc


def _config_headers(value: object) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise SystemExit("Config headers must be a JSON object")
    return {str(key): os.path.expandvars(str(item)) for key, item in value.items()}


def _headers(values: list[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit("--header values must be KEY=VALUE")
        key, raw = value.split("=", 1)
        if not key.strip():
            raise SystemExit("--header key cannot be empty")
        headers[key.strip()] = os.path.expandvars(raw)
    return headers


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"Line {line_number} must be a JSON object")
        rows.append(row)
    return rows


def _query(row: dict[str, Any]) -> Query:
    truth = row.get("ground_truth_document_ids") or row.get("answer_document_ids") or []
    return Query(
        id=str(row["id"]),
        text=str(row.get("question") or row.get("query") or row.get("text") or ""),
        metadata={key: value for key, value in row.items() if key not in {"id", "question", "query", "text"}},
        ground_truth_document_ids=tuple(str(item) for item in truth),
    )


if __name__ == "__main__":
    main()
