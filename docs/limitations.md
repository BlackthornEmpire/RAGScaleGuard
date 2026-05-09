# Limitations

- The default dense retriever is for deterministic local testing.
- Rule-based conflict detection only catches explicit field/value contradictions.
- Citation support detection is conservative and uses local signal checks unless an integrator supplies a stronger evaluator.
- Source fragmentation detection is strongest when queries include expected source IDs or useful metadata.
- Metadata-aware routing depends on metadata quality.
- Evaluation results should not be treated as production guarantees.
- Held-out evaluation data must not be included in training corpora.
- RAGScaleGuard cannot auto-discover private enterprise auth, schemas, prompts, vector stores, or retrieval endpoints.
- "Universal" means adapter-based coverage: use a native Python adapter, the HTTP contract, JSONL export, or a custom adapter when a proprietary system has a different shape.
