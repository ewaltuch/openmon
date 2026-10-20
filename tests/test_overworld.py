import pygame

from src.engine.overworld_scene import OverworldScene


class DummyManager:
    def __init__(self):
        self.scenes = []
        self.captured_mascot_name = None

    def push(self, scene):
        self.scenes.append(scene)


def test_party_adds_captured():
    mgr = DummyManager()
    scene = OverworldScene(mgr)
    mgr.captured_mascot_name = "Octocat"
    scene.update(0.1)
    # Party is now a list of state dicts, check for name
    assert any(state["name"] == "Octocat" for state in scene.party)


def test_party_initial():
    mgr = DummyManager()
    scene = OverworldScene(mgr)
    # Party is now a list of state dicts, check for names
    assert any(state["name"] == "Tux" for state in scene.party)
    assert any(state["name"] == "BSD Daemon" for state in scene.party)


class FakeKeys:
    def __init__(self, *held):
        self.held = held

    def __getitem__(self, key):
        return key in self.held


def walk(scene, monkeypatch, key, seconds):
    """Hold key for the given time, updating at 60 FPS."""
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: FakeKeys(key))
    for _ in range(int(seconds * 60)):
        scene.update(1 / 60)
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: FakeKeys())
    for _ in range(30):  # let the last step finish
        scene.update(1 / 60)


def test_player_moves_one_tile_per_step(monkeypatch):
    scene = OverworldScene(DummyManager())
    scene.player.place(2, 7)
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: FakeKeys(pygame.K_RIGHT))
    scene.update(1 / 60)
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: FakeKeys())
    assert scene.player.moving
    for _ in range(30):
        scene.update(1 / 60)
    assert scene.player.tile == (3, 7)
    assert (scene.player.x, scene.player.y) == (3 * 8, 7 * 8)
    assert not scene.player.moving


def test_walls_block_on_every_side(monkeypatch):
    scene = OverworldScene(DummyManager())
    # (2, 2) has walls above (row 1) and to the left (column 1)
    for key in (pygame.K_UP, pygame.K_LEFT):
        scene.player.place(2, 2)
        walk(scene, monkeypatch, key, 0.5)
        assert scene.player.tile == (2, 2)
    # The right wall is column 28: walking right stops just before it
    scene.player.place(26, 8)
    walk(scene, monkeypatch, pygame.K_RIGHT, 1.0)
    assert scene.player.tile == (27, 8)
    assert scene.player.facing == "right"


def test_npcs_block_movement(monkeypatch):
    scene = OverworldScene(DummyManager())
    npc = scene.npcs[0]
    scene.player.place(npc.x - 1, npc.y)
    walk(scene, monkeypatch, pygame.K_RIGHT, 0.5)
    assert scene.player.tile == (npc.x - 1, npc.y)


def test_encounter_counts_grass_tiles_not_frames(monkeypatch):
    mgr = DummyManager()
    scene = OverworldScene(mgr)
    scene.encounter_steps = 100
    scene.player.place(9, 3)  # start of the grass patch (columns 9-19)
    walk(scene, monkeypatch, pygame.K_RIGHT, 0.5)  # about 3 tiles
    assert 1 <= scene.steps <= 4
    assert len(mgr.scenes) == 0


def test_encounter_only_in_grass(monkeypatch):
    mgr = DummyManager()
    scene = OverworldScene(mgr)
    # Step into tall grass with one step left on the counter
    scene.player.place(10, 2)
    scene.steps = scene.encounter_steps - 1
    walk(scene, monkeypatch, pygame.K_RIGHT, 0.1)
    assert len(mgr.scenes) == 1

    # Walking on the floor never triggers an encounter
    scene.player.place(2, 8)
    scene.steps = scene.encounter_steps - 1
    walk(scene, monkeypatch, pygame.K_RIGHT, 0.5)
    assert len(mgr.scenes) == 1


def test_talk_to_faced_npc_only(monkeypatch):
    scene = OverworldScene(DummyManager())
    npc = scene.npcs[0]
    space = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)

    # Diagonal neighbours don't count
    scene.player.place(npc.x - 1, npc.y - 1)
    scene.handle_event(space)
    assert scene.active_dialogue is None

    scene.player.place(npc.x - 1, npc.y)
    scene.player.facing = "right"
    scene.handle_event(space)
    assert scene.active_dialogue == npc.dialogue[0]


def test_no_movement_while_talking(monkeypatch):
    scene = OverworldScene(DummyManager())
    scene.player.place(2, 8)
    scene.active_dialogue = "Hello"
    walk(scene, monkeypatch, pygame.K_RIGHT, 0.5)
    assert scene.player.tile == (2, 8)


def test_load_snaps_old_pixel_positions_to_grid():
    from src.engine.save import SaveManager

    scene = OverworldScene(DummyManager())
    SaveManager.save({"player": {"x": 27.5, "y": 57.9}, "party": ["Tux"]})
    scene._load_game()
    assert scene.player.tile == (3, 7)
    assert (scene.player.x, scene.player.y) == (24, 56)

    # A position on a wall or NPC falls back to the spawn point
    npc = scene.npcs[0]
    SaveManager.save({"player": {"x": npc.x * 8, "y": npc.y * 8}, "party": ["Tux"]})
    scene._load_game()
    assert scene.player.tile == scene.SPAWN_TILE


def test_npcs_stand_on_walkable_tiles():
    scene = OverworldScene(DummyManager())
    for npc in scene.npcs:
        assert scene.tilemap.is_walkable(npc.x, npc.y), npc.id


def test_healer_npc_restores_party():
    scene = OverworldScene(DummyManager())
    scene.party[0]["hp"] = 1
    scene.party[1]["hp"] = 0
    scene.party[1]["fainted"] = True
    healer = next(npc for npc in scene.npcs if npc.heals)
    scene.player.place(healer.x - 1, healer.y)
    scene.player.facing = "right"

    space = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
    for _ in range(len(healer.dialogue) + 1):
        scene.handle_event(space)

    assert scene.active_dialogue is None
    assert all(s["hp"] == s["max_hp"] and not s["fainted"] for s in scene.party)
