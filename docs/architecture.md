# Architecture

RAGScaleGuard is organised around explicit retrieval evidence:

1. `Document` and `Query` models carry text, metadata, and ground-truth identifiers.
2. Retrievers return `SearchResult` objects with score provenance.
3. Adapters normalise existing retrievers, services, and exported runs into that contract.
4. Diagnostics inspect candidate sets for density, missing top-k evidence, conflicts, citation support, source fragmentation, stale evidence, and authority failures.
5. Scoring modules provide authority, freshness, and metadata signals.
6. Rerankers combine retrieval scores with evidence quality signals.
7. The evaluation runner records metrics, failures, conflicts, diagnostic artefacts, and reportable traces.

Production integrations should replace the built-in hashing embedder with their embedding service or vector store, while preserving the `SearchResult` contract.

## Adapter Flow

Existing systems can connect in three ways:

1. In process through Python adapters.
2. Over HTTP through the retrieval endpoint contract.
3. Offline through JSONL exported retrieval runs.

The core evaluator only depends on the `search(query, top_k)` contract, so teams can add custom adapters without changing diagnostics, reports, or dashboard behaviour.

Config files provide the simplest repeatable path for teams: a checked-in example config can point at fixture data, while private copies can point at internal endpoints or exported retrieval runs.

## Diagnostic Artefacts

`DiagnosticArtifact` is the audit contract for high-risk findings. It is emitted by the enterprise risk diagnostics and attached to guard decisions and evaluation runs.

Each artefact contains:

- query ID and query text
- failure mode
- severity
- expected source set, when supplied
- retrieved source set
- candidate scores
- ranking metadata
- freshness signals
- authority signals
- supporting document IDs
- conflict reason, when applicable
- suggested remediation

The first-class failure modes are:

- `conflicting_internal_records`
- `stale_document`
- `source_fragmentation`
- `authority_scoring_failure`
- `missing_citation_support`

This changes the framework from only reporting that retrieval degraded to explaining which enterprise risk was found and what evidence caused the guard to flag it.
