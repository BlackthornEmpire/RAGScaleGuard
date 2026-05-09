from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from ragscaleguard.diagnostics.conflict_detection import Conflict, detect_conflicts
from ragscaleguard.models import Query, SearchResult
from ragscaleguard.scoring.authority import authority_score
from ragscaleguard.scoring.freshness import freshness_score

FailureMode = Literal[
    "conflicting_internal_records",
    "stale_document",
    "source_fragmentation",
    "authority_scoring_failure",
    "missing_citation_support",
]

RiskSeverity = Literal["warn", "error"]

STALE_STATUSES = {"archived", "deprecated", "draft", "expired", "old", "rejected", "stale"}
CURRENT_STATUSES = {"accepted", "approved", "current", "final", "published", "resolved", "verified"}
FRAGMENTATION_TERMS = {
    "all",
    "across",
    "combine",
    "complete",
    "every",
    "full",
    "overall",
    "summarise",
    "summary",
}
TOKEN_RE = re.compile(r"[a-z0-9]{3,}")


@dataclass(frozen=True)
class DiagnosticArtifact:
    query_id: str
    query_text: str
    failure_mode: FailureMode
    severity: RiskSeverity
    title: str
    reason: str
    expected_source_ids: tuple[str, ...]
    retrieved_source_ids: tuple[str, ...]
    candidate_scores: dict[str, float]
    ranking_metadata: dict[str, dict[str, Any]]
    freshness_signals: dict[str, float]
    authority_signals: dict[str, float]
    supporting_document_ids: tuple[str, ...]
    suggested_remediation: str
    conflict_reason: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)


def diagnose_enterprise_risks(
    query: Query,
    results: list[SearchResult] | tuple[SearchResult, ...],
) -> tuple[DiagnosticArtifact, ...]:
    result_tuple = tuple(results)
    if not result_tuple:
        return ()

    artifacts: list[DiagnosticArtifact] = []
    artifacts.extend(_conflict_artifacts(query, result_tuple))

    stale = _stale_document_artifact(query, result_tuple)
    if stale is not None:
        artifacts.append(stale)

    authority = _authority_artifact(query, result_tuple)
    if authority is not None:
        artifacts.append(authority)

    fragmentation = _source_fragmentation_artifact(query, result_tuple)
    if fragmentation is not None:
        artifacts.append(fragmentation)

    citation = _missing_citation_artifact(query, result_tuple)
    if citation is not None:
        artifacts.append(citation)

    return tuple(artifacts)


def _conflict_artifacts(
    query: Query,
    results: tuple[SearchResult, ...],
) -> list[DiagnosticArtifact]:
    artifacts: list[DiagnosticArtifact] = []
    for conflict in detect_conflicts(list(results)):
        document_ids = _conflict_document_ids(conflict)
        values = "; ".join(
            f"{value}: {', '.join(ids)}" for value, ids in sorted(conflict.values.items())
        )
        artifacts.append(
            _artifact(
                query,
                results,
                failure_mode="conflicting_internal_records",
                severity="error",
                title="Conflicting internal records",
                reason=(
                    f"Retrieved evidence gives more than one value for {conflict.field}: {values}."
                ),
                supporting_document_ids=document_ids,
                suggested_remediation=(
                    "Block generation, surface the conflicting records, and require a canonical "
                    "or human-approved source before answering."
                ),
                conflict_reason=f"{conflict.field}: {values}",
                evidence={"field": conflict.field, "values": conflict.values},
            )
        )
    return artifacts


def _stale_document_artifact(
    query: Query,
    results: tuple[SearchResult, ...],
) -> DiagnosticArtifact | None:
    top = results[0]
    top_freshness = freshness_score(top.document)
    top_status = _status(top)
    top_is_stale = top_status in STALE_STATUSES or top_freshness < 0.45
    if not top_is_stale:
        return None

    fresher_candidates = [
        result
        for result in results[1:]
        if (
            freshness_score(result.document) >= max(0.62, top_freshness + 0.2)
            or _status(result) in CURRENT_STATUSES
        )
        and authority_score(result.document) >= authority_score(top.document)
    ]
    if not fresher_candidates:
        return None

    current = fresher_candidates[0]
    return _artifact(
        query,
        results,
        failure_mode="stale_document",
        severity="error",
        title="Stale document outranked current evidence",
        reason=(
            f"The top candidate {top.document.id} looks stale, but {current.document.id} "
            "has stronger freshness or current-status signals."
        ),
        supporting_document_ids=(top.document.id, current.document.id),
        suggested_remediation=(
            "Apply freshness and status before packaging context, then prefer approved or "
            "current sources over stale high-similarity results."
        ),
        evidence={
            "top_document": top.document.id,
            "top_status": top_status,
            "top_freshness": round(top_freshness, 4),
            "current_document": current.document.id,
            "current_status": _status(current),
            "current_freshness": round(freshness_score(current.document), 4),
        },
    )


