from unittest.mock import patch

import pygame

from src.engine.battle_scene import TYPE_EFFECTIVENESS, BattleScene, Move
from src.engine.inventory import InventoryManager


class DummyManager:
    def __init__(self):
        self.battle_result = None


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
    _tux = scene.make_mascot("Tux")
    octocat = scene.make_mascot("Octocat")
    move = Move("Shellshock", 10, "Shell")
    multiplier = TYPE_EFFECTIVENESS.get((move.type, octocat.type), 1.0)
    assert multiplier == 2.0  # Shell vs Browser (Shell > Browser)
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
    inventory = InventoryManager()
    inventory.add_item("package", 1)
    manager = DummyManager()

    # Use party_states instead of party
    state = BattleScene(manager).make_mascot_state("Tux")
    scene = BattleScene(
        manager, party_states=[state], inventory=inventory, wild_species="Octocat"
    )

    scene.opponent.hp = 1  # Make capture likely

    # Mock random to ensure capture succeeds
    with patch("src.engine.battle_scene.random.random", return_value=0.1):
        scene._try_capture()

    # Check party states has captured mascot
    assert any(s["name"] == "Octocat" for s in scene.party_states)
    assert scene.captured is True

    # Verify captured mascot has full HP
    octocat_state = next(s for s in scene.party_states if s["name"] == "Octocat")
    assert octocat_state["hp"] == octocat_state["max_hp"]


# Test mascot faints when HP reaches 0
def test_mascot_faints_sets_fainted_flag():
    manager = DummyManager()
    state1 = BattleScene(manager).make_mascot_state("Tux")
    state2 = BattleScene(manager).make_mascot_state("BSD Daemon")
    scene = BattleScene(manager, party_states=[state1, state2])

    # Reduce player HP to 1
    scene.player.hp = 1

    # Opponent attacks
    scene._opponent_attack()

    # Check that player fainted
    assert scene.player.hp == 0
    assert scene.party_states[0]["fainted"] is True

    # Check that forced switch was triggered (if party has others available)
    assert scene.state == scene.STATE_PARTY_SELECT
    assert scene.forced_switch is True


# Test cannot switch to fainted mascot
def test_cannot_switch_to_fainted_mascot():
    manager = DummyManager()
    state1 = BattleScene(manager).make_mascot_state("Tux")
    state2 = BattleScene(manager).make_mascot_state("BSD Daemon")
    scene = BattleScene(manager, party_states=[state1, state2])

    # Mark second mascot as fainted
    scene.party_states[1]["fainted"] = True

    # Get available party members
    available = scene._get_available_party_indices()

    # Only first mascot should be available
    assert available == [0]
    assert 1 not in available


# Test all mascots faint leads to battle loss
def test_all_mascots_faint_battle_loss():
    manager = DummyManager()
    state1 = BattleScene(manager).make_mascot_state("Tux")
    scene = BattleScene(manager, party_states=[state1])

    # Reduce player HP to 1
    scene.player.hp = 1

    # Opponent attacks
    scene._opponent_attack()

    # Check that battle is over
    assert scene.player.hp == 0
    assert scene.party_states[0]["fainted"] is True
    assert scene.battle_over is True
    assert scene._check_all_fainted() is True


# Test fainted status persists in party states
def test_fainted_status_persists_in_party_states():
    manager = DummyManager()
    state1 = BattleScene(manager).make_mascot_state("Tux")
    state2 = BattleScene(manager).make_mascot_state("BSD Daemon")
    scene = BattleScene(manager, party_states=[state1, state2])

    # Mark first mascot as fainted
    scene.party_states[0]["fainted"] = True
    scene.player.hp = 0

    # Get party states
    states = scene.get_party_states()

    # Check fainted status is preserved
    assert states[0]["fainted"] is True
    assert states[1]["fainted"] is False


# Test party state has fainted field
def test_party_state_has_fainted_field():
    manager = DummyManager()
    scene = BattleScene(manager)

    # Check all party states have fainted field
    for state in scene.party_states:
        assert "fainted" in state
        assert state["fainted"] is False


# Test backwards compatibility for states without fainted field
def test_backwards_compatibility_no_fainted_field():
    manager = DummyManager()
    state = {
        "name": "Tux",
        "hp": 20,
        "max_hp": 24,
        "atk": 8,
        "defense": 6,
        "spd": 7,
        "type": "Kernel",
    }
    scene = BattleScene(manager, party_states=[state])

    # Check fainted field was added
    assert scene.party_states[0]["fainted"] is False


# Test fainted mascots cannot attack
def test_fainted_mascot_cannot_attack():
    manager = DummyManager()
    state1 = BattleScene(manager).make_mascot_state("Tux")
    state2 = BattleScene(manager).make_mascot_state("BSD Daemon")
    scene = BattleScene(manager, party_states=[state1, state2])

    # Mark active mascot as fainted
    scene.party_states[0]["fainted"] = True
    scene.player.hp = 0

    opponent_hp_before = scene.opponent.hp

    # Try to attack
    scene._player_attack(0)

    # Opponent should not have taken damage
    assert scene.opponent.hp == opponent_hp_before
    assert "unable to battle" in scene.msg


def test_hp_never_goes_negative():
    scene = BattleScene(DummyManager())
    scene.opponent.hp = 1
    scene._player_attack(2)
    assert scene.opponent.hp == 0

    scene = BattleScene(DummyManager(), party_states=[scene.make_mascot_state("Tux")])
    scene.player.hp = 1
    scene._opponent_attack()
    assert scene.player.hp == 0


