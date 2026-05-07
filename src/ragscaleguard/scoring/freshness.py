from __future__ import annotations

from datetime import datetime, timezone

from ragscaleguard.models import Document


def freshness_score(document: Document, now: datetime | None = None, half_life_days: int = 180) -> float:
    updated_at = document.updated_at
    if updated_at is None:
        return 0.5
    reference = now or datetime.now(timezone.utc)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    age_days = max((reference - updated_at).total_seconds() / 86_400, 0)
    return 1 / (1 + age_days / half_life_days)

