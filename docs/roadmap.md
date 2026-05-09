# Roadmap

RAGScaleGuard is focused on retrieval failure before generation. The near-term roadmap is intentionally narrow: make high-risk enterprise retrieval failures easier to reproduce, explain, and fix.

## Current Priorities

1. Improve conflicting internal record detection.
2. Improve stale evidence detection with richer status and version metadata.
3. Add stronger source fragmentation fixtures and examples.
4. Add stronger citation support evaluators for generated claims.
5. Improve authority scoring configuration for organisation-specific source hierarchies.
6. Add more end-to-end examples for existing RAG stacks and vector databases.
7. Add run manifests for corpus version, retriever settings, model versions, and report provenance.

## Diagnostic Artefact Direction

Every serious retrieval finding should emit a useful artefact, not only a score.

The artefact should explain:

- the query
- expected source set, where supplied
- retrieved source set
- candidate scores
- ranking metadata
- freshness and authority signals
- conflict reason, when relevant
- why the guard flagged the case
- suggested remediation

See [enterprise_risk_diagnostics.md](enterprise_risk_diagnostics.md) and [reporting_schema.md](reporting_schema.md).

## Contribution Areas

Good contribution areas:

- framework-specific integration examples
- vector database examples
- citation support evaluators
- richer conflict detection
- source fragmentation test fixtures
- report exporters
- dashboard investigation views
- security and governance templates

## Non-Goals

RAGScaleGuard is not intended to replace a RAG platform, vector database, tracing platform, or answer evaluation suite.

It is intended to make retrieval failure visible before unsafe context reaches generation.
