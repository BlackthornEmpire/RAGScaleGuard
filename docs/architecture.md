# Architecture

RAGScaleGuard is organised around explicit retrieval evidence:

1. `Document` and `Query` models carry text, metadata, and ground-truth identifiers.
2. Retrievers return `SearchResult` objects with score provenance.
3. Adapters normalise existing retrievers, services, and exported runs into that contract.
4. Diagnostics inspect candidate sets for density, missing top-k evidence, and conflicts.
5. Scoring modules provide authority, freshness, and metadata signals.
6. Rerankers combine retrieval scores with evidence quality signals.
7. The evaluation runner records metrics, failures, conflicts, and reportable traces.

Production integrations should replace the built-in hashing embedder with their embedding service or vector store, while preserving the `SearchResult` contract.

## Adapter Flow

Existing systems can connect in three ways:

1. In process through Python adapters.
2. Over HTTP through the retrieval endpoint contract.
3. Offline through JSONL exported retrieval runs.

The core evaluator only depends on the `search(query, top_k)` contract, so teams can add custom adapters without changing diagnostics, reports, or dashboard behaviour.

Config files provide the simplest repeatable path for teams: a checked-in example config can point at fixture data, while private copies can point at internal endpoints or exported retrieval runs.