def _authority_artifact(
    query: Query,
    results: tuple[SearchResult, ...],
) -> DiagnosticArtifact | None:
    top = results[0]
    top_authority = authority_score(top.document)
    stronger_candidates = [
        result
        for result in results[1:]
        if authority_score(result.document) >= top_authority + 0.25
        and (top.score - result.score) <= 0.25
    ]
    if not stronger_candidates:
        return None

    stronger = stronger_candidates[0]
    return _artifact(
        query,
        results,
        failure_mode="authority_scoring_failure",
        severity="warn",
        title="Low-authority result outranked canonical evidence",
        reason=(
            f"The top candidate {top.document.id} has authority {top_authority:.2f}, while "
            f"{stronger.document.id} has authority {authority_score(stronger.document):.2f} "
            "and is close enough in retrieval score to deserve promotion."
        ),
        supporting_document_ids=(top.document.id, stronger.document.id),
        suggested_remediation=(
            "Promote verified, final, resolved, or canonical sources during reranking and "
            "downrank informal notes when stronger evidence is available."
        ),
        evidence={
            "top_document": top.document.id,
            "stronger_document": stronger.document.id,
            "top_authority": round(top_authority, 4),
            "stronger_authority": round(authority_score(stronger.document), 4),
        },
    )


def _source_fragmentation_artifact(
    query: Query,
    results: tuple[SearchResult, ...],
) -> DiagnosticArtifact | None:
    expected = _expected_source_ids(query)
    retrieved = _retrieved_source_ids(results)
    expected_set = set(expected)
    retrieved_set = set(retrieved)
    if len(expected_set) > 1:
        hits = tuple(doc_id for doc_id in expected if doc_id in retrieved_set)
        if len(hits) < len(expected_set):
            return _artifact(
                query,
                results,
                failure_mode="source_fragmentation",
                severity="error",
                title="Answer evidence is fragmented across missing sources",
                reason=(
                    "The question needs several evidence sources, but retrieval returned only "
                    f"{len(hits)} of {len(expected_set)} expected documents."
                ),
                supporting_document_ids=hits,
                suggested_remediation=(
                    "Increase candidate depth, group related chunks, and retrieve by project, "
                    "ticket, customer, or policy metadata before reranking."
                ),
                evidence={"missing_source_ids": tuple(sorted(expected_set - retrieved_set))},
            )

        ranks = [retrieved.index(doc_id) for doc_id in expected if doc_id in retrieved_set]
        if ranks and max(ranks) - min(ranks) >= 4:
            return _artifact(
                query,
                results,
                failure_mode="source_fragmentation",
                severity="warn",
                title="Required evidence is spread across distant ranks",
                reason=(
                    "All expected evidence was found, but the supporting documents are spread "
                    "far apart in the candidate set."
                ),
                supporting_document_ids=tuple(doc_id for doc_id in expected if doc_id in retrieved_set),
                suggested_remediation=(
                    "Cluster related evidence before final context selection so the LLM receives "
                    "a complete answer set, not isolated fragments."
                ),
                evidence={"expected_ranks": {doc_id: retrieved.index(doc_id) + 1 for doc_id in expected}},
            )

    source_types = {str(result.document.metadata.get("source_type", "")) for result in results[:6]}
    query_terms = set(TOKEN_RE.findall(query.text.lower()))
    if len(source_types - {""}) >= 3 and query_terms & FRAGMENTATION_TERMS:
        return _artifact(
            query,
            results,
            failure_mode="source_fragmentation",
            severity="warn",
            title="Multi-source answer may need grouped context",
            reason=(
                "The query asks for a broad or complete answer and the candidate set spans "
                "several source systems."
            ),
            supporting_document_ids=tuple(result.document.id for result in results[:6]),
            suggested_remediation=(
                "Bundle related candidates by entity and source type, then verify that the "
                "context covers the complete answer before generation."
            ),
            evidence={"source_types": tuple(sorted(source_types - {""}))},
        )

    return None


