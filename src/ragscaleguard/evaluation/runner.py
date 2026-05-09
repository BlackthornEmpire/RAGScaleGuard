from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ragscaleguard.diagnostics.conflict_detection import Conflict, detect_conflicts
from ragscaleguard.diagnostics.enterprise_risks import (
    DiagnosticArtifact,
    diagnose_enterprise_risks,
)
from ragscaleguard.diagnostics.topk_failure import TopKFailure, diagnose_topk_failure
from ragscaleguard.evaluation.metrics import RetrievalMetrics, evaluate_retrieval
from ragscaleguard.models import Query, SearchResult


class Retriever(Protocol):
    def search(self, query: str, top_k: int = 10) -> list[SearchResult]: ...


@dataclass(frozen=True)
class EvaluationRun:
    name: str
    metrics: RetrievalMetrics
    failures: tuple[TopKFailure, ...]
    conflicts: tuple[Conflict, ...]
    results: dict[str, tuple[str, ...]]
    artifacts: tuple[DiagnosticArtifact, ...] = ()


class EvaluationRunner:
    def __init__(self, retriever: Retriever, name: str) -> None:
        self.retriever = retriever
        self.name = name

    def run(self, queries: list[Query], top_k: int = 10) -> EvaluationRun:
        raw_runs: dict[Query, list[SearchResult]] = {}
        failures: list[TopKFailure] = []
        conflicts: list[Conflict] = []
        artifacts: list[DiagnosticArtifact] = []
        result_ids: dict[str, tuple[str, ...]] = {}
        for query in queries:
            results = self.retriever.search(query.text, top_k=top_k)
            raw_runs[query] = results
            result_ids[query.id] = tuple(result.document.id for result in results)
            failure = diagnose_topk_failure(query, results)
            if failure is not None:
                failures.append(failure)
            conflicts.extend(detect_conflicts(results))
            artifacts.extend(diagnose_enterprise_risks(query, results))
        return EvaluationRun(
            name=self.name,
            metrics=evaluate_retrieval(raw_runs),
            failures=tuple(failures),
            conflicts=tuple(conflicts),
            results=result_ids,
            artifacts=tuple(artifacts),
        )