def _press(scene, key=pygame.K_z):
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))


def _texts(scene):
    return [m.text for m in scene.messages]


def test_turn_is_narrated_in_order_with_hp_snapshots():
    """Both attacks and the effectiveness line are queued, not overwritten."""
    party = [BattleScene(DummyManager()).make_mascot_state("Tux")]
    scene = BattleScene(DummyManager(), party_states=party, wild_species="BSD Daemon")
    _press(scene)  # dismiss "A wild BSD Daemon appeared!"
    assert scene.state == scene.STATE_MENU

    with patch(
        "src.engine.battle_scene.random.choice", return_value=Move("Hit", 1, "Shell")
    ):
        _press(scene)  # Fight
        _press(scene)  # Peck (Kernel vs Shell)

    assert scene.state == scene.STATE_MESSAGE
    assert _texts(scene) == [
        "Tux used Peck!",
        "It's super effective!",
        "BSD Daemon used Hit!",
        "It's not very effective...",
    ]
    # The opponent's HP drops with the first line; the player's only later
    first, last = scene.messages[0], scene.messages[-1]
    assert first.opponent_hp == scene.opponent.hp
    assert first.player_hp == scene.player.max_hp
    assert last.player_hp == scene.player.hp

    for _ in range(4):
        _press(scene)
    assert scene.state == scene.STATE_MENU


def test_faster_opponent_attacks_first():
    party = [BattleScene(DummyManager()).make_mascot_state("BSD Daemon")]  # spd 5
    scene = BattleScene(
        DummyManager(), party_states=party, wild_species="Octocat", wild_level=5
    )
    scene.messages.clear()
    with patch(
        "src.engine.battle_scene.random.choice", return_value=Move("PR", 5, "Editor")
    ):
        scene._player_attack(0)
    assert _texts(scene)[0] == "Octocat used PR!"


def test_fainted_player_does_not_attack_after_faster_opponent():
    party = [BattleScene(DummyManager()).make_mascot_state("BSD Daemon", hp=1)]
    scene = BattleScene(
        DummyManager(), party_states=party, wild_species="Octocat", wild_level=5
    )
    opponent_hp = scene.opponent.hp
    scene._player_attack(0)
    assert scene.opponent.hp == opponent_hp
    assert scene.battle_over is True


def test_last_message_ends_battle():
    manager = DummyManager()
    manager.pop = lambda: setattr(manager, "popped", True)
    scene = BattleScene(manager, wild_species="Octocat")
    scene.messages.clear()
    scene.state = scene.STATE_MENU
    scene.menu_idx = scene.MENU_FLEE
    _press(scene)
    assert scene.battle_over and not hasattr(manager, "popped")
    _press(scene)  # dismiss "You fled!"
    assert manager.popped is True


def test_captured_mascot_joins_at_full_hp_even_if_duplicate():
    inventory = InventoryManager()
    inventory.add_item("package", 1)
    scene = BattleScene(DummyManager(), inventory=inventory, wild_species="Octocat")
    scene.party.append(scene.make_mascot("Octocat"))
    scene.party_states.append(scene.make_mascot_state("Octocat"))
    scene.opponent.hp = 1

    with patch("src.engine.battle_scene.random.random", return_value=0.1):
        scene._try_capture()

    assert sum(m.name == "Octocat" for m in scene.party) == 2
    assert scene.party[-1].hp == scene.party[-1].max_hp
    assert scene.get_party_states()[-1]["hp"] == scene.party[-1].max_hp


def test_capture_blocked_when_party_full():
    from src.constants import PARTY_MAX

    inventory = InventoryManager()
    inventory.add_item("package", 1)
    states = [BattleScene(DummyManager()).make_mascot_state("Tux")] * PARTY_MAX
    scene = BattleScene(
        DummyManager(), party_states=[dict(s) for s in states], inventory=inventory
    )

    scene._try_capture()

    assert scene.msg == "Your party is full!"
    assert inventory.get_item_count("package") == 1


def test_wild_species_rolled_from_encounter_table():
    from src.engine.mascots import WILD_ENCOUNTERS

    names = {e["species"] for e in WILD_ENCOUNTERS}
    for _ in range(20):
        assert BattleScene(DummyManager()).opponent.name in names


def test_unknown_species_fails_loudly():
    import pytest

    with pytest.raises(ValueError, match="Unknown mascot species"):
        BattleScene(DummyManager()).make_mascot_state("Clippy")


def test_every_species_loads_and_type_chart_is_full():
    from src.engine.mascots import (
        ELEMENT_TYPES,
        SPECIES,
        TYPE_EFFECTIVENESS,
        make_mascot,
    )

    assert len(SPECIES) >= 6
    for name, data in SPECIES.items():
        assert make_mascot(name).name == name
        assert 3 <= len(make_mascot(name).moves) <= 4
        assert data["type"] in ELEMENT_TYPES
        for move in data["learnset"]:
            assert move["type"] in ELEMENT_TYPES
    assert {d["type"] for d in SPECIES.values()} == set(ELEMENT_TYPES)
    for t in ELEMENT_TYPES:
        strong = [d for (a, d), m in TYPE_EFFECTIVENESS.items() if a == t and m > 1]
        weak = [d for (a, d), m in TYPE_EFFECTIVENESS.items() if a == t and m < 1]
        assert strong, f"{t} is not strong against anything"
        assert weak, f"{t} is not weak against anything"