def _missing_citation_artifact(
    query: Query,
    results: tuple[SearchResult, ...],
) -> DiagnosticArtifact | None:
    cited_ids = _metadata_tuple(query, "cited_document_ids", "citation_document_ids")
    claims = _metadata_tuple(query, "generated_claims", "answer_claims")
    if not cited_ids and not claims:
        return None

    result_by_id = {result.document.id: result for result in results}
    missing_citations = tuple(doc_id for doc_id in cited_ids if doc_id not in result_by_id)
    if missing_citations:
        return _artifact(
            query,
            results,
            failure_mode="missing_citation_support",
            severity="error",
            title="Citation points to evidence outside the retrieved set",
            reason="The answer cites one or more documents that were not returned by retrieval.",
            supporting_document_ids=tuple(doc_id for doc_id in cited_ids if doc_id in result_by_id),
            suggested_remediation=(
                "Block the answer or rerun retrieval with citation verification before returning "
                "the response."
            ),
            evidence={"missing_citation_ids": missing_citations},
        )

    if claims and cited_ids:
        unsupported: list[dict[str, str]] = []
        for claim in claims:
            claim_tokens = _meaningful_tokens(claim)
            if not claim_tokens:
                continue
            best_overlap = 0.0
            best_doc_id = ""
            for doc_id in cited_ids:
                result = result_by_id.get(doc_id)
                if result is None:
                    continue
                overlap = _token_overlap(claim_tokens, _meaningful_tokens(result.document.text))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_doc_id = doc_id
            if best_overlap < 0.22:
                unsupported.append(
                    {"claim": claim, "best_document_id": best_doc_id, "overlap": f"{best_overlap:.2f}"}
                )
        if unsupported:
            return _artifact(
                query,
                results,
                failure_mode="missing_citation_support",
                severity="error",
                title="Cited evidence does not support the generated claim",
                reason="At least one generated claim has weak lexical support in the cited chunks.",
                supporting_document_ids=cited_ids,
                suggested_remediation=(
                    "Run citation support checks before returning the answer and require each "
                    "claim to map to a retrieved supporting chunk."
                ),
                evidence={"unsupported_claims": tuple(unsupported)},
            )

    expected = set(_expected_source_ids(query))
    if cited_ids and expected and not expected.intersection(cited_ids):
        return _artifact(
            query,
            results,
            failure_mode="missing_citation_support",
            severity="error",
            title="Citation misses the expected evidence set",
            reason="The cited documents do not overlap with the expected supporting sources.",
            supporting_document_ids=cited_ids,
            suggested_remediation=(
                "Require citations to come from the expected or highest-authority support set "
                "before answer release."
            ),
            evidence={"expected_source_ids": tuple(sorted(expected)), "cited_document_ids": cited_ids},
        )

    return None


def _artifact(
    query: Query,
    results: tuple[SearchResult, ...],
    *,
    failure_mode: FailureMode,
    severity: RiskSeverity,
    title: str,
    reason: str,
    supporting_document_ids: tuple[str, ...],
    suggested_remediation: str,
    conflict_reason: str | None = None,
    evidence: dict[str, Any] | None = None,
) -> DiagnosticArtifact:
    return DiagnosticArtifact(
        query_id=query.id,
        query_text=query.text,
        failure_mode=failure_mode,
        severity=severity,
        title=title,
        reason=reason,
        expected_source_ids=_expected_source_ids(query),
        retrieved_source_ids=_retrieved_source_ids(results),
        candidate_scores={result.document.id: round(result.score, 6) for result in results},
        ranking_metadata=_ranking_metadata(results),
        freshness_signals={
            result.document.id: round(freshness_score(result.document), 6) for result in results
        },
        authority_signals={
            result.document.id: round(authority_score(result.document), 6) for result in results
        },
        supporting_document_ids=supporting_document_ids,
        suggested_remediation=suggested_remediation,
        conflict_reason=conflict_reason,
        evidence=evidence or {},
    )


def _ranking_metadata(results: tuple[SearchResult, ...]) -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    for rank, result in enumerate(results, start=1):
        document = result.document
        updated_at = document.updated_at.isoformat() if document.updated_at is not None else None
        metadata[document.id] = {
            "rank": rank,
            "score": round(result.score, 6),
            "source": result.source,
            "source_type": document.metadata.get("source_type"),
            "status": document.metadata.get("status"),
            "updated_at": updated_at,
            "is_verified": document.metadata.get("is_verified"),
            "authority_score": round(authority_score(document), 6),
            "freshness_score": round(freshness_score(document), 6),
        }
    return metadata


def _expected_source_ids(query: Query) -> tuple[str, ...]:
    values = query.ground_truth_document_ids or _metadata_tuple(
        query,
        "expected_source_ids",
        "expected_document_ids",
        "required_source_ids",
    )
    return tuple(str(value) for value in values if str(value).strip())


def _metadata_tuple(query: Query, *keys: str) -> tuple[str, ...]:
    for key in keys:
        value = query.metadata.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            return (value,)
        try:
            return tuple(str(item) for item in value)
        except TypeError:
            return (str(value),)
    return ()


def _retrieved_source_ids(results: tuple[SearchResult, ...]) -> tuple[str, ...]:
    return tuple(result.document.id for result in results)


def _conflict_document_ids(conflict: Conflict) -> tuple[str, ...]:
    ids: list[str] = []
    for document_ids in conflict.values.values():
        ids.extend(document_ids)
    return tuple(dict.fromkeys(ids))


def _status(result: SearchResult) -> str:
    return str(result.document.metadata.get("status", "")).lower()


def _meaningful_tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower())) - FRAGMENTATION_TERMS


def _token_overlap(left: set[str], right: set[str]) -> float:
    if not left:
        return 0.0
    return len(left & right) / len(left)
