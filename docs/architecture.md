# Architecture

RAGScaleGuard is organised around explicit retrieval evidence:

1. `Document` and `Query` models carry text, metadata, and ground-truth identifiers.
2. Retrievers return `SearchResult` objects with score provenance.
3. Diagnostics inspect candidate sets for density, missing top-k evidence, and conflicts.
4. Scoring modules provide authority, freshness, and metadata signals.
5. Rerankers combine retrieval scores with evidence quality signals.
6. The evaluation runner records metrics, failures, conflicts, and reportable traces.

Production integrations should replace the built-in hashing embedder with their embedding service or vector store, while preserving the `SearchResult` contract.

