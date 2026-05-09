# Reporting Schema

RAGScaleGuard writes JSON and Markdown reports from the same evaluation run data.

Reports are designed for retrieval review, audit trails, and debugging. They should be treated as sensitive because they can contain document IDs, source metadata, scores, and failure explanations.

## Evaluation Run

An evaluation run contains:

- `name`
- `metrics`
- `failures`
- `conflicts`
- `results`
- `artifacts`

## Metrics

The built-in metrics are:

- `recall_at_k`
- `precision_at_k`
- `citation_accuracy`
- `evaluated_queries`

These metrics show retrieval quality but do not explain all enterprise risk. Review diagnostic artefacts alongside the metrics.

## Top-k Failures

Top-k failures are emitted when a query provides ground truth document IDs and one or more expected documents are missing from the retrieved candidate set.

Fields:

- `query_id`
- `missing_ground_truth_ids`
- `retrieved_ids`
- `diagnosis`

## Conflicts

Conflict records are emitted when retrieved documents contain contradictory structured facts.

Fields:

- `field`
- `values`

`values` maps each detected value to the document IDs that contained it.

## Diagnostic Artefacts

Diagnostic artefacts are the main enterprise risk output.

Fields:

| Field | Meaning |
| --- | --- |
| `query_id` | Query identifier. |
| `query_text` | Query text used for the run. |
| `failure_mode` | Named enterprise retrieval risk. |
| `severity` | `warn` or `error`. |
| `title` | Human-readable finding title. |
| `reason` | Why the guard flagged the case. |
| `expected_source_ids` | Expected source IDs, when supplied. |
| `retrieved_source_ids` | Candidate IDs returned by the retriever. |
| `candidate_scores` | Retriever scores by document ID. |
| `ranking_metadata` | Rank, source, source type, status, timestamps, authority, and freshness data. |
| `freshness_signals` | Freshness score by document ID. |
| `authority_signals` | Authority score by document ID. |
| `supporting_document_ids` | Documents directly involved in the finding. |
| `suggested_remediation` | Practical next step. |
| `conflict_reason` | Conflict explanation, when applicable. |
| `evidence` | Additional mode-specific evidence. |

## Failure Modes

Current values:

- `conflicting_internal_records`
- `stale_document`
- `source_fragmentation`
- `authority_scoring_failure`
- `missing_citation_support`

## Markdown Output

Markdown reports include:

- metrics
- top-k failures
- conflicts
- diagnostic artefacts

Corpus-controlled values are escaped before being written to Markdown.

## JSON Output

JSON reports contain the full dataclass structure and are better for automation.

Common uses:

- CI artefacts
- dashboard ingestion
- audit review
- regression comparison
- failure triage

## Redaction

Reports redact common secret patterns before output.

Current redaction covers common API keys and token-like patterns. It is not a full DLP system. Teams should add their own redaction pass before sharing reports outside an authorised environment.
