from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

from ragscaleguard.diagnostics.conflict_detection import detect_conflicts
from ragscaleguard.diagnostics.density import CorpusDensityAnalyser
from ragscaleguard.diagnostics.enterprise_risks import (
    DiagnosticArtifact,
    diagnose_enterprise_risks,
)
from ragscaleguard.models import Query, SearchResult
from ragscaleguard.scoring.authority import authority_score
from ragscaleguard.scoring.freshness import freshness_score

Severity = Literal["ok", "warn", "error"]
SuggestionProvider = Callable[[Query, Sequence[SearchResult], Sequence["GuardIssue"]], Sequence[str]]


@dataclass(frozen=True)
class GuardIssue:
    stage: str
    severity: Severity
    title: str
    detail: str
    suggestion: str


@dataclass(frozen=True)
class PipelineStage:
    name: str
    severity: Severity
    status: str
    bottleneck: str | None = None


@dataclass(frozen=True)
class GuardDecision:
    query: Query
    severity: Severity
    should_block_generation: bool
    approved_results: tuple[SearchResult, ...]
    issues: tuple[GuardIssue, ...]
    diagnostic_artifacts: tuple[DiagnosticArtifact, ...]
    suggestions: tuple[str, ...]
    stages: tuple[PipelineStage, ...]

    @property
    def approved_context(self) -> tuple[str, ...]:
        return tuple(result.document.text for result in self.approved_results)


def guard_retrieval(
    query: str | Query,
    results: Sequence[SearchResult],
    *,
    block_on_conflict: bool = True,
    min_authority: float = 0.2,
    suggestion_provider: SuggestionProvider | None = None,
) -> GuardDecision:
    normalised_query = query if isinstance(query, Query) else Query("ad-hoc", query)
    result_tuple = tuple(results)
    issues: list[GuardIssue] = []
    diagnostic_artifacts = diagnose_enterprise_risks(normalised_query, result_tuple)

    density_risk = _density_risk(result_tuple)
    if density_risk >= 0.72:
        issues.append(
            GuardIssue(
                stage="Retrieve",
                severity="error",
                title="Crowded candidate set",
                detail="Retrieved evidence is tightly clustered, so the fact-bearing item can be displaced.",
                suggestion="Increase candidate depth, blend lexical retrieval, then rerank before generation.",
            )
        )
    elif density_risk >= 0.5:
        issues.append(
            GuardIssue(
                stage="Rerank",
                severity="warn",
                title="Neighbourhood pressure",
                detail="Several candidates are close enough to require stronger ranking signals.",
                suggestion="Add metadata, authority, freshness or source-specific ranking before answer synthesis.",
            )
        )

    conflicts = detect_conflicts(list(result_tuple))
    if conflicts:
        severity: Severity = "error" if block_on_conflict else "warn"
        issues.append(
            GuardIssue(
                stage="Conflict gate",
                severity=severity,
                title="Conflicting evidence",
                detail="Retrieved documents contain contradictory structured facts.",
                suggestion="Block generation or require an answer that cites and explains the conflicting sources.",
            )
        )

    low_authority = [
        result for result in result_tuple if authority_score(result.document) < min_authority
    ]
    if low_authority:
        issues.append(
            GuardIssue(
                stage="Authority check",
                severity="warn",
                title="Weak authority evidence",
                detail="Some candidates come from low-authority, stale or unverified sources.",
                suggestion="Prefer verified, final or resolved sources when packaging LLM context.",
            )
        )

    _append_artifact_issues(issues, diagnostic_artifacts)

    approved = _approved_results(result_tuple, min_authority=min_authority)
    if not approved:
        issues.append(
            GuardIssue(
                stage="LLM gate",
                severity="error",
                title="No safe context",
                detail="No retrieved evidence passed the minimum guard policy.",
                suggestion="Return a retrieval failure response instead of calling the language model.",
            )
        )

    issue_severity = _overall_severity(issues)
    should_block = issue_severity == "error"
    suggestions = _suggestions(normalised_query, result_tuple, tuple(issues), suggestion_provider)
    return GuardDecision(
        query=normalised_query,
        severity=issue_severity,
        should_block_generation=should_block,
        approved_results=tuple(approved),
        issues=tuple(issues),
        diagnostic_artifacts=diagnostic_artifacts,
        suggestions=tuple(suggestions),
        stages=_stages(issue_severity, tuple(issues), should_block),
    )


