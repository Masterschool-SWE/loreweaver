# Loreweaver

A solo tabletop RPG in the realm of **Aethelgard**. Players create a hero and talk to **the Keeper**, a Game Master agent that narrates the adventure, looks up canon in the Worldbook, and delegates questions about saved game data to **the Archivist**, a read-only SQL sub-agent.

The app is a FastAPI backend plus a Streamlit client. Conversation memory, RAG, nested agents, optional Langfuse tracing, and a Ragas RAG eval are all included.

## Features

- **Accounts and heroes** — register/login (JWT), create and select a hero
- **The Keeper** — LangChain agent that runs the session in second person, with per-hero memory
- **Worldbook RAG** — lore, rules, bestiary, and items ingested into Chroma; optional hybrid (BM25) and rerank modes
- **The Archivist** — agent-as-a-tool: the Keeper asks a SQL expert instead of inventing inventory, quests, or gold
- **Structured encounters** — forge a validated combat/story encounter from a scene
- **Optional web search** — Tavily, only if a key is set
- **Optional tracing** — Langfuse nested traces: Keeper → Archivist → `execute_sql`
- **RAG evaluation** — Ragas scores over a small golden set

Demo login: `demo` / `demo1234` (hero **Thalia Emberkin**).

## Architecture

```
Streamlit  ──HTTP──▶  FastAPI
                        ├─ /auth, /heroes
                        └─ /agent/invoke
                             └─ Keeper  (tools)
                                  ├─ search_worldbook  →  Chroma (Worldbook)
                                  ├─ Tavily            →  web (optional)
                                  └─ ask_archivist     →  Archivist
                                                           └─ execute_sql (SELECT-only SQLite)
```

Each hero has one adventure `thread_id`. The Keeper’s message history is stored in a LangGraph SQLite checkpointer, so the story continues across turns.

When you ask something like *“how many quests have I completed?”*:

```
You
 └─ Keeper  ── ask_archivist("how many quests has hero 1 completed?") ──▶  Archivist
                                                                              └─ execute_sql("SELECT COUNT(*) ... WHERE status='completed'")
  ◀── "You've completed 1 quest." ────────────────────────────────────────────┘
```

If Langfuse keys are set, that nested run shows up as one trace.

## Stack

| Layer | |
|---|---|
| API | FastAPI, SQLModel, SQLite, JWT |
| UI | Streamlit |
| Agents | LangChain 1.0 `create_agent`, `init_chat_model` (OpenAI, Ollama, …) |
| Memory | LangGraph SQLite checkpointer |
| RAG | Chroma, optional BM25 + Flashrank rerank |
| Observability | Langfuse (opt-in) |
| Eval | Ragas (`eval/run_eval.py`) |

## Setup

```bash
uv sync
cp .env.example .env   # set OPENAI_API_KEY; Langfuse and Tavily are optional
```

Ingest the Worldbook (needed before lore/rules/item lookups work):

```bash
uv run python -m app.agent.rag.ingest --app-dir backend
```

Run the API and UI:

```bash
uv run uvicorn app.main:app --app-dir backend --reload
uv run streamlit run frontend/streamlit_app.py
```

API docs: http://localhost:8000/docs

The Keeper model is any string `init_chat_model` understands, e.g. `openai:gpt-4o-mini` or `ollama:llama3.1`. The Streamlit sidebar can override model and temperature per session.

## Configuration

See `.env.example`. The important ones:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Default cloud model + embeddings |
| `KEEPER_MODEL` / `ARCHIVIST_MODEL` | Chat models (`provider:name`) |
| `EMBEDDING_MODEL` | `openai:…`, `ollama:…`, or `fake:256` (tests) |
| `RETRIEVAL_MODE` | `basic`, `hybrid`, or `rerank` |
| `TAVILY_API_KEY` | Enables web search |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | Enables tracing |

Use the **same** embedding model for ingest and retrieval.

## Tests

Hermetic: isolated test DB, fake embeddings, Keeper calls mocked. No API key required.

```bash
uv run pytest
```

Includes the Archivist SQL-guard tests (writes, multi-statement queries, and `created_at` not falsely blocked).

## RAG evaluation

Needs `OPENAI_API_KEY` and a store ingested with the **same** embeddings used at eval time:

```bash
uv run python -m app.agent.rag.ingest --app-dir backend
uv sync --group eval
uv run python eval/run_eval.py
```

Metrics: faithfulness, answer relevancy, context precision, context recall.

Ragas 0.4.x currently imports Vertex AI symbols that `langchain-community` 0.4.x removed. `eval/run_eval.py` registers a small placeholder shim so evaluation still runs. Remove it once Ragas ships a compatible release.

## Deploy (DigitalOcean)

One **Basic Droplet, 1 GB RAM / 25 GB disk** (~$6/month). The $4 / 10 GB size is too small for the Docker image. No domain required — open `http://<droplet-ip>`. Add **2 GB of swap** so FastAPI + Streamlit + Chroma fit; without swap the 1 GB box will OOM.

1. Create an Ubuntu 24.04 droplet, add your SSH key, and a firewall allowing **22** and **80** only.
2. SSH in and install Docker, then add swap:

```bash
curl -fsSL https://get.docker.com | sh
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

3. Copy this repo onto the droplet (git clone or `scp`), then:

```bash
cp .env.example .env
# set OPENAI_API_KEY and a real SECRET_KEY in .env
docker compose up -d --build
```

First boot ingests the Worldbook (needs the OpenAI key and a minute or two). Then visit `http://<droplet-ip>`. Demo login: `demo` / `demo1234`.

The API stays on the Docker network; only Caddy (port 80 → Streamlit) is public.

## Security

The Archivist executes model-written SQL. The tool is the trust boundary: it opens the database **read-only**, allows **SELECT only**, rejects multiple statements, and the prompt schema omits the `user` table (password hashes). Never give an LLM a writable database connection.
