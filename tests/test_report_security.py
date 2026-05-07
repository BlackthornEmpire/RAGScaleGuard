from __future__ import annotations

from ragscaleguard.diagnostics.conflict_detection import Conflict
from ragscaleguard.diagnostics.topk_failure import TopKFailure
from ragscaleguard.evaluation.metrics import RetrievalMetrics
from ragscaleguard.evaluation.reports import to_json, to_markdown
from ragscaleguard.evaluation.runner import EvaluationRun


def test_markdown_report_escapes_dataset_controlled_values() -> None:
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
