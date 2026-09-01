"""Application configuration, read from environment variables (.env supported)."""
import os

from dotenv import load_dotenv

load_dotenv()  # load variables from a local .env file if present

# --- Auth ---
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me-to-a-long-random-string")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))

# --- Database ---
# Default: a SQLite file under ./data/. Override with DATABASE_URL if you like.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/loreweaver.db")

# --- The Keeper (agent) ---
# Model string understood by init_chat_model, e.g. "openai:gpt-4o-mini",
# "anthropic:claude-haiku-4-5", or a local "ollama:llama3.1".
KEEPER_MODEL = os.getenv("KEEPER_MODEL", "openai:gpt-4o-mini")
KEEPER_TEMPERATURE = float(os.getenv("KEEPER_TEMPERATURE", "0.7"))

# Where the agent's short-term memory (LangGraph checkpointer) is stored.
CHECKPOINT_DB_PATH = os.getenv("CHECKPOINT_DB_PATH", "./data/checkpoints.db")

# --- v3: the Archivist (SQL sub-agent) ---
ARCHIVIST_MODEL = os.getenv("ARCHIVIST_MODEL", KEEPER_MODEL)

# Filesystem path to the SQLite DB, derived from DATABASE_URL (used for read-only SQL).
SQLITE_PATH = DATABASE_URL[len("sqlite:///"):] if DATABASE_URL.startswith("sqlite:///") else DATABASE_URL

# Tables the Archivist may read. Note `user` is intentionally excluded (it holds password hashes).
ARCHIVIST_TABLES = ["hero", "item", "inventory", "quest", "monster", "adventure"]

# --- v2: RAG (the Worldbook) ---
WORLDBOOK_DIR = os.getenv("WORLDBOOK_DIR", "./assets/worldbook")
CHROMA_DIR = os.getenv("CHROMA_DIR", "./data/chroma")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "worldbook")

# Embedding model: "<provider>:<name>". provider is openai | ollama | fake.
#   openai:text-embedding-3-small  |  ollama:nomic-embed-text  |  fake:256 (tests, no key)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "openai:text-embedding-3-small")

# Chunking strategy — students tune these and compare retrieval quality.
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))

# Retrieval: how many chunks, and which strategy.
#   basic  = dense vector search
#   hybrid = BM25 + dense (EnsembleRetriever)         [advanced]
#   rerank = hybrid, then a cross-encoder reranker     [advanced]
RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", "4"))
RETRIEVAL_MODE = os.getenv("RETRIEVAL_MODE", "basic")
