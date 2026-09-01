# Loreweaver — Game Rules

These are the rules the Keeper (the Game Master) follows. When a player asks "how does X work?",
the answer should come from this document.

## Heroes

A **Hero** has six core attributes:

- **Level** — starts at 1, maximum 20.
- **HP (Hit Points)** — how much damage a hero can take before falling. A new hero has 10 HP per
  level for warriors, 6 per level for mages, 8 per level for rogues.
- **Gold** — currency, earned from quests and selling items.
- **Class** — Warrior, Mage, Rogue, or Ranger (see below).
- **Race** — Human, Elf, Dwarf, Orc, or Halfling.
- **Backstory** — free text; the Keeper uses it to personalize the adventure.

## Classes

| Class   | Strength            | Weakness            | Signature ability        |
| ------- | ------------------- | ------------------- | ------------------------ |
| Warrior | High HP, melee      | Slow vs. casters    | **Shield Wall** (block)  |
| Mage    | Powerful spells     | Fragile, low HP     | **Arcane Bolt** (ranged) |
| Rogue   | Stealth, critical hits | Poor in open fights | **Backstab** (x3 damage from hiding) |
| Ranger  | Ranged + beast bond | Weak armor          | **Hunter's Mark** (track any creature) |

## Leveling

A hero levels up by completing quests. Each completed quest grants **experience equal to its
reward gold divided by 10**. When accumulated experience reaches **100 × current level**, the hero
levels up: +1 level, +max HP for their class, and HP is restored to full.

## Combat (narrative)

Loreweaver combat is narrative, not turn-based dice. The Keeper describes the situation; the player
declares an action; the Keeper resolves it by weighing:

1. The hero's class and level vs. the foe's **challenge rating** (see the bestiary).
2. Whether the player's tactic plays to their class strength.
3. A pinch of luck.

A foe whose challenge rating is **more than double** the hero's level should almost always win
unless the player is extraordinarily clever. The Keeper never lets a hero die without giving them
at least one chance to flee.

## Gold and Rewards

- Quests pay **reward_gold** on completion.
- Selling an item returns **half its listed value**.
- Buying an item costs its full listed value.

## Item Rarity

Items come in five rarity tiers, in ascending order:

1. **Common** (white)
2. **Uncommon** (green)
3. **Rare** (blue)
4. **Epic** (purple)
5. **Legendary** (gold)

Legendary items are unique — only one of each exists in all of Aethelgard. A hero may carry at most
**one** legendary item attuned at a time.

## Quests

A quest has a **status**: `active`, `completed`, or `failed`. A hero may have multiple active
quests. The Keeper should track which quests are active and offer to advance them. Failing a quest
(e.g., letting a protected NPC die) does not end the game, but the reward is lost.
