# Evaluation Methodology

Recommended comparisons:

- Dense vector only
- BM25 only
- Hybrid retrieval
- Hybrid plus reranker
- Hybrid plus reranker plus metadata-aware scoring
- Pipeline comparison with conflict detection and reporting

Primary retrieval metrics are recall@k, precision@k, citation accuracy, top-k failure count, and conflict count. Answer faithfulness should be measured with a project-approved evaluator when answer generation is enabled.

For scale testing, run each retrieval strategy at multiple corpus sizes and track where neighbourhood density starts correlating with recall loss.
