# Integrations

RAGScaleGuard can test an existing RAG system through adapters. The system under test only needs to return retrieved candidates with enough text and identity to score the run.

## Supported Routes

Use the route that matches the access you have:

- `GuardedRetriever` for simple Python retrievers.
- `LangChainRetrieverAdapter` for LangChain-style retrievers and vector stores.
- `LlamaIndexRetrieverAdapter` for LlamaIndex retrievers returning nodes or scored nodes.
- `HaystackRetrieverAdapter` for Haystack components returning documents.
- `HTTPRetrieverAdapter` for any service with a retrieval endpoint.
- `JSONLRetrievalRunAdapter` for exported retrieval runs.

## Fastest Path

Run the bundled example first:

```bash
ragscaleguard-test --config configs/ragscaleguard-jsonl.example.json
```

This reads `examples/fixtures/questions.jsonl`, tests `examples/fixtures/retrieval-runs.jsonl`, and writes a report under `reports/`.

For your own system, copy `configs/ragscaleguard-jsonl.example.json` or `configs/ragscaleguard-http.example.json`, then change the paths or endpoint URL.

## Python Guard

Use this when your application already has retrieved candidates:

```python
from ragscaleguard import guard_retrieval

results = retriever.search("What is the approved deadline?", top_k=10)
decision = guard_retrieval("What is the approved deadline?", results)

if decision.should_block_generation:
    return {
        "error": "Retrieval failed guard checks",
        "issues": decision.issues,
        "diagnostic_artifacts": decision.diagnostic_artifacts,
    }

answer = llm.generate(context="\n\n".join(decision.approved_context))
```

## Generic Retriever

Use this when your retriever exposes `search`, `retrieve`, `invoke`, `get_relevant_documents`, or `similarity_search`.

```python
from ragscaleguard.adapters import GuardedRetriever

guarded = GuardedRetriever(existing_retriever)
decision = guarded.search("Which source has the final decision?", top_k=10)
```

## Framework Adapters

```python
from ragscaleguard.adapters import (
    HaystackRetrieverAdapter,
    LangChainRetrieverAdapter,
    LlamaIndexRetrieverAdapter,
)

langchain_results = LangChainRetrieverAdapter(langchain_retriever).search("deadline", top_k=10)
llamaindex_results = LlamaIndexRetrieverAdapter(llamaindex_retriever).search("deadline", top_k=10)
haystack_results = HaystackRetrieverAdapter(haystack_retriever).search("deadline", top_k=10)
```

The adapters use structural typing. They do not import those frameworks, so projects do not need extra RAGScaleGuard dependencies just to run tests.

## HTTP Contract

Use this when your RAG system is a service.

Request:

```json
{"query": "What is the approved deadline?", "top_k": 10}
```

Response:

```json
{
  "results": [
    {
      "id": "ticket-123",
      "text": "The approved deadline is 2026-06-01.",
      "score": 0.92,
      "metadata": {
        "source_type": "ticket",
        "status": "resolved",
        "updated_at": "2026-05-01T12:00:00Z"
      }
    }
  ]
}
```

Run:

```bash
ragscaleguard-test \
  --adapter http \
  --url http://127.0.0.1:8080/retrieve \
  --questions questions.jsonl \
  --report reports/http-retriever.md
```

Or use a config file:

```json
{
  "adapter": "http",
  "url": "https://rag.example.internal/retrieve",
  "questions": "questions.jsonl",
  "report": "reports/http-retriever.md",
  "top_k": 10,
  "headers": {
    "Authorization": "Bearer $RAG_API_TOKEN"
  }
}
```

Headers can be passed without placing secrets in committed files:

```bash
RAG_API_TOKEN=token-value ragscaleguard-test \
  --adapter http \
  --url https://rag.example.internal/retrieve \
  --header Authorization='Bearer $RAG_API_TOKEN' \
  --questions questions.jsonl \
  --report reports/http-retriever.md
```

## JSONL Export Contract

Use this when the system cannot expose an endpoint.

Questions:

```jsonl
{"id":"q1","question":"What is the approved deadline?","ground_truth_document_ids":["ticket-123"]}
```

Retrieval runs:

```jsonl
{"query":"What is the approved deadline?","results":[{"id":"ticket-123","text":"The approved deadline is 2026-06-01.","score":0.92,"metadata":{"source_type":"ticket"}}]}
```

Run:

```bash
ragscaleguard-test \
  --adapter jsonl \
  --retrieval-runs retrieval-runs.jsonl \
  --questions questions.jsonl \
  --report reports/exported-runs.md
```

Or use a config file:

```json
{
  "adapter": "jsonl",
  "questions": "questions.jsonl",
  "retrieval_runs": "retrieval-runs.jsonl",
  "report": "reports/exported-runs.md",
  "top_k": 10
}
```

## Candidate Fields

RAGScaleGuard accepts common field names:

- ID: `id`, `doc_id`, or `document_id`.
- Text: `text`, `content`, `page_content`, or `body`.
- Score: `score`.
- Metadata: `metadata`, or top-level fields such as `source_type`, `updated_at`, `status`, `project`, `customer`, and `department`.

## Fields That Improve Enterprise Risk Diagnostics

Basic retrieval tests only need candidate IDs, text, and scores. Enterprise risk diagnostics become more useful when your integration also supplies source metadata and answer support metadata.

Recommended document metadata:

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

Recommended question metadata:

- `ground_truth_document_ids`
- `expected_source_ids`
- `expected_document_ids`
- `required_source_ids`
- `cited_document_ids`
- `citation_document_ids`
- `generated_claims`
- `answer_claims`

These fields let RAGScaleGuard emit stronger diagnostic artefacts for stale evidence, source fragmentation, authority failures, and weak citation support.

See [enterprise_risk_diagnostics.md](enterprise_risk_diagnostics.md) and [reporting_schema.md](reporting_schema.md) for the full artefact contract.

## Security Notes

- Keep retrieval endpoints internal unless they are separately authenticated and authorised.
- Pass secrets through environment variables, not committed files.
- Do not send raw enterprise documents to an external adviser model.
- Use JSONL export when a production system cannot safely expose a live endpoint.
- Treat diagnostic artefacts as sensitive because they can expose document IDs, source relationships, ranking metadata, and internal failure modes.
