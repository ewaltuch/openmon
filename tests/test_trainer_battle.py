"""
Test trainer battle functionality.
"""
import pygame
from src.engine.scene_manager import SceneManager
from src.engine.battle_scene import BattleScene
from src.engine.inventory import InventoryManager
from src.engine.npc import NPC


def test_trainer_battle_init():
    """Test that trainer battles initialize correctly."""
    pygame.init()
    screen = pygame.display.set_mode((240, 160))
    manager = SceneManager()

    player_party = [
        {
            "name": "Tux",
            "hp": 24,
            "max_hp": 24,
            "atk": 8,
            "defense": 6,
            "spd": 7,
            "type": "Kernel",
            "fainted": False
        }
    ]

    opponent_party_states = [
        {
            "name": "BSD Daemon",
            "hp": 22,
            "max_hp": 22,
            "atk": 7,
            "defense": 7,
            "spd": 5,
            "type": "Shell",
            "fainted": False
        }
    ]

    inventory = InventoryManager()
    inventory.add_item("package", 5)

    # Create battle scene with opponent party
    from src.engine.battle_scene import BattleScene
    bs = BattleScene(manager)
    opponent_party = [bs.hydrate_mascot(state) for state in opponent_party_states]

    battle = BattleScene(
        manager,
        party_states=player_party,
        inventory=inventory,
        opponent_party=opponent_party,
        is_trainer_battle=True
    )

    # Verify trainer battle setup
    assert battle.is_trainer_battle is True
    assert battle.opponent.name == "BSD Daemon"
    assert "Trainer challenges you" in battle.msg
    assert battle.player.name == "Tux"

    pygame.quit()


def test_trainer_battle_no_capture():
    """Test that you cannot capture in trainer battles."""
    pygame.init()
    screen = pygame.display.set_mode((240, 160))
    manager = SceneManager()

    player_party = [
        {
            "name": "Tux",
            "hp": 24,
            "max_hp": 24,
            "atk": 8,
            "defense": 6,
            "spd": 7,
            "type": "Kernel",
            "fainted": False
        }
    ]

    opponent_party_states = [
        {
            "name": "BSD Daemon",
            "hp": 22,
            "max_hp": 22,
            "atk": 7,
            "defense": 7,
            "spd": 5,
            "type": "Shell",
            "fainted": False
        }
    ]

    inventory = InventoryManager()
    inventory.add_item("package", 5)

    # Create trainer battle
    from src.engine.battle_scene import BattleScene
    bs = BattleScene(manager)
    opponent_party = [bs.hydrate_mascot(state) for state in opponent_party_states]

    battle = BattleScene(
        manager,
        party_states=player_party,
        inventory=inventory,
        opponent_party=opponent_party,
        is_trainer_battle=True
    )

    # Try to capture
    initial_packages = inventory.get_item_count("package")
    battle._try_capture()

    # Verify capture was blocked
    assert battle.msg == "You can't capture a trainer's mascot!"
    assert inventory.get_item_count("package") == initial_packages  # No package consumed
    assert battle.captured is False

    pygame.quit()


def test_npc_trainer_flag():
    """Test that NPC trainer flag works correctly."""
    # Regular NPC
    npc1 = NPC(
        id="npc1",
        name="Linus",
        x=5,
        y=8,
        sprite="tux",
        dialogue=["Hello!"]
    )
    assert npc1.is_trainer() is False

    # Trainer NPC (not defeated)
    trainer1 = NPC(
        id="trainer1",
        name="Richard",
        x=8,
        y=10,
        sprite="trainer",
        dialogue=["Let's battle!"],
        trainer=True,
        party=["BSD Daemon", "Tux"]
    )
    assert trainer1.is_trainer() is True

    # Trainer NPC (defeated)
    trainer2 = NPC(
        id="trainer2",
        name="Ada",
        x=10,
        y=12,
        sprite="trainer",
        dialogue=["Good battle!"],
        trainer=True,
        party=["Octocat"],
        defeated=True
    )
    assert trainer2.is_trainer() is False  # Already defeated


def test_trainer_battle_no_flee():
    """Test that you cannot flee from trainer battles."""
    pygame.init()
    screen = pygame.display.set_mode((240, 160))
    manager = SceneManager()

    player_party = [
        {
            "name": "Tux",
            "hp": 24,
            "max_hp": 24,
            "atk": 8,
            "defense": 6,
            "spd": 7,
            "type": "Kernel",
            "fainted": False
        }
    ]

    opponent_party_states = [
        {
            "name": "BSD Daemon",
            "hp": 22,
            "max_hp": 22,
            "atk": 7,
            "defense": 7,
            "spd": 5,
            "type": "Shell",
            "fainted": False
        }
    ]

    inventory = InventoryManager()

    # Create trainer battle
    from src.engine.battle_scene import BattleScene
    bs = BattleScene(manager)
    opponent_party = [bs.hydrate_mascot(state) for state in opponent_party_states]

    battle = BattleScene(
        manager,
        party_states=player_party,
        inventory=inventory,
        opponent_party=opponent_party,
        is_trainer_battle=True
    )

    # Try to select flee option (menu index 2)
    battle.menu_idx = battle.MENU_FLEE

    # Simulate pressing Z to confirm flee
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z)
    battle.handle_event(event)

    # Verify flee was blocked
    assert battle.msg == "You can't flee from a trainer battle!"
    assert battle.battle_over is False  # Battle should continue
    assert battle.state == "menu"  # Should return to menu

    pygame.quit()


def test_trainer_defeated_dialogue():
    """Test that trainers show different dialogue after defeat."""
    # Create trainer with defeated dialogue
    trainer = NPC(
        id="trainer1",
        name="Richard",
        x=8,
        y=10,
        sprite="trainer",
        dialogue=["Hey! I'm a trainer!", "Let's battle!"],
        defeated_dialogue=["You're really strong!", "I need to train more..."],
        trainer=True,
        party=["BSD Daemon", "Tux"],
        defeated=False
    )

    # Before defeat - should show regular dialogue
    assert trainer.talk() == "Hey! I'm a trainer!"
    assert trainer.talk() == "Let's battle!"
    assert trainer.talk() is None  # Dialogue exhausted

    # Mark as defeated
    trainer.defeated = True

    # After defeat - should show defeated dialogue
    assert trainer.talk() == "You're really strong!"
    assert trainer.talk() == "I need to train more..."
    assert trainer.talk() is None  # Dialogue exhausted
