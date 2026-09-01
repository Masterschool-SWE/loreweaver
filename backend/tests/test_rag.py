"""Hermetic RAG test: ingest the Worldbook with fake embeddings, then retrieve.

Verifies the whole offline flow (load -> chunk -> embed -> store) and that retrieval returns
chunks from the expected source file. No API key needed (EMBEDDING_MODEL=fake, set in conftest).
"""
from app.agent.rag.ingest import run_ingest
from app.agent.rag.retriever import get_retriever, get_vectorstore


def test_ingest_and_retrieve():
    # Clear the cached vector store so we read the freshly-ingested collection.
    get_vectorstore.cache_clear()

    n_chunks = run_ingest(chunk_size=600, chunk_overlap=80)
    assert n_chunks > 0, "ingestion produced no chunks"

    get_vectorstore.cache_clear()
    hits = get_retriever(k=3, mode="basic").invoke("What is the Cinderwyrm weak to?")
    assert hits, "retrieval returned nothing"
    sources = {h.metadata.get("source") for h in hits}
    assert "bestiary.md" in sources, f"expected bestiary.md in sources, got {sources}"
