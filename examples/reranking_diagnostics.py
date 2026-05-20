from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragscaleguard.evaluation.comparison import compare_retrievers
from ragscaleguard.evaluation.reports import comparison_to_markdown, to_markdown
from ragscaleguard.models import Document, Query
from ragscaleguard.pipelines.hybrid_rerank import HybridRerankPipeline
from ragscaleguard.retrieval.hybrid import HybridRetriever


def run_reranking_diagnostics() -> None:
    print("=== RAGScaleGuard Reranking Diagnostics Example ===\n")
    
    # Corpus with Enterprise Metadata
    documents = [
        # Project Atlas
        Document(
            id="atlas-stale",
            text="What is the approved rollout deadline for Project Atlas? 2025-01-01 (initial draft notes).",
            metadata={"source_type": "slack", "status": "stale", "created_at": "2021-01-01T10:00:00Z"},
        ),
        Document(
            id="atlas-noise",
            text="Project Atlas rollout sync meeting notes regarding launch prep.",
            metadata={"source_type": "slack", "status": "draft", "created_at": "2025-06-01T10:00:00Z"},
        ),
        Document(
            id="atlas-approved",
            text="The official rollout deadline for Project Atlas is confirmed and approved for 2026-06-01.",
            metadata={
                "source_type": "confluence",
                "status": "approved",
                "is_verified": True,
                "created_at": "2026-05-01T10:00:00Z",
            },
        ),

        # SLA Escalation Policy
        Document(
            id="sla-noise1",
            text="What is the SLA escalation policy for Enterprise Tier customers? Check routine ticket 1.",
            metadata={"source_type": "jira", "status": "resolved", "is_verified": True, "created_at": "2026-05-01T10:00:00Z"},
        ),
        Document(
            id="sla-noise2",
            text="What is the SLA escalation policy for Enterprise Tier customers? Check routine ticket 2.",
            metadata={"source_type": "jira", "status": "resolved", "is_verified": True, "created_at": "2026-05-01T10:00:00Z"},
        ),
        Document(
            id="sla-noise3",
            text="What is the SLA escalation policy for Enterprise Tier customers? Check routine ticket 3.",
            metadata={"source_type": "jira", "status": "resolved", "is_verified": True, "created_at": "2026-05-01T10:00:00Z"},
        ),
        Document(
            id="sla-noise4",
            text="What is the SLA escalation policy for Enterprise Tier customers? Check routine ticket 4.",
            metadata={"source_type": "jira", "status": "resolved", "is_verified": True, "created_at": "2026-05-01T10:00:00Z"},
        ),
        Document(
            id="sla-noise5",
            text="What is the SLA escalation policy for Enterprise Tier customers? Check routine ticket 5.",
            metadata={"source_type": "jira", "status": "resolved", "is_verified": True, "created_at": "2026-05-01T10:00:00Z"},
        ),
        Document(
            id="sla-policy",
            text="Enterprise Tier customers receive an automatic SLA escalation after 2 hours of inactivity.",
            metadata={"source_type": "confluence", "status": "approved", "is_verified": True, "created_at": "2026-05-01T10:00:00Z"},
        ),
    ]

    # Evaluation Queries
    queries = [
        Query(
            id="q_success",
            text="What is the approved rollout deadline for Project Atlas?",
            ground_truth_document_ids=("atlas-approved",),
            metadata={"expected_source_ids": ["atlas-approved"]},
        ),
        Query(
            id="q_failure",
            text="What is the SLA escalation policy for Enterprise Tier customers?",
            ground_truth_document_ids=("sla-policy",),
            metadata={"expected_source_ids": ["sla-policy"]},
        ),
    ]

    
    # comparing baseline Hybrid retrieval vs. Hybrid + Heuristic Reranking
    retrievers = {
        "baseline (hybrid)": HybridRetriever(documents),
        "reranked (hybrid + rerank)": HybridRerankPipeline(documents),
    }

    print("Running evaluation comparing baseline retrieval vs. reranked retrieval at top_k=1...\n")
    comparison = compare_retrievers(retrievers, queries, top_k=1)

    # Reports 
    summary_md = comparison_to_markdown(comparison)
    print(summary_md)

    baseline_md = to_markdown(comparison.runs[0])
    reranked_md = to_markdown(comparison.runs[1])

    full_report = (
        "# Reranking Diagnostics Audit Report\n\n"
        "This report demonstrates how RAGScaleGuard evaluates retrieval quality before and after reranking.\n\n"
        f"{summary_md}\n\n"
        "## Baseline Retrieval Run Details\n\n"
        f"{baseline_md}\n\n"
        "## Reranked Retrieval Run Details\n\n"
        f"{reranked_md}\n"
    )

    reports_dir = Path(__file__).resolve().parents[1] / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "reranking_diagnostics_report.md"
    report_path.write_text(full_report, encoding="utf-8")
    
    print(f"Full diagnostic report written successfully to: {report_path.relative_to(Path.cwd())}\n")

    # Detailed Insights
    print("=== Diagnostic Insights ===")
    print("1. Reranking Success Case (Query: q_success):")
    print("   - In baseline retrieval, 'atlas-stale' (a draft Slack note from 2021) ranked #1 due to exact token matching.")
    print("   - In reranked retrieval, 'atlas-approved' (an approved Confluence doc) was promoted to #1 using authority and freshness signals.")
    print("2. Reranking Failure Case (Query: q_failure):")
    print("   - 'sla-policy' was pushed out of the initial candidate pool (top 5) by semantic crowding from routine Jira tickets.")
    print("   - Because the correct document was never retrieved in the baseline candidates, reranking could not promote it into top-k.")


if __name__ == "__main__":
    run_reranking_diagnostics()
