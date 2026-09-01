"""Request/response schemas (separate from the DB tables in models.py)."""
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel


class UserCreate(SQLModel):
    username: str
    password: str


class UserRead(SQLModel):
    id: int
    username: str
    created_at: datetime


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class HeroCreate(SQLModel):
    name: str
    char_class: str = "Warrior"
    race: str = "Human"
    backstory: str = ""


class HeroRead(SQLModel):
    id: int
    name: str
    char_class: str
    race: str
    level: int
    hp: int
    gold: int
    backstory: str


class AgentInvokeRequest(SQLModel):
    """The contract for talking to the Keeper.

    ``hero_id`` and ``message`` are the core fields (present since v0). v1 adds optional
    per-request overrides so the UI can let players experiment with models/configs.
    """
    hero_id: int
    message: str
    model: Optional[str] = None
    temperature: Optional[float] = None
    reasoning_effort: Optional[str] = None


class AgentInvokeResponse(SQLModel):
    reply: str


class EncounterRequest(SQLModel):
    """Request a structured Encounter for a hero (v2 structured-output demo)."""
    hero_id: int
    scene: str = "a random wilderness encounter suited to the hero"
    model: Optional[str] = None
