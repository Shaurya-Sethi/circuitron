from __future__ import annotations

from pathlib import Path
from typing import Optional

from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.retrievers import VectorStoreRetriever


class SkidlDocRetriever:
    """Wrapper around a LangChain vector store for SKiDL docs."""

    def __init__(self, docs_path: Path | str = "backend/data/skidl_docs") -> None:
        self.docs_path = Path(docs_path)
        embeddings = OpenAIEmbeddings()  # TODO(codex): switch to local embeddings
        self.store = FAISS.load_local(str(self.docs_path), embeddings)
        self.retriever = VectorStoreRetriever(vectorstore=self.store)

    def retrieve(self, query: str, *, tag: Optional[str] = None) -> list[Document]:
        """Retrieve documents optionally filtered by metadata tag."""
        docs = self.retriever.get_relevant_documents(query)
        if tag:
            docs = [d for d in docs if d.metadata.get("tag") == tag]
        return docs
