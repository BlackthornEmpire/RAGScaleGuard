from __future__ import annotations

import sys
from pathlib import Path

# Ensure src is on sys.path when running example directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragscaleguard.evaluation.comparison import compare_retrievers
from ragscaleguard.evaluation.reports import comparison_to_markdown, to_markdown
from ragscaleguard.models import Document, Query
from ragscaleguard.pipelines.hybrid_rerank import HybridRerankPipeline
from ragscaleguard.retrieval.hybrid import HybridRetriever


def run_reranking_diagnostics() -> None:
    print("=== RAGScaleGuard Reranking Diagnostics Example ===\n")
    
    # 1. Setup Corpus with Enterprise Metadata
    documents = [
        # Case 1 Documents: Project Atlas
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

        # Case 2 Documents: Reactor B Emergency Override
        Document(
            id="reactor-noise1",
            text="What is the secret manual override code for reactor B? Check routine log 1.",
            metadata={"source_type": "confluence", "status": "approved", "is_verified": True, "created_at": "2026-05-01T10:00:00Z"},
        ),
        Document(
            id="reactor-noise2",
            text="What is the secret manual override code for reactor B? Check routine log 2.",
            metadata={"source_type": "confluence", "status": "approved", "is_verified": True, "created_at": "2026-05-01T10:00:00Z"},
        ),
        Document(
            id="reactor-noise3",
            text="What is the secret manual override code for reactor B? Check routine log 3.",
            metadata={"source_type": "confluence", "status": "approved", "is_verified": True, "created_at": "2026-05-01T10:00:00Z"},
        ),
        Document(
            id="reactor-noise4",
            text="What is the secret manual override code for reactor B? Check routine log 4.",
            metadata={"source_type": "confluence", "status": "approved", "is_verified": True, "created_at": "2026-05-01T10:00:00Z"},
        ),
        Document(
            id="reactor-noise5",
            text="What is the secret manual override code for reactor B? Check routine log 5.",
            metadata={"source_type": "confluence", "status": "approved", "is_verified": True, "created_at": "2026-05-01T10:00:00Z"},
        ),
        Document(
            id="reactor-override",
            text="Manual override code 99382 for reactor B emergency shutdown.",
            metadata={"source_type": "confluence", "status": "approved", "is_verified": True, "created_at": "2026-05-01T10:00:00Z"},
        ),
    ]

    # 2. Setup Evaluation Queries
    queries = [
        Query(
            id="q_success",
            text="What is the approved rollout deadline for Project Atlas?",
            ground_truth_document_ids=("atlas-approved",),
            metadata={"expected_source_ids": ["atlas-approved"]},
        ),
        Query(
            id="q_failure",
            text="What is the secret manual override code for reactor B?",
            ground_truth_document_ids=("reactor-override",),
            metadata={"expected_source_ids": ["reactor-override"]},
        ),
    ]

    # 3. Define Retrievers to Compare
    # We compare baseline Hybrid retrieval vs. Hybrid + Heuristic Reranking
    retrievers = {
        "baseline (hybrid)": HybridRetriever(documents),
        "reranked (hybrid + rerank)": HybridRerankPipeline(documents),
    }

    print("Running evaluation comparing baseline retrieval vs. reranked retrieval at top_k=1...\n")
    comparison = compare_retrievers(retrievers, queries, top_k=1)

    # 4. Generate Reports
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

    # 5. Print Detailed Insights
    print("=== Diagnostic Insights ===")
    print("1. Reranking Success Case (Query: q_success):")
    print("   - In baseline retrieval, 'atlas-stale' (a draft Slack note from 2021) ranked #1 due to exact token matching.")
    print("   - In reranked retrieval, 'atlas-approved' (an approved Confluence doc) was promoted to #1 using authority and freshness signals.")
    print("2. Reranking Failure Case (Query: q_failure):")
    print("   - 'reactor-override' was pushed out of the initial candidate pool (top 5) by semantic crowding from routine logs.")
    print("   - Because the correct document was never retrieved in the baseline candidates, reranking could not promote it into top-k.")


if __name__ == "__main__":
    run_reranking_diagnostics()
