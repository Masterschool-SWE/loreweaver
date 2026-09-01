"""Pytest fixtures. Hermetic: isolated DB + fake embeddings, so tests need no API keys."""
import os

# Must be set BEFORE the app (and its config) is imported.
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-32b")
os.environ["DATABASE_URL"] = "sqlite:///./data/test_v3.db"
# RAG tests use deterministic fake embeddings + a throwaway Chroma dir (no OpenAI key needed).
os.environ["EMBEDDING_MODEL"] = "fake:256"
os.environ["CHROMA_DIR"] = "./data/test_chroma"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from app.main import app  # imported here so the env above is in effect

    # The context manager triggers FastAPI's lifespan (create tables + seed).
    with TestClient(app) as c:
        yield c
