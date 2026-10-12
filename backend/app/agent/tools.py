"""Tools the Keeper can call.

- ``search_worldbook`` — RAG retrieval over Aethelgard's lore/rules/bestiary/items.
- ``ask_archivist`` — delegate data questions to the Archivist SQL sub-agent (v3).
- Tavily web search — added only when TAVILY_API_KEY is set, so the app still runs without it.
"""
import os

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from .archivist import build_archivist
from .rag.retriever import get_retriever


@tool
def search_worldbook(query: str) -> str:
    """Search the Worldbook — Aethelgard's lore, game rules, bestiary, and item catalog.

    Use this for ANY in-world fact you are unsure of: a monster's stats or weakness, an item's
    price or rarity, a rule, or regional lore. Returns the most relevant passages.
    """
    try:
        docs = get_retriever().invoke(query)
    except Exception as exc:
        return f"Worldbook search failed: {exc}"
    if not docs:
        return "No relevant Worldbook passages found. (Has the Worldbook been ingested yet?)"
    return "\n\n---\n\n".join(
        f"[source: {d.metadata.get('source', '?')}]\n{d.page_content}" for d in docs
    )


@tool
def ask_archivist(question: str, config: RunnableConfig) -> str:
    """Ask the Archivist — a SQL expert over the game database — about the player's data:
    heroes, items, inventory, quests, monsters.

    Use for counts and lookups, e.g. 'how many quests has hero 1 completed?', 'what is in hero 1's
    inventory?', 'which monster has the highest challenge rating?'. Always include the hero's id
    when the question is about a specific hero.
    """
    try:
        archivist = build_archivist()
        # Callbacks only — do not reuse the Keeper's thread_id, or the sub-agent can
        # write into the same checkpoint and leave dangling tool_calls.
        child_config = {}
        if config and config.get("callbacks"):
            child_config["callbacks"] = config["callbacks"]
        result = archivist.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config=child_config,
        )
        content = result["messages"][-1].content
        return content if isinstance(content, str) else str(content)
    except Exception as exc:
        return f"The Archivist could not answer: {exc}"


def get_keeper_tools() -> list:
    """The Keeper's toolbelt. Web search is included only if a Tavily key is configured."""
    tools = [search_worldbook, ask_archivist]
    if os.getenv("TAVILY_API_KEY"):
        from langchain_tavily import TavilySearch

        tools.append(TavilySearch(max_results=3))
    return tools
