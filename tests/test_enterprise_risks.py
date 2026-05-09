from __future__ import annotations

from ragscaleguard.diagnostics.enterprise_risks import diagnose_enterprise_risks
from ragscaleguard.evaluation.runner import EvaluationRunner
from ragscaleguard.integrations.guard import guard_retrieval
from ragscaleguard.models import Document, Query, SearchResult


def _result(
    document_id: str,
    text: str,
    score: float,
    *,
    source_type: str,
    status: str | None = None,
    updated_at: str | None = None,
    is_verified: bool | None = None,
) -> SearchResult:
    metadata: dict[str, object] = {"source_type": source_type}
    if status is not None:
        metadata["status"] = status
    if updated_at is not None:
        metadata["updated_at"] = updated_at
    if is_verified is not None:
        metadata["is_verified"] = is_verified
    return SearchResult(Document(document_id, text, metadata), score, "test")


def test_conflicting_internal_records_emit_diagnostic_artefact() -> None:
    query = Query("q-conflict", "What is the deadline?")
    results = [
        _result("policy", "Deadline is 2026-05-20.", 0.91, source_type="confluence"),
        _result("chat", "Deadline is 2026-06-01.", 0.88, source_type="slack"),
    ]

    artifacts = diagnose_enterprise_risks(query, results)

    assert artifacts[0].failure_mode == "conflicting_internal_records"
    assert artifacts[0].severity == "error"
    assert artifacts[0].supporting_document_ids == ("policy", "chat")
    assert "deadline" in (artifacts[0].conflict_reason or "")


def test_stale_document_detection_flags_old_top_candidate() -> None:
    query = Query("q-stale", "What is the current policy?")
    results = [
        _result(
            "old-note",
            "Policy is from the old rollout.",
            0.94,
            source_type="slack",
            status="stale",
            updated_at="2022-01-01T00:00:00Z",
        ),
        _result(
            "current-policy",
            "Current approved policy.",
            0.86,
            source_type="confluence",
            status="approved",
            updated_at="2099-01-01T00:00:00Z",
            is_verified=True,
        ),
    ]

    artifacts = diagnose_enterprise_risks(query, results)

    assert any(artifact.failure_mode == "stale_document" for artifact in artifacts)
    stale = next(artifact for artifact in artifacts if artifact.failure_mode == "stale_document")
    assert stale.supporting_document_ids == ("old-note", "current-policy")
    assert stale.evidence["top_status"] == "stale"


def test_source_fragmentation_detection_flags_missing_required_sources() -> None:
    query = Query(
        "q-fragmented",
        "Summarise the full customer escalation.",
        ground_truth_document_ids=("email", "ticket", "meeting"),
    )
    results = [
        _result("email", "Customer request.", 0.9, source_type="gmail"),
        _result("ticket", "Support ticket.", 0.82, source_type="jira"),
    ]

    artifacts = diagnose_enterprise_risks(query, results)

    assert any(artifact.failure_mode == "source_fragmentation" for artifact in artifacts)
    fragmentation = next(
        artifact for artifact in artifacts if artifact.failure_mode == "source_fragmentation"
    )
    assert fragmentation.severity == "error"
    assert fragmentation.evidence["missing_source_ids"] == ("meeting",)


def test_authority_scoring_failure_flags_informal_top_result() -> None:
    query = Query("q-authority", "What is the approved deadline?")
    results = [
        _result("slack-note", "Probably launches in June.", 0.91, source_type="slack"),
        _result(
            "approved-spec",
            "Approved deadline is 2026-06-01.",
            0.84,
            source_type="confluence",
            status="approved",
            is_verified=True,
        ),
    ]

    artifacts = diagnose_enterprise_risks(query, results)

    assert any(artifact.failure_mode == "authority_scoring_failure" for artifact in artifacts)
    authority = next(
        artifact for artifact in artifacts if artifact.failure_mode == "authority_scoring_failure"
    )
    assert authority.supporting_document_ids == ("slack-note", "approved-spec")


def test_missing_citation_support_flags_unsupported_generated_claim() -> None:
    query = Query(
        "q-citation",
        "What is the approved deadline?",
        metadata={
            "generated_claims": ["The approved deadline is 2026-06-01."],
            "cited_document_ids": ["customer-email"],
        },
        ground_truth_document_ids=("approved-spec",),
    )
    results = [
        _result("customer-email", "Customer asked for roadmap visibility.", 0.9, source_type="gmail"),
        _result(
            "approved-spec",
            "Approved deadline is 2026-06-01.",
            0.86,
            source_type="confluence",
        ),
    ]

    artifacts = diagnose_enterprise_risks(query, results)

    assert any(artifact.failure_mode == "missing_citation_support" for artifact in artifacts)
    citation = next(
        artifact for artifact in artifacts if artifact.failure_mode == "missing_citation_support"
    )
    assert citation.severity == "error"
    assert citation.supporting_document_ids == ("customer-email",)


def test_guard_decision_includes_enterprise_artefacts_and_blocks_high_risk_cases() -> None:
    results = [
        _result("current", "Deadline is 2026-05-20.", 0.9, source_type="confluence"),
        _result("old", "Deadline is 2026-06-01.", 0.8, source_type="slack"),
    ]

    decision = guard_retrieval("What is the deadline?", results)

    assert decision.should_block_generation is True
    assert any(
        artifact.failure_mode == "conflicting_internal_records"
        for artifact in decision.diagnostic_artifacts
    )
    assert any(issue.title == "Conflicting internal records" for issue in decision.issues)


def test_evaluation_runner_collects_diagnostic_artefacts() -> None:
    class Retriever:
        def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
            return [
                _result("policy", "Status is approved.", 0.9, source_type="confluence"),
                _result("chat", "Status is rejected.", 0.8, source_type="slack"),
            ][:top_k]

    run = EvaluationRunner(Retriever(), "fixture").run([Query("q1", "What is the status?")])

    assert len(run.artifacts) == 1
    assert run.artifacts[0].failure_mode == "conflicting_internal_records"
