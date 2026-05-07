from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Document:
    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def source_type(self) -> str | None:
        value = self.metadata.get("source_type")
        return str(value) if value is not None else None

    @property
    def updated_at(self) -> datetime | None:
        value = self.metadata.get("updated_at") or self.metadata.get("created_at")
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None


@dataclass(frozen=True)
class Query:
    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    ground_truth_document_ids: tuple[str, ...] = ()

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass(frozen=True)
class SearchResult:
    document: Document
    score: float
    source: str
    explanation: dict[str, Any] = field(default_factory=dict)
