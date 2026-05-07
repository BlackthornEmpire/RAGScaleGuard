from __future__ import annotations

from pathlib import Path


def test_readme_documents_universal_adapter_routes() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "Python adapters" in readme
    assert "HTTP retrieval endpoints" in readme
    assert "exported JSONL runs" in readme
    assert "LangChainRetrieverAdapter" in readme
    assert "LlamaIndexRetrieverAdapter" in readme
    assert "HaystackRetrieverAdapter" in readme
    assert "ragscaleguard-test" in readme
    assert "ragscaleguard-jsonl.example.json" in readme
    assert "docs/integrations.md" in readme


def test_integration_docs_keep_the_universal_claim_honest() -> None:
    docs = Path("docs/integrations.md").read_text(encoding="utf-8")
    limitations = Path("docs/limitations.md").read_text(encoding="utf-8")

    assert "HTTP Contract" in docs
    assert "JSONL Export Contract" in docs
    assert "Fastest Path" in docs
    assert "Candidate Fields" in docs
    assert "custom adapters" in docs or "custom adapter" in limitations
    assert "cannot auto-discover" in limitations
