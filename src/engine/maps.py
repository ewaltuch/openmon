"""
Map definitions: one YAML per map in assets/maps/ (tiles file, spawn, warps,
NPCs, encounter table) next to its tile CSV.
"""

import os
from dataclasses import dataclass, field

import yaml

from src.constants import MAP_DIR
from src.overworld import TileMap

from .npc import NPC


@dataclass
class Warp:
    x: int
    y: int
    to: str  # destination map id
    tx: int
    ty: int
    facing: str | None = None


@dataclass
class MapData:
    id: str
    name: str
    tilemap: TileMap
    spawn: tuple
    warps: list = field(default_factory=list)
    npcs: list = field(default_factory=list)
    # None: use mascots.yaml's default table; []: no wild encounters (interiors)
    encounters: list | None = None

    def warp_at(self, tx, ty):
        for warp in self.warps:
            if (warp.x, warp.y) == (tx, ty):
                return warp
        return None


def map_exists(map_id):
    return os.path.exists(os.path.join(MAP_DIR, f"{map_id}.yaml"))


def load_map(map_id):
    """Load a map by id. Raises ValueError for an unknown id."""
    path = os.path.join(MAP_DIR, f"{map_id}.yaml")
    if not os.path.exists(path):
        raise ValueError(f"Unknown map: {map_id}")
    with open(path) as f:
        data = yaml.safe_load(f)
    return MapData(
        id=map_id,
        name=data.get("name", map_id),
        tilemap=TileMap(os.path.join(MAP_DIR, data["tiles"])),
        spawn=tuple(data.get("spawn", (1, 1))),
        warps=[Warp(**w) for w in data.get("warps", [])],
        npcs=[NPC(**n) for n in data.get("npcs", [])],
        encounters=data.get("encounters"),
    )
