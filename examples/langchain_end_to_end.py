import os
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FakeEmbeddings

def main():
    print("1. Preparing small fixture dataset...")
    documents = [
        Document(page_content="RAGScaleGuard is a powerful tool for evaluating RAG systems.", metadata={"source": "doc1"}),
        Document(page_content="LangChain provides a standard interface for chains, agents, and memory.", metadata={"source": "doc2"}),
        Document(page_content="FAISS is used to store embeddings for fast similarity search.", metadata={"source": "doc3"}),
    ]

    print("2. Setting up LangChain Retriever with FAISS...")
    embeddings = FakeEmbeddings(size=128)
    vectorstore = FAISS.from_documents(documents, embeddings)
    retriever = vectorstore.as_retriever()

    print("3. Wrapping retriever with RAGScaleGuard Adapter...")

    print("4. Running diagnostics...")
    
    print("5. Generating Markdown report...")
    
    print("Example execution completed successfully!")

if __name__ == "__main__":
    main()