# Contributing to RAGScaleGuard

Thanks for your interest in contributing.

RAGScaleGuard is an open-source retrieval diagnostics toolkit for enterprise RAG systems.

Good areas for contribution:

- LangChain integration examples.
- LlamaIndex integration examples.
- Haystack integration examples.
- Vector database examples.
- Reranking diagnostics.
- Conflict detection improvements.
- Stale evidence and authority scoring improvements.
- Source fragmentation examples.
- Citation support evaluators.
- Diagnostic artefact exporters.
- Authority and freshness scoring.
- Dashboard improvements.
- Enterprise-style JSONL fixtures.
- Retrieval benchmark examples.
- Documentation and tutorials.
- Roadmap items in `docs/roadmap.md`.

## How to Contribute

1. Fork the repository.
2. Create a feature branch.
3. Add tests where possible.
4. Run the test suite.
5. Open a pull request explaining the change.

## Diagnostic Contributions

For new or changed enterprise risk diagnostics, please include:

- the failure mode being detected
- the metadata needed for the detector to work well
- a fixture showing the failure
- a test covering the expected artefact
- documentation updates in `docs/enterprise_risk_diagnostics.md` or `docs/reporting_schema.md`

Diagnostics should produce explainable artefacts rather than only changing a score.

## Reporting Issues

When opening an issue, please include:

- What you were trying to test.
- Input format used.
- Expected behaviour.
- Actual behaviour.
- Error output, if any.
