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
    docs = get_retriever().invoke(query)
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
    archivist = build_archivist()
    # Passing `config` through propagates callbacks (e.g. Langfuse) so the sub-agent's work
    # shows up nested inside the Keeper's trace.
    result = archivist.invoke({"messages": [{"role": "user", "content": question}]}, config=config)
    return result["messages"][-1].content


def get_keeper_tools() -> list:
    """The Keeper's toolbelt. Web search is included only if a Tavily key is configured."""
    tools = [search_worldbook, ask_archivist]
    if os.getenv("TAVILY_API_KEY"):
        from langchain_tavily import TavilySearch

        tools.append(TavilySearch(max_results=3))
    return tools
