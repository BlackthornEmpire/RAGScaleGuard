from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path so examples module can be imported during pytest collection
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.reranking_diagnostics import run_reranking_diagnostics
from ragscaleguard.evaluation.comparison import compare_retrievers
from ragscaleguard.models import Document, Query
from ragscaleguard.pipelines.hybrid_rerank import HybridRerankPipeline
from ragscaleguard.retrieval.hybrid import HybridRetriever


def test_reranking_diagnostics_script_execution() -> None:
    # Run the full example script
    run_reranking_diagnostics()

    # Verify that the report file was created and contains expected content
    reports_dir = Path(__file__).resolve().parents[1] / "reports"
    report_file = reports_dir / "reranking_diagnostics_report.md"
    assert report_file.exists()

    content = report_file.read_text(encoding="utf-8")
    assert "baseline" in content
    assert "reranked" in content
    assert "Best by recall@k:" in content


def test_reranking_promotes_canonical_evidence() -> None:

    documents = [
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
    ]
    queries = [
        Query(
            id="q_success",
            text="What is the approved rollout deadline for Project Atlas?",
            ground_truth_document_ids=("atlas-approved",),
            metadata={"expected_source_ids": ["atlas-approved"]},
        ),
    ]

    retrievers = {
        "baseline": HybridRetriever(documents),
        "reranked": HybridRerankPipeline(documents),
    }

    comparison = compare_retrievers(retrievers, queries, top_k=1)
    
    assert len(comparison.runs) == 2
    baseline_run = comparison.runs[0]
    reranked_run = comparison.runs[1]


    assert baseline_run.metrics.recall_at_k == 0.0

    assert reranked_run.metrics.recall_at_k == 1.0


def test_reranking_cannot_recover_unretrieved_evidence() -> None:
    # Setup test case for top-k displacement failure
    documents = [
        Document(f"noise{i}", "What is the SLA escalation policy? Routine ticket.", {"status": "approved"})
        for i in range(5)
    ] + [Document("sla-policy", "Enterprise SLA escalation after 2 hours.", {"status": "approved"})]

    queries = [
        Query("q2", "What is the SLA escalation policy?", ground_truth_document_ids=("sla-policy",))
    ]

    retrievers = {
        "baseline": HybridRetriever(documents),
        "reranked": HybridRerankPipeline(documents),
    }

    comparison = compare_retrievers(retrievers, queries, top_k=1)

    # baseline, noise documents occupy top 5 slots
    assert comparison.runs[0].metrics.recall_at_k == 0.0

    assert comparison.runs[1].metrics.recall_at_k == 0.0
