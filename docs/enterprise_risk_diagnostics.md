# Enterprise Risk Diagnostics

RAGScaleGuard now treats the highest-risk enterprise retrieval failures as first-class diagnostic artefacts.

The goal is not only to say that recall or precision dropped. The goal is to explain when retrieval can create a confident but unsupported answer before the LLM is called.

## What Gets Flagged

### Conflicting Internal Records

Flags cases where retrieved sources contain different values for the same structured fact.

Example:

- a current policy says `deadline is 2026-05-20`
- an older chat thread says `deadline is 2026-06-01`

Why it matters:

The model can produce a confident answer from whichever source appears strongest unless the conflict is surfaced.

Recommended action:

Block generation or return a conflict response until the canonical source is selected.

### Stale Document Outranking Current Evidence

Flags cases where the top result looks stale but a fresher or approved source exists nearby in the candidate set.

Signals used:

- `updated_at`
- `created_at`
- `status`
- `is_verified`
- source authority

Recommended action:

Apply freshness and status during reranking, then prefer approved or current sources over stale high-similarity results.

### Source Fragmentation

Flags cases where the answer needs multiple sources but retrieval returns only part of the expected evidence set.

This is strongest when the query supplies `ground_truth_document_ids`, `expected_source_ids`, `expected_document_ids`, or `required_source_ids`.

Recommended action:

Increase candidate depth, group related chunks by metadata, and retrieve by project, ticket, customer, policy, or source family before reranking.

### Authority Scoring Failure

Flags cases where a low-authority result outranks a stronger canonical source that is close enough in retrieval score.

Example:

- Slack note ranks first
- approved Confluence policy ranks second
- scores are close enough that authority should change the order

Recommended action:

Promote verified, approved, final, resolved, or canonical sources and downrank informal notes when stronger evidence is available.

### Missing Citation Support

Flags cases where the generated answer cites a document that was not retrieved or where the cited document does not support the generated claim.

Signals used when supplied:

- `cited_document_ids`
- `citation_document_ids`
- `generated_claims`
- `answer_claims`
- expected source IDs

Recommended action:

Run citation support checks before returning the answer and require each claim to map to a retrieved supporting chunk.

## Diagnostic Artefact Contract

Each finding is emitted as a `DiagnosticArtifact` with:

- `query_id`
- `query_text`
- `failure_mode`
- `severity`
- `title`
- `reason`
- `expected_source_ids`
- `retrieved_source_ids`
- `candidate_scores`
- `ranking_metadata`
- `freshness_signals`
- `authority_signals`
- `supporting_document_ids`
- `suggested_remediation`
- `conflict_reason`
- `evidence`

The artefact is attached to:

- `GuardDecision.diagnostic_artifacts`
- `EvaluationRun.artifacts`
- JSON reports
- Markdown reports
- the dashboard full-details view

## Input Fields That Improve Diagnostics

RAGScaleGuard works with basic `id`, `text`, and `score` fields, but richer metadata improves the quality of enterprise diagnostics.

Useful document metadata:

- `source_type`
- `status`
- `updated_at`
- `created_at`
- `is_verified`
- `project`
- `customer`
- `ticket_id`
- `department`
- `author`

Useful question metadata:

- `ground_truth_document_ids`
- `expected_source_ids`
- `expected_document_ids`
- `required_source_ids`
- `cited_document_ids`
- `citation_document_ids`
- `generated_claims`
- `answer_claims`

## Guard Behaviour

High-risk artefacts are converted into guard issues and pipeline stages.

Blocking cases include:

- conflicting internal records
- stale evidence outranking current evidence
- missing citation support
- missing required source fragments

Warning cases include:

- authority scoring failure
- distant but present evidence fragments
- broad multi-source answers that may need grouped context

The default behaviour is conservative. It is designed to stop unsafe context before generation, not to guarantee answer truth by itself.
