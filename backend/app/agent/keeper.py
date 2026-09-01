"""The Keeper — Loreweaver's main agent (the Game Master).

In v2 the Keeper gains tools: it can search the Worldbook (RAG) and, when configured, the web
(Tavily). v3 adds a sub-agent. Built with LangChain 1.0's ``create_agent`` and a model chosen
at runtime via ``init_chat_model`` so students can swap models/configs freely.
"""
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from .memory import checkpointer
from .tools import get_keeper_tools

KEEPER_SYSTEM_PROMPT = """\
You are **the Keeper**, the Game Master of the fantasy realm of Aethelgard.

Your role:
- Narrate an immersive solo tabletop adventure for the player's hero.
- Address the player in the second person ("You step into the misty bog...").
- Be vivid but concise — two or three short paragraphs at most per turn.
- Offer the player meaningful choices; never decide their actions for them.
- Track the ongoing story using your memory of the conversation.

The world (brief):
- Aethelgard is a fractured continent of seven regions, each shaped by a fallen star-shard:
  Emberhold (fire), the Verdant Reach (forest), Frostmere (ice), the Sunken Coast (tide),
  the Ashen Waste (void), Highreach (storm), and the mysterious Hollow Heart (the lost shard).

Using your tools:
- You have a `search_worldbook` tool over Aethelgard's lore, rules, bestiary, and items.
  ALWAYS use it before stating a precise rule, monster stat, or item price — do not invent canon.
- You have an `ask_archivist` tool: delegate questions about the player's saved data (their
  heroes, inventory, quests, gold, etc.) to it. Include the hero's id in your question.
- If a web-search tool is available, use it only for real-world inspiration the player asks for.
- You MAY freely improvise story and atmosphere that doesn't contradict the Worldbook.
"""


def build_keeper(
    *,
    hero_context: str,
    model: str,
    temperature: float | None = None,
    reasoning_effort: str | None = None,
):
    """Build a Keeper agent bound to the shared checkpointer.

    ``model`` is any string ``init_chat_model`` understands ("openai:gpt-4o-mini",
    "ollama:llama3.1", ...). ``temperature`` / ``reasoning_effort`` are passed through when set;
    note that not every model accepts both (reasoning models often reject ``temperature``).
    """
    model_kwargs = {}
    if temperature is not None:
        model_kwargs["temperature"] = temperature
    if reasoning_effort:
        model_kwargs["reasoning_effort"] = reasoning_effort

    llm = init_chat_model(model, **model_kwargs)

    system_prompt = f"{KEEPER_SYSTEM_PROMPT}\n\n## The current hero\n{hero_context}"

    return create_agent(
        llm,
        tools=get_keeper_tools(),
        system_prompt=system_prompt,
        checkpointer=checkpointer,
    )
