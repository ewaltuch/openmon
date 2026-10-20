"""
Mascot species registry for Open-Mon: stats, moves, sprites and the type chart,
loaded from assets/mascots.yaml.

Party members are plain state dicts (see make_state) so they serialize into
saves; hydrate() turns a state into a Mascot for battle.
"""

import os
import random
from functools import cache

import pygame
import yaml
from PIL import Image, ImageDraw

from src.constants import GB_PALETTE, SPRITE_DIR

MASCOTS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "assets", "mascots.yaml"
)
MASCOT_SPRITE_SIZE = 32
MAX_MOVES = 4


class Mascot:
    def __init__(
        self, name, hp, atk, defense, spd, sprite, moves, type_, level=None, xp=0
    ):
        self.name = name
        self.level = BASE_LEVEL if level is None else level
        self.xp = xp
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.defense = defense
        self.spd = spd
        self.sprite = sprite
        self.moves = moves
        self.type = type_


class Move:
    def __init__(self, name, power, type_):
        self.name = name
        self.power = power
        self.type = type_


def _load(path):
    with open(path) as f:
        return yaml.safe_load(f)


_DATA = _load(MASCOTS_PATH)
SPECIES = _DATA["species"]
WILD_ENCOUNTERS = _DATA["wild_encounters"]
TYPE_EFFECTIVENESS = {
    (attacker, defender): multiplier
    for attacker, row in _DATA["type_effectiveness"].items()
    for defender, multiplier in row.items()
}
ELEMENT_TYPES = _DATA["types"]
BASE_LEVEL = _DATA["base_level"]  # species stats are given at this level
MAX_LEVEL = _DATA["max_level"]
STATS = ("hp", "atk", "defense", "spd")


def species(name):
    """Return the species definition for name, failing loudly on typos."""
    try:
        return SPECIES[name]
    except KeyError:
        raise ValueError(f"Unknown mascot species: {name!r}") from None


def clamp_level(level):
    return max(1, min(MAX_LEVEL, int(level)))


def stats_at(name, level):
    """Stats (hp/atk/defense/spd) of a species at a level: base + growth."""
    s = species(name)
    growth = s["growth"]
    return {
        k: max(1, round(s[k] + growth[k] * (clamp_level(level) - BASE_LEVEL)))
        for k in STATS
    }


def learnset_moves(name, level):
    """Moves known at a level: learnset entries up to it, newest 4, in order."""
    known = [m for m in species(name)["learnset"] if m["level"] <= level]
    return known[-MAX_MOVES:]


def moves_from_names(name, names):
    """Learnset entries for saved move names (species-only, unknown skipped)."""
    by_name = {m["name"]: m for m in species(name)["learnset"]}
    return [by_name[n] for n in names if n in by_name][:MAX_MOVES]


def moves_learned_at(name, level):
    """Learnset entries that unlock exactly at this level."""
    return [m for m in species(name)["learnset"] if m["level"] == level]


def xp_to_next(level):
    """XP needed to go from `level` to the next (xp counts within a level)."""
    return 3 * level * level


def xp_fraction(level, xp):
    """Progress through the current level, 0.0 to 1.0 (full at max level)."""
    if level >= MAX_LEVEL:
        return 0.0
    return max(0.0, min(1.0, xp / xp_to_next(level)))


def xp_yield(name, level, trainer=False):
    """XP awarded for defeating a mascot of this species and level."""
    amount = species(name)["xp_yield"] * level // 5
    return amount * 3 // 2 if trainer else amount


def make_state(name, hp=None, level=None, xp=0):
    """
    Create a mascot state dictionary with stats computed from level.
    If hp is None, sets to max_hp (for new mascots).
    If hp is provided, uses that value (for loading/persistence).
    """
    level = clamp_level(BASE_LEVEL if level is None else level)
    s = species(name)
    stats = stats_at(name, level)
    return {
        "name": name,
        "level": level,
        "xp": xp,
        "hp": hp if hp is not None else stats["hp"],
        "max_hp": stats["hp"],
        "atk": stats["atk"],
        "defense": stats["defense"],
        "spd": stats["spd"],
        "type": s["type"],
        "fainted": False,
    }


def normalize_state(state):
    """Fill level/xp on states from old saves (level 5, xp 0). Returns state."""
    state.setdefault("level", BASE_LEVEL)
    state.setdefault("xp", 0)
    return state


def parse_party_entry(entry):
    """A trainer party entry: "Name" or {name: ..., level: ...} -> (name, level)."""
    if isinstance(entry, str):
        return entry, BASE_LEVEL
    return entry["name"], entry.get("level", BASE_LEVEL)


def wild_level(name, rng=random):
    """Roll a level for a wild `name` from the encounter table."""
    for e in WILD_ENCOUNTERS:
        if e["species"] == name:
            lv = e.get("level", BASE_LEVEL)
            if isinstance(lv, (list, tuple)):
                return rng.randint(lv[0], lv[1])
            return lv
    return BASE_LEVEL


def hydrate(state):
    """Create a battle Mascot from a state dict; stats come from the state."""
    normalize_state(state)
    # A saved moveset (chosen via the forget prompt) wins over the derived one
    known = moves_from_names(state["name"], state.get("moves") or [])
    if not known:
        known = learnset_moves(state["name"], state["level"])
    mascot = Mascot(
        name=state["name"],
        hp=state["max_hp"],
        atk=state["atk"],
        defense=state["defense"],
        spd=state["spd"],
        sprite=get_sprite(state["name"]),
        moves=[Move(m["name"], m["power"], m["type"]) for m in known],
        type_=state["type"],
        level=state["level"],
        xp=state["xp"],
    )
    mascot.hp = state["hp"]
    return mascot


def make_mascot(name, level=None):
    """A fresh full-HP Mascot of the given species and level."""
    return hydrate(make_state(name, level=level))


@cache
def get_sprite(name, scale=1):
    """Battle sprite for a species, generated once per scale and shared."""
    if scale != 1:
        base = get_sprite(name)
        size = (base.get_width() * scale, base.get_height() * scale)
        return pygame.transform.scale(base, size)
    spec = species(name)
    if spec.get("sprite"):
        path = os.path.join(SPRITE_DIR, spec["sprite"] + ".png")
        if os.path.exists(path):
            loaded = pygame.image.load(path)
            if loaded.get_size() == (MASCOT_SPRITE_SIZE, MASCOT_SPRITE_SIZE):
                return loaded
    p = spec["placeholder"]
    img = Image.new("RGB", (MASCOT_SPRITE_SIZE, MASCOT_SPRITE_SIZE), GB_PALETTE[0])
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 24, 24], fill=GB_PALETTE[p["body"]])
    draw.rectangle(p["feet_box"], fill=GB_PALETTE[p["feet"]])
    return pygame.image.fromstring(img.tobytes(), img.size, img.mode)


def roll_wild_encounter(rng=random, table=None):
    """Pick a wild species name using an encounter table's weights.

    table is a map's own list; None falls back to the default WILD_ENCOUNTERS.
    """
    table = table or WILD_ENCOUNTERS
    names = [e["species"] for e in table]
    weights = [e["weight"] for e in table]
    return rng.choices(names, weights=weights)[0]
