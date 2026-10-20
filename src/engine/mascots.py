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


class Mascot:
    def __init__(self, name, hp, atk, defense, spd, sprite, moves, type_):
        self.name = name
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


def species(name):
    """Return the species definition for name, failing loudly on typos."""
    try:
        return SPECIES[name]
    except KeyError:
        raise ValueError(f"Unknown mascot species: {name!r}") from None


def make_state(name, hp=None):
    """
    Create a mascot state dictionary with base stats.
    If hp is None, sets to max_hp (for new mascots).
    If hp is provided, uses that value (for loading/persistence).
    """
    s = species(name)
    return {
        "name": name,
        "hp": hp if hp is not None else s["hp"],
        "max_hp": s["hp"],
        "atk": s["atk"],
        "defense": s["defense"],
        "spd": s["spd"],
        "type": s["type"],
        "fainted": False,
    }


def hydrate(state):
    """Create a battle Mascot from a state dict; stats come from the state."""
    s = species(state["name"])
    mascot = Mascot(
        name=state["name"],
        hp=state["max_hp"],
        atk=state["atk"],
        defense=state["defense"],
        spd=state["spd"],
        sprite=get_sprite(state["name"]),
        moves=[Move(m["name"], m["power"], m["type"]) for m in s["moves"]],
        type_=state["type"],
    )
    mascot.hp = state["hp"]
    return mascot


def make_mascot(name):
    """A fresh full-HP Mascot of the given species."""
    return hydrate(make_state(name))


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


def roll_wild_encounter(rng=random):
    """Pick a wild species name using the encounter table weights."""
    names = [e["species"] for e in WILD_ENCOUNTERS]
    weights = [e["weight"] for e in WILD_ENCOUNTERS]
    return rng.choices(names, weights=weights)[0]
