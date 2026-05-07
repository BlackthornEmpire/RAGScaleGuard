<p align="center">
  <img src="examples/dashboard/assets/ragscaleguard-logo-lockup.png" alt="RAGScaleGuard - Reliable AI retrieval" width="560">
</p>

# RAGScaleGuard

RAGScaleGuard is an open-source retrieval hardening toolkit for enterprise RAG. It helps teams diagnose and reduce retrieval collapse caused by dense semantic neighbourhoods, near-duplicates, stale documents, fragmented sources, and conflicting internal knowledge.

The RAGScaleGuard name, shield logo, cube/orbit mark, and "Reliable AI retrieval" lock-up are official project branding. See [TRADEMARKS.md](TRADEMARKS.md) before redistributing modified versions or using the marks outside this project.

It is a practical framework for comparing retrieval strategies, finding why top-k failed, and producing auditable reports at enterprise-like scale.

## What It Does

- Measures corpus crowding and near-neighbour density.
- Compares dense-only, BM25-only, hybrid, and hybrid-plus-rerank retrieval.
- Provides authority, freshness, and metadata scoring primitives.
- Detects simple factual conflicts across retrieved evidence.
- Diagnoses cases where the answer document exists but was pushed out of top-k.
- Produces JSON and Markdown evaluation reports.
- Redacts common secrets and escapes corpus-controlled fields in reports.
- Provides deterministic unit tests and extension points for real embeddings, vector stores, and rerankers.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Minimal Demo

```bash
python examples/minimal_local_demo.py
```

## Plug Into Existing RAG Pipelines

Use `guard_retrieval` when your system already has retrieved candidates:

```python
from ragscaleguard import guard_retrieval

results = retriever.search("What changed in the rollout plan?", top_k=12)
decision = guard_retrieval("What changed in the rollout plan?", results)

if decision.should_block_generation:
    raise RuntimeError("Retrieval is not safe enough for generation")

answer = llm.generate(context="\n\n".join(decision.approved_context))
```

For retrievers that return dictionaries or document objects, wrap them with `GuardedRetriever`:

```python
from ragscaleguard.adapters import GuardedRetriever

guarded = GuardedRetriever(existing_retriever)
decision = guarded.search("What is the approved deadline?", top_k=10)
```

The guard returns pipeline stages, blocking issues, approved context, and fix suggestions. A custom suggestion provider can be attached when teams want model-generated remediation advice.

## Dashboard Demo

Open `examples/dashboard/index.html` in a browser to try a local interactive dashboard. It uses static sample values, local JavaScript, and no external network calls.

To serve it locally:

```bash
python examples/serve_dashboard.py
```

When served locally, dashboard events and error states are written to `reports/dashboard-events.jsonl`.
The local event endpoint accepts only bounded JSON events, redacts common secret fields, and rotates the event log before unbounded growth.

### Visual Walkthrough

The dashboard is designed to show the retrieval path, current quality, candidate evidence, fault states, and optional local adviser output without needing a remote service.

![Compact dashboard view](docs/assets/screenshots/dashboard-compact.png)

Run the simulation to watch the pipeline move from query intake through retrieval, density analysis, reranking, conflict checks, validation, and approved context.

![Running dashboard simulation](docs/assets/screenshots/dashboard-running.png)

Broken or risky stages turn red automatically, including the progress bar, affected pipeline nodes, metric cards, and recommendations.

![Blocked retrieval state](docs/assets/screenshots/dashboard-risk-state.png)

Full details mode exposes the operational view used for investigation: stage status, bottlenecks, fix suggestions, adapter output, adviser controls, review toggles, and the local event log.

![Full details dashboard](docs/assets/screenshots/dashboard-full-details.png)

See [docs/dashboard_walkthrough.md](docs/dashboard_walkthrough.md) for a short guide to each dashboard area.

## Local Corpus Evaluation

RAGScaleGuard can evaluate any local enterprise-style corpus represented as JSONL documents and questions. It does not bundle or require external corpora.

```bash
python examples/run_local_corpus.py \
  --documents /path/to/documents.jsonl \
  --questions /path/to/questions.jsonl \
  --report reports/local-corpus.md
```

Expected document fields are `id`, `text`, and optional `source_type`, `created_at`, `updated_at`, `author`, `project`, `customer`, `ticket_id`, `department`, `status`, and `is_verified`.

Expected question fields are `id`, `question`, and optional `ground_truth_document_ids`.

## Current Limitations

- The built-in dense retriever is a deterministic hashing baseline for reproducible tests, not a production embedding model.
- Conflict detection is conservative and rule-based.
- Generated-answer faithfulness is represented by citation and retrieval metrics until a user supplies an evaluator.
- Large-corpus performance depends on the backing retriever/vector store used by integrators.

See [docs/architecture.md](docs/architecture.md), [docs/evaluation_methodology.md](docs/evaluation_methodology.md), [docs/limitations.md](docs/limitations.md), and [docs/security_governance.md](docs/security_governance.md).
