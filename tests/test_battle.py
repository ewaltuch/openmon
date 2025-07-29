import pytest
from src.engine.battle_scene import BattleScene, Mascot, Move, TYPE_EFFECTIVENESS

class DummyManager:
    def __init__(self):
        self.captured_mascot_name = None

# Test mascot creation and move types
def test_make_mascot_types():
    scene = BattleScene(DummyManager())
    tux = scene.make_mascot("Tux")
    assert tux.type == "Kernel"
    assert any(m.type == "Shell" for m in tux.moves)
    octocat = scene.make_mascot("Octocat")
    assert octocat.type == "Browser"
    assert any(m.type == "Browser" for m in octocat.moves)

# Test type effectiveness
def test_type_effectiveness():
    scene = BattleScene(DummyManager())
    tux = scene.make_mascot("Tux")
    octocat = scene.make_mascot("Octocat")
    move = Move("Shellshock", 10, "Shell")
    multiplier = TYPE_EFFECTIVENESS.get((move.type, octocat.type), 1.0)
    assert multiplier == 1.0  # Shell vs Browser (default)
    move2 = Move("Code", 8, "Editor")
    multiplier2 = TYPE_EFFECTIVENESS.get((move2.type, octocat.type), 1.0)
    assert multiplier2 == 0.5

# Test move selection and damage calculation
def test_player_attack_damage():
    scene = BattleScene(DummyManager())
    tux = scene.make_mascot("Tux")
    octocat = scene.make_mascot("Octocat")
    scene.player = tux
    scene.opponent = octocat
    # Use Shellshock (Shell vs Browser, multiplier=1.0)
    scene._player_attack(2)
    assert octocat.hp < octocat.max_hp

# Test capturing mascot adds to party
def test_capture_adds_to_party():
    scene = BattleScene(DummyManager())
    tux = scene.make_mascot("Tux")
    octocat = scene.make_mascot("Octocat")
    scene.player = tux
    scene.opponent = octocat
    scene.party = [tux]
    octocat.hp = 1  # Make capture likely
    scene._try_capture()
    assert any(m.name == "Octocat" for m in scene.party)
    assert scene.captured is True
