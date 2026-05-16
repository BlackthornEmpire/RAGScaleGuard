import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from langchain_core.documents import Document as LangChainDocument
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FakeEmbeddings

from ragscaleguard.adapters import LangChainRetrieverAdapter
from ragscaleguard.evaluation.comparison import compare_retrievers
from ragscaleguard.evaluation.reports import comparison_to_markdown
from ragscaleguard.models import Query

def main():
    print("1. Preparing small fixture dataset...")
    documents = [
        LangChainDocument(page_content="RAGScaleGuard is a powerful tool for evaluating RAG systems.", metadata={"id": "doc1"}),
        LangChainDocument(page_content="LangChain provides a standard interface for chains, agents, and memory.", metadata={"id": "doc2"}),
        LangChainDocument(page_content="FAISS is used to store embeddings for fast similarity search.", metadata={"id": "doc3"}),
    ]

    print("2. Setting up LangChain Retriever with FAISS...")
    embeddings = FakeEmbeddings(size=128)
    vectorstore = FAISS.from_documents(documents, embeddings)
    retriever = vectorstore.as_retriever()

    print("3. Wrapping retriever with RAGScaleGuard Adapter...")
    adapter = LangChainRetrieverAdapter(retriever)

    print("4. Preparing test queries and running diagnostics...")
    queries = [
        Query(id="q1", text="What tool evaluates RAG systems?", ground_truth_document_ids=("doc1",)),
        Query(id="q2", text="How do you store embeddings for fast search?", ground_truth_document_ids=("doc3",)),
    ]

    comparison = compare_retrievers({"langchain_faiss": adapter}, queries, top_k=2)
    
    print("5. Generating Markdown report...")
    report_md = comparison_to_markdown(comparison)
    
    report_path = Path("langchain_evaluation_report.md")
    report_path.write_text(report_md, encoding="utf-8")
    
    print(f"Example execution completed successfully! Report saved to: {report_path.resolve()}")

if __name__ == "__main__":
    main()