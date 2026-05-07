# Security And Governance

RAGScaleGuard handles the kind of data that enterprises normally classify as confidential: emails, support tickets, customer context, internal decisions, source-code discussions, meeting transcripts, and policy documents.

## Data Handling Requirements

- Keep raw enterprise corpora in `data/`, which is ignored by git.
- Keep generated reports in `reports/`, which is ignored by git.
- Do not log raw document text in CI.
- Redact reports before sharing outside the authorised team.
- Treat document IDs as sensitive when they encode customer names, ticket IDs, employee names, or repository paths.

## Governance Controls The Toolkit Should Support

- Source authority scoring: final specs and resolved tickets should outrank stale chat.
- Freshness scoring: current artefacts should be preferred where facts change over time.
- Metadata-aware constraints: project, customer, source type, date, owner, and department should be usable as retrieval signals.
- Conflict detection: contradictory evidence should be surfaced rather than hidden behind a single generated answer.
- Auditability: reports should show which retrieval strategy produced which evidence set.
- Evaluation integrity: held-out evaluation data must not be used for model training.

## Enterprise Deployment Checklist

- Run evaluations inside a controlled working directory or container.
- Pin dependencies and run `pytest`, `mypy`, and `ruff` in CI.
- Decide whether hosted rerankers or answer evaluators are allowed to receive document text.
- Record corpus version, corpus size, retriever settings, embedding model, reranker model, and top-k.
- Review report artefacts before publishing external summaries or case studies.