def _density_risk(results: Sequence[SearchResult]) -> float:
    documents = [result.document for result in results]
    if len(documents) < 2:
        return 0.0
    findings = CorpusDensityAnalyser(similarity_threshold=0.5).analyse(
        documents,
        nearest_k=min(3, len(documents) - 1),
    )
    if not findings:
        return 0.0
    mean_similarity = sum(finding.mean_similarity for finding in findings) / len(findings)
    dense_ratio = sum(finding.neighbours_above_threshold for finding in findings) / (
        len(findings) * max(len(documents) - 1, 1)
    )
    return min(mean_similarity * 0.65 + dense_ratio * 0.35, 1.0)


def _approved_results(results: Sequence[SearchResult], min_authority: float) -> list[SearchResult]:
    ranked = sorted(
        results,
        key=lambda result: (
            result.score * 0.55
            + authority_score(result.document) * 0.3
            + freshness_score(result.document) * 0.15
        ),
        reverse=True,
    )
    return [result for result in ranked if authority_score(result.document) >= min_authority]


def _overall_severity(issues: Sequence[GuardIssue]) -> Severity:
    if any(issue.severity == "error" for issue in issues):
        return "error"
    if any(issue.severity == "warn" for issue in issues):
        return "warn"
    return "ok"


def _suggestions(
    query: Query,
    results: Sequence[SearchResult],
    issues: Sequence[GuardIssue],
    suggestion_provider: SuggestionProvider | None,
) -> list[str]:
    base = [issue.suggestion for issue in issues]
    if not base and results:
        base.append("Proceed with approved context and keep citation checks enabled.")
    if suggestion_provider is None:
        return base
    provided = [str(item) for item in suggestion_provider(query, results, issues) if str(item).strip()]
    return [*base, *provided]


def _append_artifact_issues(
    issues: list[GuardIssue],
    artifacts: Sequence[DiagnosticArtifact],
) -> None:
    existing = {(issue.stage, issue.title) for issue in issues}
    for artifact in artifacts:
        stage = _artifact_stage(artifact)
        severity: Severity = artifact.severity
        key = (stage, artifact.title)
        if key in existing:
            continue
        issues.append(
            GuardIssue(
                stage=stage,
                severity=severity,
                title=artifact.title,
                detail=artifact.reason,
                suggestion=artifact.suggested_remediation,
            )
        )
        existing.add(key)


def _artifact_stage(artifact: DiagnosticArtifact) -> str:
    return {
        "conflicting_internal_records": "Conflict gate",
        "stale_document": "Freshness check",
        "source_fragmentation": "Retrieve",
        "authority_scoring_failure": "Authority check",
        "missing_citation_support": "Citation gate",
    }[artifact.failure_mode]


def _stages(
    severity: Severity,
    issues: Sequence[GuardIssue],
    should_block_generation: bool,
) -> tuple[PipelineStage, ...]:
    issue_by_stage = {issue.stage: issue for issue in issues}
    stage_names = (
        "Adapter",
        "Retrieve",
        "Rerank",
        "Authority check",
        "Freshness check",
        "Conflict gate",
        "Citation gate",
        "LLM gate",
        "Telemetry",
    )
    stages: list[PipelineStage] = []
    for name in stage_names:
        issue = issue_by_stage.get(name)
        if issue is not None:
            stages.append(PipelineStage(name, issue.severity, issue.title, issue.detail))
        elif name == "LLM gate" and should_block_generation:
            stages.append(PipelineStage(name, "error", "Blocked", "Generation is blocked by guard policy."))
        elif name == "Telemetry" and severity != "ok":
            stages.append(PipelineStage(name, "warn", "Log review event", "Persist diagnostics for review."))
        else:
            stages.append(PipelineStage(name, "ok", "Passed"))
    return tuple(stages)
