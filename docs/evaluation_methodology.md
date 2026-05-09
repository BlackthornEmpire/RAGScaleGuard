# Evaluation Methodology

Recommended comparisons:

- Dense vector only
- BM25 only
- Hybrid retrieval
- Hybrid plus reranker
- Hybrid plus reranker plus metadata-aware scoring
- Pipeline comparison with conflict detection and reporting

Primary retrieval metrics are recall@k, precision@k, citation accuracy, top-k failure count, conflict count, and diagnostic artefact count. Answer faithfulness should be measured with a project-approved evaluator when answer generation is enabled.

Enterprise risk diagnostics should be reviewed alongside the metrics. These diagnostics focus on cases that can create confident but unsupported answers:

- conflicting internal records
- stale documents outranking current evidence
- source fragmentation across chunks or systems
- low-authority evidence outranking canonical sources
- missing citation support

Each diagnostic artefact should give enough evidence for investigation: query, expected source set, retrieved source set, scores, ranking metadata, freshness signals, authority signals, conflict reason, and why the guard flagged the case.

Existing RAG systems can be evaluated through the same metrics by connecting a Python adapter, HTTP retrieval endpoint, or JSONL exported run. This keeps comparisons consistent even when teams use different retrievers, vector stores, or orchestration frameworks.

For scale testing, run each retrieval strategy at multiple corpus sizes and track where neighbourhood density starts correlating with recall loss.

## Recommended Review Flow

1. Run a baseline retriever.
2. Run the hardened retriever or guarded adapter.
3. Compare recall@k, precision@k, and citation accuracy.
4. Review top-k failures.
5. Review conflicts.
6. Review diagnostic artefacts.
7. Fix the highest-risk artefacts first.

Prioritise artefacts that can create confident unsupported answers before tuning lower-risk ranking quality issues.

## Failure Mode Priority

Recommended triage order:

1. `conflicting_internal_records`
2. `missing_citation_support`
3. `stale_document`
4. `source_fragmentation`
5. `authority_scoring_failure`

This order reflects business risk rather than implementation difficulty. Teams may choose a different order for their own domain, but the report should make the tradeoff explicit.

See [enterprise_risk_diagnostics.md](enterprise_risk_diagnostics.md) for detector behaviour and [reporting_schema.md](reporting_schema.md) for the output contract.
