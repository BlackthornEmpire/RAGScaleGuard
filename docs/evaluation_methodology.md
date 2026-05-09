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
