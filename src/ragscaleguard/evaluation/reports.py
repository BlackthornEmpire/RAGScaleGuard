from __future__ import annotations

import json
from dataclasses import asdict

from ragscaleguard.evaluation.comparison import ComparisonRun
from ragscaleguard.evaluation.runner import EvaluationRun
from ragscaleguard.security.redaction import markdown_escape, redact_secrets


def to_json(run: EvaluationRun) -> str:
    return redact_secrets(json.dumps(asdict(run), indent=2, sort_keys=True))


def to_markdown(run: EvaluationRun) -> str:
    metrics = run.metrics
    lines = [
        f"# RAGScaleGuard Evaluation: {markdown_escape(run.name)}",
        "",
        "## Metrics",
        "",
        f"- Recall@k: {metrics.recall_at_k:.3f}",
        f"- Precision@k: {metrics.precision_at_k:.3f}",
        f"- Citation accuracy: {metrics.citation_accuracy:.3f}",
        f"- Evaluated queries: {metrics.evaluated_queries}",
        "",
        "## Top-k Failures",
        "",
    ]
    if run.failures:
        for failure in run.failures:
            missing = ", ".join(markdown_escape(doc_id) for doc_id in failure.missing_ground_truth_ids)
            lines.append(
                f"- `{markdown_escape(failure.query_id)}` missing {missing}"
            )
    else:
        lines.append("- None detected.")
    lines.extend(["", "## Conflicts", ""])
    if run.conflicts:
        for conflict in run.conflicts:
            values = "; ".join(
                f"{markdown_escape(value)}: {', '.join(markdown_escape(doc_id) for doc_id in ids)}"
                for value, ids in conflict.values.items()
            )
            lines.append(f"- `{markdown_escape(conflict.field)}` conflict: {values}")
    else:
        lines.append("- None detected.")
    lines.extend(["", "## Diagnostic Artefacts", ""])
    if run.artifacts:
        for artifact in run.artifacts:
            lines.extend(
                [
                    f"### {markdown_escape(artifact.title)}",
                    "",
                    f"- Query: `{markdown_escape(artifact.query_id)}`",
                    f"- Failure mode: `{markdown_escape(artifact.failure_mode)}`",
                    f"- Severity: `{markdown_escape(artifact.severity)}`",
                    f"- Reason: {markdown_escape(artifact.reason, max_length=500)}",
                    "- Expected source set: "
                    + _inline_list(artifact.expected_source_ids, empty_value="not supplied"),
                    "- Retrieved source set: "
                    + _inline_list(artifact.retrieved_source_ids, empty_value="none"),
                    "- Supporting documents: "
                    + _inline_list(artifact.supporting_document_ids, empty_value="none"),
                    f"- Remediation: {markdown_escape(artifact.suggested_remediation, max_length=500)}",
                    "",
                ]
            )
    else:
        lines.append("- None detected.")
    return redact_secrets("\n".join(lines) + "\n")


def comparison_to_markdown(comparison: ComparisonRun) -> str:
    lines = [
        "# RAGScaleGuard Retrieval Comparison",
        "",
        "| Retriever | Recall@k | Precision@k | Citation accuracy | Failures | Conflicts |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for run in comparison.runs:
        metrics = run.metrics
        lines.append(
            "| "
            f"{markdown_escape(run.name)} | "
            f"{metrics.recall_at_k:.3f} | "
            f"{metrics.precision_at_k:.3f} | "
            f"{metrics.citation_accuracy:.3f} | "
            f"{len(run.failures)} | "
            f"{len(run.conflicts)} |"
        )
    best = comparison.best_by_recall
    if best is not None:
        lines.extend(["", f"Best by recall@k: `{markdown_escape(best.name)}`"])
    return "\n".join(lines) + "\n"


def _inline_list(values: tuple[str, ...], *, empty_value: str) -> str:
    if not values:
        return markdown_escape(empty_value)
    return ", ".join(f"`{markdown_escape(value)}`" for value in values)
