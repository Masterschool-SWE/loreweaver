"""Orchestration glue between the API and the Keeper agent.

The router calls :func:`invoke_keeper`. Tests monkeypatch this one function so they never need
a real model or API key.
"""
import uuid

from sqlmodel import Session, select

from ..config import KEEPER_MODEL, KEEPER_TEMPERATURE
from ..models import Adventure, Hero
from .keeper import build_keeper
from .repair import repair_checkpoint
from .tracing import flush_langfuse, get_langfuse_handler


def get_or_create_adventure(session: Session, hero_id: int) -> Adventure:
    """Each hero has one ongoing adventure thread; create it on first contact."""
    adventure = session.exec(select(Adventure).where(Adventure.hero_id == hero_id)).first()
    if adventure is None:
        adventure = Adventure(hero_id=hero_id, thread_id=str(uuid.uuid4()), title="A new adventure")
        session.add(adventure)
        session.commit()
        session.refresh(adventure)
    return adventure


def _hero_context(hero: Hero) -> str:
    return (
        f"- Hero ID: {hero.id}\n"
        f"- Name: {hero.name}\n"
        f"- Class: {hero.char_class}\n"
        f"- Race: {hero.race}\n"
        f"- Level: {hero.level}\n"
        f"- HP: {hero.hp}\n"
        f"- Gold: {hero.gold}\n"
        f"- Backstory: {hero.backstory or 'unknown'}"
    )


def invoke_keeper(
    session: Session,
    hero: Hero,
    message: str,
    *,
    model: str | None = None,
    temperature: float | None = None,
    reasoning_effort: str | None = None,
) -> str:
    """Run one turn of conversation and return the Keeper's reply text."""
    adventure = get_or_create_adventure(session, hero.id)

    keeper = build_keeper(
        hero_context=_hero_context(hero),
        model=model or KEEPER_MODEL,
        temperature=KEEPER_TEMPERATURE if temperature is None else temperature,
        reasoning_effort=reasoning_effort,
    )

    # thread_id ties this turn to the hero's persistent memory; the Langfuse handler (if any)
    # traces the whole nested flow (Keeper -> Archivist -> tools).
    config = {"configurable": {"thread_id": adventure.thread_id}}
    handler = get_langfuse_handler()
    if handler:
        config["callbacks"] = [handler]

    # A prior turn may have checkpointed tool_calls without results; fix that first
    # so this prompt is not rejected by the model API.
    repair_checkpoint(keeper, config)
    try:
        result = keeper.invoke({"messages": [{"role": "user", "content": message}]}, config=config)
    except Exception:
        repair_checkpoint(keeper, config)
        raise
    if handler:
        flush_langfuse()
    return result["messages"][-1].content


def forge_encounter(
    hero: Hero,
    scene: str,
    *,
    model: str | None = None,
    temperature: float | None = None,
):
    """Structured-output demo: return an :class:`Encounter` for the given scene."""
    from .encounter import generate_encounter

    enc = generate_encounter(
        _hero_context(hero),
        scene,
        model=model or KEEPER_MODEL,
        temperature=KEEPER_TEMPERATURE if temperature is None else temperature,
    )
    flush_langfuse()
    return enc
