from __future__ import annotations

from ragscaleguard.diagnostics.enterprise_risks import DiagnosticArtifact
from ragscaleguard.diagnostics.conflict_detection import Conflict
from ragscaleguard.diagnostics.topk_failure import TopKFailure
from ragscaleguard.evaluation.metrics import RetrievalMetrics
from ragscaleguard.evaluation.reports import to_json, to_markdown
from ragscaleguard.evaluation.runner import EvaluationRun


def test_markdown_report_escapes_corpus_controlled_values() -> None:
    run = EvaluationRun(
        name="eval [link](https://example.com)",
        metrics=RetrievalMetrics(0.0, 0.0, 0.0, 1),
        failures=(
            TopKFailure(
                query_id="q`1",
                missing_ground_truth_ids=("doc](https://evil.example)",),
                retrieved_ids=(),
                diagnosis="missing",
            ),
        ),
        conflicts=(Conflict("deadline", {"2026-05-20 | injected": ("doc-1",)}),),
        results={},
    )

    report = to_markdown(run)

    assert "[link](https://example.com)" not in report
    assert "doc](https://evil.example)" not in report
    assert "\\[link\\]" in report


def test_reports_redact_common_secret_patterns() -> None:
    run = EvaluationRun(
        name="secret token=abc123456789",
        metrics=RetrievalMetrics(0.0, 0.0, 0.0, 0),
        failures=(),
        conflicts=(),
        results={"q1": ("sk-testtokenvalue1234567890",)},
    )

    assert "abc123456789" not in to_markdown(run)
    assert "sk-testtokenvalue1234567890" not in to_json(run)
    assert "[REDACTED]" in to_json(run)


def test_markdown_report_includes_sanitised_diagnostic_artefacts() -> None:
    run = EvaluationRun(
        name="enterprise-risk",
        metrics=RetrievalMetrics(0.0, 0.0, 0.0, 1),
        failures=(),
        conflicts=(),
        results={"q1": ("doc-1",)},
        artifacts=(
            DiagnosticArtifact(
                query_id="q1",
                query_text="What is the deadline?",
                failure_mode="missing_citation_support",
                severity="error",
                title="Citation [bad](https://example.com)",
                reason="token=abc123456789 cited chunk does not support the claim.",
                expected_source_ids=("approved-spec",),
                retrieved_source_ids=("email", "approved-spec"),
                candidate_scores={"email": 0.92},
                ranking_metadata={"email": {"rank": 1}},
                freshness_signals={"email": 0.5},
                authority_signals={"email": 0.6},
                supporting_document_ids=("email",),
                suggested_remediation="Block generation until citation support is verified.",
            ),
        ),
    )

    report = to_markdown(run)

    assert "Diagnostic Artefacts" in report
    assert "missing\\_citation\\_support" in report
    assert "[bad](https://example.com)" not in report
    assert "abc123456789" not in report
    assert "[REDACTED]" in report
