"""Map loading, warps, the fade transition, per-map encounters and map saves."""

import pygame
import pytest

from src.constants import MAP_DIR
from src.engine import mascots
from src.engine.maps import load_map
from src.engine.overworld_scene import FADE_TIME, OverworldScene
from src.engine.save import SaveManager
from src.overworld import TILE_SIZE
from tests.test_overworld import DummyManager, FakeKeys


def make_scene():
    return OverworldScene(DummyManager())


def walk_until_warp(scene, monkeypatch, key):
    """Hold key until the warp fade starts (stops before the fade advances)."""
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: FakeKeys(key))
    for _ in range(60):
        scene.update(1 / 60)
        if scene.fade:
            break
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: FakeKeys())


def finish_fade(scene):
    scene.update(FADE_TIME + 0.01)  # fade out; map swaps
    scene.update(FADE_TIME + 0.01)  # fade in


def test_maps_dir_has_town_and_route():
    assert MAP_DIR.endswith("maps/")
    town, route = load_map("town"), load_map("route1")
    assert town.tilemap.width == 30 and route.tilemap.height == 22
    assert town.encounters is None  # falls back to the default table
    assert route.encounters
    assert any(n.id == "route_hiker" for n in route.npcs)


def test_unknown_map_raises():
    with pytest.raises(ValueError):
        load_map("nowhere")


def test_every_warp_lands_on_a_walkable_tile_and_returns():
    for map_id in ("town", "route1"):
        m = load_map(map_id)
        for w in m.warps:
            dest = load_map(w.to)
            assert m.tilemap.is_walkable(w.x, w.y)
            assert dest.tilemap.is_walkable(w.tx, w.ty)
            assert dest.warp_at(w.tx, w.ty) is None  # arrival is not a warp tile
            assert any(back.to == map_id for back in dest.warps)


def test_warp_town_to_route_with_fade(monkeypatch):
    scene = make_scene()
    scene.encounter_steps = 1000
    scene.player.place(14, 14)
    walk_until_warp(scene, monkeypatch, pygame.K_DOWN)
    assert scene.fade and scene.fade["phase"] == "out"
    assert scene.map.id == "town"  # still in town while fading out
    scene.update(FADE_TIME + 0.01)
    assert scene.map.id == "route1"
    assert scene.fade["phase"] == "in"
    scene.update(FADE_TIME + 0.01)
    assert scene.fade is None
    assert scene.player.tile == (14, 1)
    assert scene.tilemap is scene.map.tilemap


def test_warp_back_route_to_town(monkeypatch):
    scene = make_scene()
    scene.enter_map("route1", 14, 1)
    walk_until_warp(scene, monkeypatch, pygame.K_UP)
    assert scene.fade
    finish_fade(scene)
    assert scene.map.id == "town"
    assert scene.player.tile == (14, 14)


def test_input_locked_and_overlay_drawn_during_fade(monkeypatch):
    scene = make_scene()
    scene.player.place(14, 14)
    walk_until_warp(scene, monkeypatch, pygame.K_DOWN)
    pos = scene.player.tile
    assert scene.fade["phase"] == "out"
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: FakeKeys(pygame.K_LEFT))
    scene.update(1 / 60)
    assert scene.player.tile == pos
    scene.fade["t"] = FADE_TIME / 2
    assert 0 < scene._fade_alpha() < 255
    scene.draw(pygame.display.get_surface())


def test_camera_clamps_to_new_map():
    scene = make_scene()
    scene.enter_map("route1", 28, 20)
    scene.update(0.0)
    assert scene.camera_x == scene.tilemap.width * TILE_SIZE - 240
    assert scene.camera_y == scene.tilemap.height * TILE_SIZE - 160


def test_encounters_use_the_maps_table(monkeypatch):
    seen = []

    def fake_roll(rng=None, table=None):
        seen.append(table)
        return "Gopher"

    monkeypatch.setattr(mascots, "roll_wild_encounter", fake_roll)
    scene = make_scene()
    scene.steps = scene.encounter_steps - 1
    scene.player.place(10, 2)
    scene._on_step_finished()
    scene.enter_map("route1", 5, 5)
    scene.steps = scene.encounter_steps - 1
    scene._on_step_finished()
    assert seen[0] is None and seen[1] == scene.map.encounters


def test_roll_uses_table():
    table = [{"species": "Gopher", "weight": 1}]
    assert all(mascots.roll_wild_encounter(table=table) == "Gopher" for _ in range(20))


def test_save_restores_map():
    scene = make_scene()
    scene.enter_map("route1", 5, 5)
    scene._save_game()
    assert SaveManager.load()["map"] == "route1"
    scene2 = make_scene()
    scene2._load_game()
    assert scene2.map.id == "route1"
    assert scene2.player.tile == (5, 5)


def test_old_save_without_map_loads_default_map():
    scene = make_scene()
    scene.enter_map("route1", 5, 5)
    SaveManager.save(
        {
            "player": {"x": 5 * TILE_SIZE, "y": 3 * TILE_SIZE},
            "party": ["Tux"],
            "defeated_npcs": {"trainer_1": True},
        }
    )
    scene._load_game()
    assert scene.map.id == "town"
    assert scene.player.tile == (5, 3)
    trainer = next(n for n in scene.npcs if n.id == "trainer_1")
    assert trainer.defeated  # bare ids belong to the default map


def test_unknown_map_in_save_falls_back():
    scene = make_scene()
    SaveManager.save({"map": "gone", "player": {"x": 0, "y": 0}, "party": ["Tux"]})
    scene._load_game()
    assert scene.map.id == "town"
    assert scene.player.tile == scene.SPAWN_TILE


def test_defeated_trainers_keyed_by_map():
    scene = make_scene()
    trainer = next(n for n in scene.npcs if n.trainer)
    trainer.defeated = True
    scene.enter_map("route1")
    scene._save_game()
    assert SaveManager.load()["defeated_npcs"] == {"town:trainer_1": True}
    scene2 = make_scene()
    scene2._load_game()
    scene2.enter_map("town")
    assert next(n for n in scene2.npcs if n.trainer).defeated
