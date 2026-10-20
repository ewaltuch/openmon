from unittest.mock import patch

from src.engine.battle_scene import BattleScene
from src.engine.inventory import InventoryManager
from src.engine.save import SaveManager


class DummyManager:
    def __init__(self):
        self.captured_mascot_name = None
        self.last_battle_party_states = None

    def push(self, scene):
        pass

    def pop(self):
        pass


def test_make_mascot_state_full_hp():
    """Test that make_mascot_state creates mascot with full HP by default."""
    scene = BattleScene(DummyManager())
    state = scene.make_mascot_state("Tux")
    assert state["hp"] == state["max_hp"]
    assert state["hp"] == 24
    assert state["name"] == "Tux"
    assert state["type"] == "Kernel"


def test_make_mascot_state_custom_hp():
    """Test that make_mascot_state accepts custom HP value."""
    scene = BattleScene(DummyManager())
    state = scene.make_mascot_state("Tux", hp=10)
    assert state["hp"] == 10
    assert state["max_hp"] == 24


def test_hydrate_mascot():
    """Test that hydrate_mascot creates Mascot object from state."""
    scene = BattleScene(DummyManager())
    state = scene.make_mascot_state("Tux", hp=10)
    mascot = scene.hydrate_mascot(state)
    assert mascot.name == "Tux"
    assert mascot.hp == 10
    assert mascot.max_hp == 24
    assert len(mascot.moves) == 3


def test_get_party_states():
    """Test that get_party_states extracts current HP."""
    scene = BattleScene(DummyManager())
    # Create party with damaged mascot
    states = [scene.make_mascot_state("Tux", hp=10)]
    scene2 = BattleScene(DummyManager(), party_states=states)

    # Damage the mascot more
    scene2.party[0].hp = 5

    # Get states should reflect new HP
    updated_states = scene2.get_party_states()
    assert updated_states[0]["hp"] == 5
    assert updated_states[0]["max_hp"] == 24


def test_battle_hp_persistence():
    """Test that HP persists through battle."""
    manager = DummyManager()

    # Create party with damaged mascot
    scene = BattleScene(manager)
    state = scene.make_mascot_state("Tux", hp=15)
    battle = BattleScene(manager, party_states=[state])

    # Simulate damage in battle
    battle.party[0].hp = 8

    # Simulate battle ending
    manager.last_battle_party_states = battle.get_party_states()

    # Verify HP is in returned states
    assert manager.last_battle_party_states[0]["hp"] == 8


def test_healing_item_persists():
    """Test that healing items persist HP changes."""
    manager = DummyManager()
    inventory = InventoryManager()
    inventory.add_item("health_pack", 1)

    # Create damaged mascot
    state = {
        "name": "Tux",
        "hp": 5,
        "max_hp": 24,
        "atk": 8,
        "defense": 6,
        "spd": 7,
        "type": "Kernel",
    }
    battle = BattleScene(manager, party_states=[state], inventory=inventory)

    # Use healing item
    battle.inventory.use_item("health_pack", battle.player)

    # Check HP increased (5 + 20 = 25, capped at 24)
    assert battle.player.hp == 24

    # Get states should reflect healed HP
    states = battle.get_party_states()
    assert states[0]["hp"] == 24


def test_captured_mascot_full_hp():
    """Test that captured mascots start with full HP."""
    manager = DummyManager()
    inventory = InventoryManager()
    inventory.add_item("package", 1)

    battle = BattleScene(manager, inventory=inventory)
    battle.opponent.hp = 1  # Make capture likely

    with patch("src.engine.battle_scene.random.random", return_value=0.1):
        battle._try_capture()

    # Check captured mascot has full HP in party states
    captured_state = battle.party_states[-1]
    assert captured_state["hp"] == captured_state["max_hp"]


def test_save_load_hp_persistence(tmp_path, monkeypatch):
    """Test that HP persists through save/load cycle."""
    monkeypatch.setattr("src.constants.SAVE_PATH", str(tmp_path / "save1.json"))

    # Create save with damaged mascot
    state = {
        "player": {"x": 16, "y": 16},
        "party": [
            {
                "name": "Tux",
                "hp": 10,
                "max_hp": 24,
                "atk": 8,
                "defense": 6,
                "spd": 7,
                "type": "Kernel",
            },
            {
                "name": "BSD Daemon",
                "hp": 20,
                "max_hp": 22,
                "atk": 7,
                "defense": 7,
                "spd": 5,
                "type": "Shell",
            },
        ],
        "inventory": {"items": {}},
    }

    SaveManager.save(state)
    loaded = SaveManager.load()

    assert loaded["party"][0]["hp"] == 10
    assert loaded["party"][0]["max_hp"] == 24
    assert loaded["party"][1]["hp"] == 20
    assert loaded["party"][1]["max_hp"] == 22


def test_party_switching_preserves_hp():
    """Test that party switching preserves individual HP values."""
    manager = DummyManager()

    # Create party with different HP values
    states = [
        {
            "name": "Tux",
            "hp": 10,
            "max_hp": 24,
            "atk": 8,
            "defense": 6,
            "spd": 7,
            "type": "Kernel",
        },
        {
            "name": "BSD Daemon",
            "hp": 15,
            "max_hp": 22,
            "atk": 7,
            "defense": 7,
            "spd": 5,
            "type": "Shell",
        },
    ]

    battle = BattleScene(manager, party_states=states)

    # Switch to second mascot using _execute_switch
    battle._execute_switch(1)
    assert battle.player.name == "BSD Daemon"
    assert battle.player.hp == 15

    # Get states should preserve both HP values
    final_states = battle.get_party_states()
    assert final_states[0]["hp"] == 10
    assert final_states[1]["hp"] == 15
