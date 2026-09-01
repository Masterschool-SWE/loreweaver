"""SQLModel database tables — the shared data model used across all four phases.

These tables grow over the project but are introduced here in full so later phases
(especially the v3 Archivist SQL sub-agent) have rich data to work with.
"""
from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=_utcnow)

    heroes: List["Hero"] = Relationship(back_populates="user")


class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str
    char_class: str = "Warrior"  # Warrior | Mage | Rogue | Ranger
    race: str = "Human"
    level: int = 1
    hp: int = 10
    gold: int = 50
    backstory: str = ""
    created_at: datetime = Field(default_factory=_utcnow)

    user: Optional[User] = Relationship(back_populates="heroes")


class Item(SQLModel, table=True):
    """Catalog of items that can exist in the world (see assets/worldbook/items.md)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    type: str  # Weapon | Armor | Trinket | Consumable
    rarity: str  # Common | Uncommon | Rare | Epic | Legendary
    value: int = 0
    description: str = ""


class Inventory(SQLModel, table=True):
    """Join table: which hero owns how many of which item."""
    id: Optional[int] = Field(default=None, primary_key=True)
    hero_id: int = Field(foreign_key="hero.id", index=True)
    item_id: int = Field(foreign_key="item.id", index=True)
    quantity: int = 1


class Quest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hero_id: int = Field(foreign_key="hero.id", index=True)
    title: str
    status: str = "active"  # active | completed | failed
    reward_gold: int = 0
    description: str = ""
    created_at: datetime = Field(default_factory=_utcnow)


class Monster(SQLModel, table=True):
    """Bestiary catalog (see assets/worldbook/bestiary.md)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    type: str
    challenge_rating: int = 1
    hp: int = 10
    abilities: str = ""
    lore: str = ""


class Adventure(SQLModel, table=True):
    """One conversational thread for a hero. ``thread_id`` drives the v1 memory checkpointer."""
    id: Optional[int] = Field(default=None, primary_key=True)
    hero_id: int = Field(foreign_key="hero.id", index=True)
    thread_id: str = Field(index=True)
    title: str = "A new adventure"
    created_at: datetime = Field(default_factory=_utcnow)
