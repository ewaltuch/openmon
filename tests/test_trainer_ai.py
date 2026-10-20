"""Trainer move AI and line-of-sight challenges."""

import random

import pygame

from src.engine import battle_scene
from src.engine.battle_result import BattleResult
from src.engine.battle_scene import BattleScene
from src.engine.mascots import Move
from src.engine.overworld_scene import (
    ALERT_TIME,
    APPROACH_STEP_TIME,
    OverworldScene,
)
from src.engine.scene_manager import SceneManager


def _battle(trainer=True):
    if trainer:
        foe = BattleScene(SceneManager()).make_mascot("BSD Daemon")
        b = BattleScene(SceneManager(), opponent_party=[foe], is_trainer_battle=True)
    else:
        b = BattleScene(SceneManager(), wild_species="BSD Daemon")
    b.opponent.moves = [
        Move("Weak", 10, "Shell"),
        Move("Strong", 40, "Shell"),
        Move("Effective", 40, "Kernel"),
    ]
    b.player.type = "Shell"
    b.opponent.type = "Shell"
    return b


def test_expected_damage_uses_power_and_type():
    b = _battle()
    weak, strong, eff = b.opponent.moves
    dmg = lambda m: b._expected_damage(m, b.opponent, b.player)  # noqa: E731
    assert dmg(strong) > dmg(weak)
    # Kernel > Shell: super-effective beats an equal-power neutral move
    assert dmg(eff) > dmg(strong)


def test_trainer_prefers_best_move_with_bounded_randomness(monkeypatch):
    b = _battle()
    monkeypatch.setattr(battle_scene, "ai_rng", random.Random(1))
    picks = [b._choose_opponent_move().name for _ in range(1000)]
    best = picks.count("Effective") / 1000
    assert 0.8 < best < 1.0  # mostly the best, but not fully predictable


def test_trainer_ai_is_seedable(monkeypatch):
    b = _battle()
    runs = []
    for _ in range(2):
        monkeypatch.setattr(battle_scene, "ai_rng", random.Random(7))
        runs.append([b._choose_opponent_move().name for _ in range(50)])
    assert runs[0] == runs[1]


def test_zero_random_chance_always_picks_best(monkeypatch):
    b = _battle()
    monkeypatch.setattr(battle_scene, "AI_RANDOM_CHANCE", 0)
    assert {b._choose_opponent_move().name for _ in range(50)} == {"Effective"}


def test_wild_opponent_still_random():
    b = _battle(trainer=False)
    random.seed(3)
    assert len({b._choose_opponent_move().name for _ in range(100)}) > 1


# ---- line of sight ----


class _NoKeys:
    def __getitem__(self, key):
        return False


def _scene(monkeypatch=None):
    s = OverworldScene(SceneManager())
    s.enter_map("town")
    s.npcs = [n for n in s.npcs if n.trainer]
    t = s.npcs[0]
    t.x, t.y, t.facing, t.sight, t.defeated = 10, 10, "down", 4, False
    t.home = (10, 10)
    if monkeypatch:
        monkeypatch.setattr(pygame.key, "get_pressed", lambda: _NoKeys())
    return s, t


def test_sees_player_in_line_and_range():
    s, t = _scene()
    s.player.place(10, 13)
    assert s.trainer_distance_to_player(t) == 3
    s.player.place(10, 14)
    assert s.trainer_distance_to_player(t) == 4
    s.player.place(10, 15)  # out of range
    assert s.trainer_distance_to_player(t) is None


def test_facing_matters():
    s, t = _scene()
    s.player.place(10, 13)
    t.facing = "up"
    assert s.trainer_distance_to_player(t) is None
    s.player.place(10, 8)
    assert s.trainer_distance_to_player(t) == 2
    s.player.place(11, 12)  # diagonal never counts
    assert s.trainer_distance_to_player(t) is None


def test_wall_blocks_sight():
    s, t = _scene()
    s.player.place(10, 13)
    s.tilemap.tiles[12][10] = 1
    assert s.trainer_distance_to_player(t) is None


def test_other_npc_blocks_sight():
    s, t = _scene()
    s.player.place(10, 13)
    s.npcs.append(type(t)("x", "X", 10, 12, "tux", ["hi"]))
    assert s.trainer_distance_to_player(t) is None


def test_defeated_trainer_does_not_challenge(monkeypatch):
    s, t = _scene(monkeypatch)
    s.player.place(10, 12)
    t.defeated = True
    s.update(1 / 60)
    assert s.challenge is None


def test_challenge_alert_walk_then_dialogue_and_battle(monkeypatch):
    s, t = _scene(monkeypatch)
    s.player.place(10, 14)
    s.update(1 / 60)
    assert s.challenge and s.challenge["phase"] == "alert"
    assert s.active_dialogue is None
    s.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s))  # locked
    s.update(ALERT_TIME + 0.01)
    assert s.challenge["phase"] == "walk"
    for _ in range(3):
        s.update(APPROACH_STEP_TIME + 0.001)
    assert (t.x, t.y) == (10, 13)  # adjacent to the player
    assert s.challenge is None
    assert s.active_npc is t and s.active_dialogue
    assert s.player.facing == "up"
    for _ in range(10):  # finish the dialogue: the battle starts
        if not s.active_dialogue:
            break
        s.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z))
    battle = s.manager.scenes[-1]
    assert isinstance(battle, BattleScene) and battle.is_trainer_battle


def test_adjacent_trainer_challenges_without_walking(monkeypatch):
    s, t = _scene(monkeypatch)
    s.player.place(10, 11)
    s.update(1 / 60)
    s.update(ALERT_TIME + 0.01)
    assert (t.x, t.y) == (10, 10)
    assert s.active_dialogue


def test_lost_trainer_returns_home():
    s, t = _scene()
    t.x, t.y = 10, 12
    s._pending_trainer = t
    s._apply_battle_result(BattleResult(party_states=s.party, lost=True))
    assert (t.x, t.y) == (10, 10)


def test_trainer_reward_still_pays():
    s, t = _scene()
    s._pending_trainer = t
    before = s.inventory.money
    s._apply_battle_result(BattleResult(party_states=s.party, won=True, reward=60))
    assert s.inventory.money == before + 60 and t.defeated
