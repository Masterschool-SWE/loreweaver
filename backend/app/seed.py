"""Seed the database with the world's items, monsters, and a ready-to-use demo hero.

Seeding is idempotent: it only inserts when a table is empty / the demo user is missing.
The demo data gives the v3 Archivist sub-agent something interesting to query from day one.

Demo login:  username ``demo``  /  password ``demo1234``
"""
import uuid

from sqlmodel import Session, select

from .auth import hash_password
from .models import Adventure, Hero, Inventory, Item, Monster, Quest, User

ITEMS = [
    {"name": "Cinderbrand", "type": "Weapon", "rarity": "Legendary", "value": 5000,
     "description": "A longsword forged from a sliver of the Crimson Shard; always warm, sheds light."},
    {"name": "Frostfang Dagger", "type": "Weapon", "rarity": "Epic", "value": 1200,
     "description": "A Frostmere blade that never dulls and leaves frost on every wound."},
    {"name": "Stormbow", "type": "Weapon", "rarity": "Rare", "value": 600,
     "description": "A Highreach longbow strung with griffon sinew; arrows crackle with static."},
    {"name": "Iron Shortsword", "type": "Weapon", "rarity": "Common", "value": 25,
     "description": "A plain, reliable village blade."},
    {"name": "Aegis of the Lantern", "type": "Armor", "rarity": "Epic", "value": 1500,
     "description": "A blessed shield that turns aside the first blow of any fight."},
    {"name": "Tideweave Cloak", "type": "Armor", "rarity": "Rare", "value": 700,
     "description": "Sea-silk cloak; lets the wearer breathe water for one hour."},
    {"name": "Leather Jerkin", "type": "Armor", "rarity": "Common", "value": 20,
     "description": "Basic light protection."},
    {"name": "Shardglass Lens", "type": "Trinket", "rarity": "Rare", "value": 800,
     "description": "Reveals hidden illusions and disguises."},
    {"name": "Healing Draught", "type": "Consumable", "rarity": "Uncommon", "value": 50,
     "description": "Restores a third of a hero's maximum HP."},
    {"name": "Griffon Whistle", "type": "Consumable", "rarity": "Uncommon", "value": 120,
     "description": "Summons a tamed Stormtalon from the nearest roost."},
    {"name": "Waystone", "type": "Trinket", "rarity": "Common", "value": 10,
     "description": "Drop one to remember a location."},
]

MONSTERS = [
    {"name": "Cinderwyrm", "type": "Dragon", "challenge_rating": 12, "hp": 200,
     "abilities": "Fire breath, molten scales, flight", "lore": "Hoards heat; weak to cold and water."},
    {"name": "Frostmaw", "type": "Beast", "challenge_rating": 6, "hp": 90,
     "abilities": "Freezing bite, ice-step, pack tactics", "lore": "White wolf of Frostmere; won't cross running water."},
    {"name": "Gloomtide Kraken", "type": "Aberration", "challenge_rating": 15, "hp": 300,
     "abilities": "Tentacle grapple, ink cloud, pull-under", "lore": "Terror of the Sunken Coast; despises fire."},
    {"name": "Ashwalker", "type": "Undead", "challenge_rating": 4, "hp": 45,
     "abilities": "Life-drain, immune to fear, reforms", "lore": "Bound to an anchor-bone; shatter it to end them."},
    {"name": "Stormtalon", "type": "Beast", "challenge_rating": 8, "hp": 110,
     "abilities": "Lightning dive, gale wings, keen sight", "lore": "Giant griffon of Highreach; fears the Cinderwyrm."},
    {"name": "Mirewight", "type": "Fey", "challenge_rating": 2, "hp": 20,
     "abilities": "Illusion, drowning lullaby, camouflage", "lore": "Swamp spirit; a song of apology sends it away."},
    {"name": "Hollow King", "type": "Undead", "challenge_rating": 18, "hp": 400,
     "abilities": "Command undead, shard-siphon", "lore": "A rumored ruler of the Hollow Heart. Treat sightings with suspicion."},
]


def seed_initial_data(engine) -> None:
    with Session(engine) as session:
        if session.exec(select(Item)).first() is None:
            session.add_all(Item(**row) for row in ITEMS)
        if session.exec(select(Monster)).first() is None:
            session.add_all(Monster(**row) for row in MONSTERS)
        session.commit()

        if session.exec(select(User).where(User.username == "demo")).first() is not None:
            return  # demo hero already seeded

        user = User(username="demo", hashed_password=hash_password("demo1234"))
        session.add(user)
        session.commit()
        session.refresh(user)

        hero = Hero(
            user_id=user.id, name="Thalia Emberkin", char_class="Mage", race="Human",
            level=3, hp=18, gold=320,
            backstory="A firespeaker from Cinderspire seeking the lost Seventh Shard.",
        )
        session.add(hero)
        session.commit()
        session.refresh(hero)

        session.add(Adventure(hero_id=hero.id, thread_id=str(uuid.uuid4()),
                              title="The Search for the Seventh Shard"))
        session.add_all([
            Quest(hero_id=hero.id, title="Cleanse the Mirewight Bog", status="completed",
                  reward_gold=150, description="Drive the Mirewight from the Verdant Reach swamp."),
            Quest(hero_id=hero.id, title="Retrieve the Tideweave Cloak", status="active",
                  reward_gold=300, description="Dive the Sunken Coast for a lost cloak."),
            Quest(hero_id=hero.id, title="Slay the Frostmaw pair", status="active",
                  reward_gold=400, description="Hunt the wolves stalking Hollowfrost."),
        ])

        def item_id(name: str) -> int:
            return session.exec(select(Item).where(Item.name == name)).first().id

        session.add_all([
            Inventory(hero_id=hero.id, item_id=item_id("Healing Draught"), quantity=3),
            Inventory(hero_id=hero.id, item_id=item_id("Iron Shortsword"), quantity=1),
            Inventory(hero_id=hero.id, item_id=item_id("Shardglass Lens"), quantity=1),
        ])
        session.commit()
