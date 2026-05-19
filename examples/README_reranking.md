# Reranking Diagnostics in RAGScaleGuard

Reranking is one of the most common techniques teams use to improve Retrieval-Augmented Generation (RAG) quality. By decoupling initial fast candidate retrieval from a secondary, more expensive scoring pass (e.g., cross-encoders or heuristic weighting), teams aim to promote the most relevant chunks to the top of the context window.

However, **reranking does not solve all retrieval failure modes**.

This example demonstrates how RAGScaleGuard evaluates and compares retrieval quality before and after reranking, helping teams diagnose when reranking succeeds and when deeper top-$k$ displacement issues remain.

## Why This Matters

When evaluating RAG retrieval, teams often encounter two distinct failure scenarios:

1. **Reranking Success (Candidate Reordering)**: The ground-truth document was successfully retrieved by the baseline retriever (BM25 or dense embedding) but placed at rank 4 or 5 due to semantic crowding or exact keyword matching from older draft notes. Reranking evaluates authority, freshness, and verified status metadata to successfully promote the canonical document to rank 1.
2. **Reranking Failure (Candidate Absence)**: The initial retrieval candidate pool (`top_k * candidate_multiplier`) is completely saturated by highly repetitive routine logs or noisy chunks. Because the ground-truth document was never retrieved in the baseline candidate set, reranking cannot recover it. Reranking can only reorder what has already been retrieved.

## Running the Example

You can run the bundled diagnostic example locally without needing any external API keys or paid services:

```bash
python examples/reranking_diagnostics.py
```

## What the Example Does

The script sets up a curated enterprise corpus containing documents with realistic metadata (`status`, `is_verified`, `source_type`, `created_at`) and runs two test queries at `top_k=1`:

- **Query 1 (`q_success`)**: *"What is the approved rollout deadline for Project Atlas?"*
  - **Baseline**: Ranks an older, stale draft note first because its exact wording matches the query tokens. Ground-truth recall@1 is 0.0.
  - **Reranked**: Promotes the verified Confluence specification (`atlas-approved`) to rank 1 based on its `approved` status and high authority score. Ground-truth recall@1 increases to 1.0.

- **Query 2 (`q_failure`)**: *"What is the SLA escalation policy for Enterprise Tier customers?"*
  - **Baseline**: Saturated by 5 identical routine Jira tickets that push the correct policy document to rank 6 (outside the candidate multiplier pool).
  - **Reranked**: Reranks the 5 routine tickets, but because the correct document is missing from the candidate pool, top-$k$ failure persists. Recall@1 remains 0.0.

## Report Output

The script outputs a summary table directly to the console and writes a full diagnostic audit report to `reports/reranking_diagnostics_report.md`.

### Summary Comparison Table

```markdown
# RAGScaleGuard Retrieval Comparison

| Retriever | Recall@k | Precision@k | Citation accuracy | Failures | Conflicts |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline (hybrid) | 0.000 | 0.000 | 0.000 | 2 | 0 |
| reranked (hybrid + rerank) | 0.500 | 0.500 | 0.500 | 1 | 0 |

Best by recall@k: `reranked (hybrid + rerank)`
```

By inspecting the detailed markdown report, teams can trace the exact reasons behind remaining top-$k$ failures and review the suggested remediations (e.g., increasing candidate depth or clustering evidence before reranking).
