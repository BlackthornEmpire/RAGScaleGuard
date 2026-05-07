from __future__ import annotations

import re
from dataclasses import dataclass

from ragscaleguard.models import SearchResult

FACT_RE = re.compile(
    r"\b(deadline|due date|status|owner|budget|price|launch date)\s*(?:is|:|-)\s*([^.;\n]+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Conflict:
    field: str
    values: dict[str, tuple[str, ...]]


def detect_conflicts(results: list[SearchResult]) -> list[Conflict]:
    facts: dict[str, dict[str, list[str]]] = {}
    for result in results:
        for match in FACT_RE.finditer(result.document.text):
            field = match.group(1).lower()
            value = match.group(2).strip().lower()
            facts.setdefault(field, {}).setdefault(value, []).append(result.document.id)
    conflicts: list[Conflict] = []
    for field, values in facts.items():
        if len(values) > 1:
            conflicts.append(
                Conflict(
                    field=field,
                    values={value: tuple(document_ids) for value, document_ids in values.items()},
                )
            )
    return conflicts

