"""XP, levels, stat growth, learnsets and old-save defaults (ROADMAP 2.1)."""

import random
from unittest.mock import patch

from src.engine import mascots
from src.engine.battle_scene import BattleScene
from src.engine.inventory import InventoryManager
from src.engine.overworld_scene import OverworldScene
from src.engine.save import SaveManager
from src.engine.scene_manager import SceneManager


class DummyManager:
    pass


def _scene(player_level=20, wild="Octocat", wild_level=5, name="Tux"):
    state = mascots.make_state(name, level=player_level)
    return BattleScene(
        DummyManager(),
        party_states=[state],
        wild_species=wild,
        wild_level=wild_level,
    )


def _texts(scene):
    return [m.text for m in scene.messages]


def _win(scene):
    scene.opponent.hp = 0
    scene._on_opponent_fainted()


def test_xp_curve_increases_and_yield_scales_with_level():
    needs = [mascots.xp_to_next(lv) for lv in range(1, mascots.MAX_LEVEL)]
    assert needs == sorted(needs) and needs[0] > 0
    assert mascots.xp_yield("Tux", 10) == 2 * mascots.xp_yield("Tux", 5)
    assert mascots.xp_yield("Tux", 5, trainer=True) > mascots.xp_yield("Tux", 5)


def test_stats_grow_with_level_and_default_matches_species():
    low, base, high = (mascots.stats_at("Tux", lv) for lv in (3, 5, 15))
    assert base == {k: mascots.SPECIES["Tux"][k] for k in mascots.STATS}
    for k in mascots.STATS:
        assert low[k] <= base[k] < high[k]
    state = mascots.make_state("Tux", level=15)
    assert state["level"] == 15 and state["xp"] == 0
    assert state["max_hp"] == state["hp"] == high["hp"]
    assert mascots.make_state("Tux")["level"] == 5


def test_learnset_depends_on_level_and_caps_at_four():
    assert [m.name for m in mascots.make_mascot("Tux", 5).moves] == [
        "Peck",
        "Code",
        "Shellshock",
    ]
    tux20 = mascots.make_mascot("Tux", 20)
    assert len(tux20.moves) == 4
    assert tux20.moves[-1].name == "Rm -rf"
    assert "Peck" not in [m.name for m in tux20.moves]


def test_wild_level_in_range_and_trainer_entries_backwards_compatible():
    rng = random.Random(1)
    for e in mascots.WILD_ENCOUNTERS:
        lo, hi = e["level"]
        levels = [mascots.wild_level(e["species"], rng) for _ in range(20)]
        assert all(lo <= lv <= hi for lv in levels)
    assert mascots.parse_party_entry("Tux") == ("Tux", 5)
    assert mascots.parse_party_entry({"name": "Tux", "level": 8}) == ("Tux", 8)
    scene = BattleScene(DummyManager(), wild_species="Gopher")
    assert 3 <= scene.opponent.level <= 7


def test_victory_awards_xp_and_narrates():
    scene = _scene()
    scene.messages.clear()
    _win(scene)
    expected = mascots.xp_yield("Octocat", 5)
    assert scene.player.xp == expected
    assert f"Tux gained {expected} XP!" in _texts(scene)
    assert scene.get_party_states()[0]["xp"] == expected


def test_level_up_grows_stats_heals_by_gain_and_plays_sound():
    scene = _scene(player_level=5)
    scene.messages.clear()
    before = (scene.player.max_hp, scene.player.atk)
    scene.player.hp -= 5
    hp_before = scene.player.hp
    scene._gain_xp(scene.player, mascots.xp_to_next(5) + 3)
    assert scene.player.level == 6 and scene.player.xp == 3
    assert scene.player.max_hp > before[0] and scene.player.atk >= before[1]
    assert scene.player.hp == hp_before + scene.player.max_hp - before[0]
    levelup = [m for m in scene.messages if "grew to level 6" in m.text]
    assert levelup and levelup[0].sound == "levelup"
    state = scene.get_party_states()[0]
    assert (state["level"], state["xp"]) == (6, 3)


def test_learning_into_free_slot_does_not_forget():
    scene = _scene(player_level=8)
    scene.messages.clear()
    scene._gain_xp(scene.player, mascots.xp_to_next(8))
    texts = _texts(scene)
    assert "Tux grew to level 9!" in texts
    assert "Tux learned Sudo!" in texts
    assert not any("forgot" in t for t in texts)
    assert scene.player.moves[-1].name == "Sudo"


def test_xp_shared_between_participants_and_fainted_get_none():
    def two_party():
        return BattleScene(
            DummyManager(),
            party_states=[
                mascots.make_state("Tux", level=20),
                mascots.make_state("BSD Daemon", level=20),
            ],
            wild_species="Octocat",
            wild_level=5,
        )

    total = mascots.xp_yield("Octocat", 5)
    scene = two_party()
    scene._execute_switch(1)
    _win(scene)
    assert scene.party[0].xp == scene.party[1].xp == total // 2

    scene = two_party()
    scene._execute_switch(1)
    scene.party_states[0]["fainted"] = True
    _win(scene)
    assert scene.party[0].xp == 0 and scene.party[1].xp == total


def test_trainer_battle_gives_bonus_xp_per_mascot():
    scene = BattleScene(
        DummyManager(),
        party_states=[mascots.make_state("Tux", level=20)],
        opponent_party=[mascots.make_mascot("Gopher", 6), mascots.make_mascot("Konqi")],
        is_trainer_battle=True,
    )
    scene.messages.clear()
    _win(scene)
    assert scene.player.xp == mascots.xp_yield("Gopher", 6, trainer=True)
    assert not scene.battle_over


def test_level_and_xp_persist_through_battle_result():
    manager = DummyManager()
    manager.pop = lambda: None
    scene = BattleScene(
        manager,
        party_states=[mascots.make_state("Tux", level=20)],
        wild_species="Octocat",
        wild_level=5,
    )
    _win(scene)
    scene._finish_battle()
    synced = manager.battle_result.party_states[0]
    assert synced["xp"] == scene.player.xp and synced["level"] == scene.player.level
    again = mascots.hydrate(synced)
    assert again.max_hp == scene.player.max_hp and again.xp == synced["xp"]


def test_capture_keeps_opponent_level():
    inv = InventoryManager()
    inv.add_item("package", 1)
    scene = _scene(wild_level=7)
    scene.inventory = inv
    scene.opponent.hp = 1
    with patch("src.engine.battle_scene.random.random", return_value=0.0):
        scene._try_capture()
    assert scene.get_party_states()[-1]["level"] == 7


def test_old_save_without_level_xp_defaults():
    old_party = [
        {
            "name": "Tux",
            "hp": 10,
            "max_hp": 24,
            "atk": 8,
            "defense": 6,
            "spd": 7,
            "type": "Kernel",
            "fainted": False,
        }
    ]
    SaveManager.save({"player": {"x": 8, "y": 8}, "party": old_party})
    ow = OverworldScene(SceneManager())
    ow._load_game()
    assert ow.party[0]["level"] == 5 and ow.party[0]["xp"] == 0
    assert ow.party[0]["hp"] == 10
    assert BattleScene(DummyManager(), party_states=ow.party).player.level == 5
