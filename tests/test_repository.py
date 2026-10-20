"""Repository: capture overflow, save round-trip, deposit/withdraw, capacity."""

from unittest.mock import patch

import pygame

from src.constants import PARTY_MAX, STORAGE_MAX
from src.engine import mascots
from src.engine.battle_scene import BattleScene
from src.engine.inventory import InventoryManager
from src.engine.menu_screens import RepositoryScreen, deposit, withdraw
from src.engine.overworld_scene import OverworldScene
from src.engine.save import SaveManager
from src.engine.scene_manager import SceneManager


def state(name="Tux", **kw):
    s = mascots.make_state(name)
    s.update(kw)
    return s


def battle(party_n, storage_n):
    inv = InventoryManager()
    inv.add_item("package", 1)
    mgr = SceneManager()
    scene = BattleScene(
        mgr,
        party_states=[state() for _ in range(party_n)],
        inventory=inv,
        storage_states=[state("Octocat") for _ in range(storage_n)],
        wild_species="Octocat",
    )
    return mgr, scene, inv


def test_capture_overflow_goes_to_storage():
    mgr, scene, _ = battle(PARTY_MAX, 0)
    with patch("src.engine.battle_scene.random.random", return_value=0.0):
        scene._try_capture()
    assert len(scene.party) == PARTY_MAX
    assert len(scene.storage_states) == 1
    assert "Repository" in [m.text for m in scene.messages][-1]
    scene.messages.clear()
    scene._finish_battle()
    res = mgr.battle_result
    assert res.captured_to_storage and len(res.storage_states) == 1
    assert len(res.party_states) == PARTY_MAX


def test_capture_with_room_stays_in_party():
    _, scene, _ = battle(2, 0)
    with patch("src.engine.battle_scene.random.random", return_value=0.0):
        scene._try_capture()
    assert len(scene.party) == 3 and scene.storage_states == []


def test_capture_blocked_when_storage_full():
    _, scene, inv = battle(PARTY_MAX, STORAGE_MAX)
    scene._try_capture()
    assert "full" in scene.msg
    assert inv.get_item_count("package") == 1


def test_overworld_applies_storage_from_result():
    mgr = SceneManager()
    ow = OverworldScene(mgr)
    _, scene, _ = battle(PARTY_MAX, 0)
    with patch("src.engine.battle_scene.random.random", return_value=0.0):
        scene._try_capture()
    scene.manager = mgr
    scene.messages.clear()
    scene._finish_battle()
    ow._apply_battle_result(mgr.battle_result)
    assert len(ow.storage) == 1 and len(ow.party) == PARTY_MAX


def test_save_round_trip_and_old_save_default(tmp_path, monkeypatch):
    monkeypatch.setattr("src.constants.SAVE_PATH", str(tmp_path / "s.json"))
    ow = OverworldScene(SceneManager())
    ow.storage = [state("Octocat")]
    ow._save_game()
    ow2 = OverworldScene(SceneManager())
    ow2._load_game()
    assert [s["name"] for s in ow2.storage] == ["Octocat"]

    data = SaveManager.load()
    del data["storage"]
    SaveManager.save(data)
    ow2._load_game()
    assert ow2.storage == []


def test_deposit_withdraw_rules():
    party, box = [state(), state("Octocat")], []
    assert deposit(party, box, 0)[0]
    assert [s["name"] for s in box] == ["Tux"]
    ok, _ = deposit(party, box, 0)  # last mascot
    assert not ok and len(party) == 1
    assert withdraw(party, box, 0)[0] and len(party) == 2 and box == []


def test_deposit_keeps_a_healthy_mascot():
    party = [state(), state("Octocat", hp=0, fainted=True)]
    assert not deposit(party, [], 0)[0]
    assert deposit(party, [], 1)[0]


def test_withdraw_blocked_when_party_full_and_deposit_when_box_full():
    party = [state() for _ in range(PARTY_MAX)]
    box = [state("Octocat")]
    assert not withdraw(party, box, 0)[0] and len(box) == 1
    full = [state() for _ in range(STORAGE_MAX)]
    assert not deposit(party, full, 0)[0] and len(party) == PARTY_MAX


def test_screen_via_pause_menu_and_keys():
    mgr = SceneManager()
    ow = OverworldScene(mgr)
    mgr.push(ow)
    ow.is_paused = True
    ow.pause_menu_idx = ow.pause_menu_options.index("Repository")
    mgr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z))
    scr = mgr.scenes[-1]
    assert isinstance(scr, RepositoryScreen)
    mgr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z))
    assert len(ow.party) == 1 and len(ow.storage) == 1
    surf = pygame.Surface((240, 160))
    scr.draw(surf)
    mgr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x))
    assert mgr.scenes[-1] is ow
