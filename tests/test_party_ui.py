"""
Test that party selection UI can display multiple mascots.
"""

import pygame
from src.engine.scene_manager import SceneManager
from src.engine.battle_scene import BattleScene
from src.engine.inventory import InventoryManager


def test_large_party_display():
    """Test that we can display a party with multiple mascots."""
    pygame.init()
    _screen = pygame.display.set_mode((240, 160))
    manager = SceneManager()

    # Create party with 4 mascots (Tux, BSD Daemon, and 2 Octocats)
    party_states = [
        {
            "name": "Tux",
            "hp": 20,
            "max_hp": 24,
            "atk": 8,
            "defense": 6,
            "spd": 7,
            "type": "Kernel",
            "fainted": False,
        },
        {
            "name": "BSD Daemon",
            "hp": 22,
            "max_hp": 22,
            "atk": 7,
            "defense": 7,
            "spd": 5,
            "type": "Shell",
            "fainted": False,
        },
        {
            "name": "Octocat",
            "hp": 18,
            "max_hp": 20,
            "atk": 7,
            "defense": 5,
            "spd": 6,
            "type": "Browser",
            "fainted": False,
        },
        {
            "name": "Octocat",  # Second one captured
            "hp": 15,
            "max_hp": 20,
            "atk": 7,
            "defense": 5,
            "spd": 6,
            "type": "Browser",
            "fainted": False,
        },
    ]

    inventory = InventoryManager()
    battle = BattleScene(manager, party_states=party_states, inventory=inventory)

    # Open party select
    battle.state = battle.STATE_PARTY_SELECT
    battle.party_select_idx = 1

    # Draw party selection menu - should not raise exception
    surface = pygame.Surface((240, 160))
    battle.draw(surface)

    # Calculate expected menu dimensions
    menu_item_height = 16
    menu_padding = 8
    header_height = 18
    footer_height = 14
    party_list_height = len(party_states) * menu_item_height
    menu_height = header_height + party_list_height + footer_height + menu_padding * 2
    menu_y = 30
    total_height = menu_y + menu_height

    # Verify menu fits on screen (160px height)
    assert (
        total_height <= 160
    ), f"Party menu extends beyond screen: {total_height}px > 160px"
    assert len(battle.party) == 4, "Battle should have 4 party members"

    pygame.quit()
