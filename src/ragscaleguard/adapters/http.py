from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from urllib.parse import urlparse

from ragscaleguard.adapters.base import coerce_result_list
from ragscaleguard.models import SearchResult

MAX_RESPONSE_BYTES = 2_000_000


@dataclass(frozen=True)
class HTTPRetrieverConfig:
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    timeout_seconds: float = 10.0
    results_path: tuple[str, ...] = ("results",)


class HTTPRetrieverAdapter:
    """Adapter for any RAG system that exposes a retrieval HTTP endpoint."""

    def __init__(self, config: HTTPRetrieverConfig) -> None:
        _validate_url(config.url)
        _validate_headers(config.headers)
        if config.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.config = config

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        payload = json.dumps({"query": query, "top_k": top_k}).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            **self.config.headers,
        }
        request = urllib.request.Request(self.config.url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Retriever endpoint request failed: {exc}") from exc
        if len(raw) > MAX_RESPONSE_BYTES:
            raise RuntimeError("Retriever endpoint response exceeded the maximum supported size")
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError("Retriever endpoint did not return valid JSON") from exc
        return coerce_result_list(_select_path(decoded, self.config.results_path))


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("HTTP retriever URL must be an absolute http or https URL")


def _validate_headers(headers: dict[str, str]) -> None:
    for key, value in headers.items():
        if not key.strip():
            raise ValueError("HTTP header names cannot be empty")
        if any(char in key or char in value for char in ("\r", "\n")):
            raise ValueError("HTTP headers cannot contain control line breaks")
        if len(key) > 128 or len(value) > 4096:
            raise ValueError("HTTP headers exceed the supported size")


def _select_path(payload: object, path: tuple[str, ...]) -> object:
    current = payload
    for key in path:
        if not isinstance(current, dict) or key not in current:
            raise RuntimeError(f"Retriever response is missing results path: {'.'.join(path)}")
        current = current[key]
    return current
