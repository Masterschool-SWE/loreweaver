"""The Archivist — a SQL-expert sub-agent.

This is the "agent-as-a-tool" pattern. The Archivist is its own ``create_agent`` whose only
tool is a **read-only** ``execute_sql``. The Keeper calls the Archivist (via the ``ask_archivist``
tool in tools.py) to offload data questions instead of trying to answer them itself.
"""
import re
import sqlite3

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

from ..config import ARCHIVIST_MODEL, SQLITE_PATH

SCHEMA = """\
hero(id, user_id, name, char_class, race, level, hp, gold, backstory, created_at)
item(id, name, type, rarity, value, description)
inventory(id, hero_id, item_id, quantity)        -- join inventory.item_id -> item.id
quest(id, hero_id, title, status, reward_gold, description, created_at)  -- status: active|completed|failed
monster(id, name, type, challenge_rating, hp, abilities, lore)
adventure(id, hero_id, thread_id, title, created_at)
"""

# Whole-word match so "created_at" doesn't trip on "create".
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|replace|vacuum)\b", re.IGNORECASE
)


@tool
def execute_sql(query: str) -> str:
    """Run a single read-only SQL SELECT against the game database and return the rows as text.

    Only SELECT statements are permitted; anything that writes is rejected.
    """
    q = query.strip().rstrip(";").strip()
    if not q.lower().startswith("select"):
        return "Rejected: only SELECT queries are allowed."
    if ";" in q:
        return "Rejected: only a single statement is allowed."
    if _FORBIDDEN.search(q):
        return "Rejected: query contains a forbidden (write) keyword."

    try:
        conn = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro", uri=True)
        cur = conn.execute(q)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchmany(50)
        conn.close()
    except Exception as exc:  # surface the error so the agent can fix its query
        return f"SQL error: {exc}"

    if not rows:
        return "No rows."
    header = " | ".join(cols)
    body = "\n".join(" | ".join(str(v) for v in row) for row in rows)
    return f"{header}\n{body}"


ARCHIVIST_SYSTEM_PROMPT = f"""\
You are the Archivist, a meticulous SQL expert for Loreweaver's game database (SQLite).
Answer questions by writing and running SQL with the execute_sql tool. Rules:
- SELECT only. One statement at a time.
- Inspect the rows you get back, then answer the user in one or two plain sentences.
- If a query errors, read the message, fix the SQL, and try again.

The schema:
{SCHEMA}
"""


def build_archivist(model: str | None = None):
    """Build the Archivist sub-agent (no memory; it's a one-shot worker)."""
    llm = init_chat_model(model or ARCHIVIST_MODEL)
    return create_agent(llm, tools=[execute_sql], system_prompt=ARCHIVIST_SYSTEM_PROMPT)
