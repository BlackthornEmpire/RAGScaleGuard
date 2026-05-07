from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragscaleguard.adapters import GuardedRetriever


class ExistingRetriever:
    def search(self, query: str, top_k: int = 10) -> list[dict[str, object]]:
        return [
            {
                "id": "ticket-123",
                "text": f"{query}: approved deadline is 2026-06-01.",
                "score": 0.92,
                "metadata": {
                    "source_type": "ticket",
                    "status": "resolved",
                    "updated_at": "2026-05-01T09:00:00Z",
                },
            }
        ][:top_k]


decision = GuardedRetriever(ExistingRetriever()).search("What is the approved deadline?", top_k=5)

print(f"Severity: {decision.severity}")
print(f"Block generation: {decision.should_block_generation}")
print(f"Approved context count: {len(decision.approved_context)}")
for suggestion in decision.suggestions:
    print(f"- {suggestion}")
