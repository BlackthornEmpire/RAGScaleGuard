from __future__ import annotations

from dataclasses import dataclass

from ragscaleguard.evaluation.runner import EvaluationRun, EvaluationRunner, Retriever
from ragscaleguard.models import Query


@dataclass(frozen=True)
class ComparisonRun:
    runs: tuple[EvaluationRun, ...]

    @property
    def best_by_recall(self) -> EvaluationRun | None:
        if not self.runs:
            return None
        return max(self.runs, key=lambda run: run.metrics.recall_at_k)


def compare_retrievers(
    retrievers: dict[str, Retriever],
    queries: list[Query],
    top_k: int = 10,
) -> ComparisonRun:
    return ComparisonRun(
        runs=tuple(
            EvaluationRunner(retriever, name=name).run(queries, top_k=top_k)
            for name, retriever in retrievers.items()
        )
    )

