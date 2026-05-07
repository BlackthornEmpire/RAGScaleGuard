from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ragscaleguard.adapters.base import coerce_result_list
from ragscaleguard.models import SearchResult


class JSONLRetrievalRunAdapter:
    """Adapter for retrieval results exported from any system as JSONL."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._runs = _load_runs(self.path)

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        key = query.strip()
        if not key:
            return []
        if key not in self._runs:
            return []
        return coerce_result_list(self._runs[key])[:top_k]


def _load_runs(path: Path) -> dict[str, list[dict[str, Any]]]:
    runs: dict[str, list[dict[str, Any]]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"Line {line_number} must be a JSON object")
        query = row.get("query") or row.get("question") or row.get("query_text")
        results = row.get("results") or row.get("documents")
        if not isinstance(query, str) or not isinstance(results, list):
            raise ValueError(f"Line {line_number} must include query and results")
        runs[query.strip()] = results
    return runs
