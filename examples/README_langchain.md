# LangChain Integration Example

This example demonstrates how to integrate an existing `LangChain` retriever with `RAGScaleGuard` to run diagnostics and generate evaluation reports.

## Prerequisites

To run this example, you need to install the optional dependencies. It uses `FAISS` and `FakeEmbeddings` to simulate a local vector store without requiring any API keys.

```bash
pip install langchain langchain-community faiss-cpu