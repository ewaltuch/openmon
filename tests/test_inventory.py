"""
Tests for the inventory system in Open-Mon.
"""
import pytest
from src.engine.inventory import Item, InventoryManager
from src.engine.battle_scene import Mascot, Move


class TestItem:
    """Test the Item class."""

    def test_item_creation(self):
        """Test creating items with different types."""
        package = Item("package", "Package", "Capture item", Item.TYPE_PACKAGE)
        assert package.name == "Package"
        assert package.type == Item.TYPE_PACKAGE

        health_pack = Item("health_pack", "Health Pack", "Heals 20 HP", Item.TYPE_CONSUMABLE, {"heal": 20})
        assert health_pack.name == "Health Pack"
        assert health_pack.effect == {"heal": 20}

    def test_item_use_heal(self):
        """Test using a healing item on a mascot."""
        # Create a mascot with low HP
        mascot = Mascot("Tux", 24, 8, 6, 7, None, [], "Kernel")
        mascot.hp = 10

        # Create and use a health pack
        health_pack = Item("health_pack", "Health Pack", "Heals 20 HP", Item.TYPE_CONSUMABLE, {"heal": 20})
        consumed = health_pack.use(mascot)

        assert consumed is True
        assert mascot.hp == 24  # Capped at max HP

    def test_item_use_full_heal(self):
        """Test using a full restore item."""
        mascot = Mascot("Tux", 24, 8, 6, 7, None, [], "Kernel")
        mascot.hp = 5

        full_restore = Item("full_restore", "Full Restore", "Fully heals", Item.TYPE_CONSUMABLE, {"full_heal": True})
        consumed = full_restore.use(mascot)

        assert consumed is True
        assert mascot.hp == 24

    def test_item_use_no_effect_when_full_hp(self):
        """Test that healing items have no effect when mascot is at full HP."""
        mascot = Mascot("Tux", 24, 8, 6, 7, None, [], "Kernel")
        mascot.hp = 24

        health_pack = Item("health_pack", "Health Pack", "Heals 20 HP", Item.TYPE_CONSUMABLE, {"heal": 20})
        consumed = health_pack.use(mascot)

        assert consumed is False

    def test_key_item_not_consumed(self):
        """Test that key items are not consumed when used."""
        mascot = Mascot("Tux", 24, 8, 6, 7, None, [], "Kernel")
        key_item = Item("repo_key", "Repository Key", "Opens repository", Item.TYPE_KEY)
        consumed = key_item.use(mascot)

        assert consumed is False


class TestInventoryManager:
    """Test the InventoryManager class."""

    def test_inventory_initialization(self):
        """Test that inventory starts empty."""
        inventory = InventoryManager()
        assert inventory.get_all_items() == []

    def test_add_item(self):
        """Test adding items to inventory."""
        inventory = InventoryManager()
        inventory.add_item("package", 5)

        assert inventory.has_item("package", 5)
        assert inventory.get_item_count("package") == 5

    def test_add_multiple_items(self):
        """Test adding multiple different items."""
        inventory = InventoryManager()
        inventory.add_item("package", 3)
        inventory.add_item("health_pack", 2)

        assert inventory.get_item_count("package") == 3
        assert inventory.get_item_count("health_pack") == 2

    def test_remove_item(self):
        """Test removing items from inventory."""
        inventory = InventoryManager()
        inventory.add_item("package", 5)
        removed = inventory.remove_item("package", 2)

        assert removed is True
        assert inventory.get_item_count("package") == 3

    def test_remove_all_items(self):
        """Test removing all of an item type."""
        inventory = InventoryManager()
        inventory.add_item("package", 3)
        inventory.remove_item("package", 3)

        assert inventory.get_item_count("package") == 0
        assert not inventory.has_item("package")

    def test_remove_item_not_enough(self):
        """Test that removing more items than available fails."""
        inventory = InventoryManager()
        inventory.add_item("package", 2)
        removed = inventory.remove_item("package", 5)

        assert removed is False
        assert inventory.get_item_count("package") == 2

    def test_has_item(self):
        """Test checking item availability."""
        inventory = InventoryManager()
        inventory.add_item("package", 3)

        assert inventory.has_item("package")
        assert inventory.has_item("package", 3)
        assert not inventory.has_item("package", 4)
        assert not inventory.has_item("nonexistent")

    def test_get_item_definition(self):
        """Test retrieving item definitions."""
        inventory = InventoryManager()
        package = inventory.get_item("package")

        assert package is not None
        assert package.name == "Package"
        assert package.type == Item.TYPE_PACKAGE

    def test_get_all_items(self):
        """Test getting all items in inventory."""
        inventory = InventoryManager()
        inventory.add_item("package", 5)
        inventory.add_item("health_pack", 2)

        items = inventory.get_all_items()
        assert len(items) == 2

        # Check that we get (item, quantity) tuples
        item_dict = {item.id: qty for item, qty in items}
        assert item_dict["package"] == 5
        assert item_dict["health_pack"] == 2

    def test_use_item(self):
        """Test using an item through the inventory manager."""
        inventory = InventoryManager()
        inventory.add_item("health_pack", 2)

        mascot = Mascot("Tux", 24, 8, 6, 7, None, [], "Kernel")
        mascot.hp = 10

        consumed = inventory.use_item("health_pack", mascot)

        assert consumed is True
        assert mascot.hp == 24
        assert inventory.get_item_count("health_pack") == 1

    def test_use_item_not_in_inventory(self):
        """Test using an item that's not in inventory."""
        inventory = InventoryManager()
        mascot = Mascot("Tux", 24, 8, 6, 7, None, [], "Kernel")
        mascot.hp = 10

        consumed = inventory.use_item("health_pack", mascot)

        assert consumed is False

    def test_serialization(self):
        """Test saving and loading inventory."""
        inventory = InventoryManager()
        inventory.add_item("package", 5)
        inventory.add_item("health_pack", 3)

        # Serialize
        data = inventory.to_dict()
        assert "items" in data
        assert data["items"]["package"] == 5
        assert data["items"]["health_pack"] == 3

        # Deserialize into new inventory
        new_inventory = InventoryManager()
        new_inventory.from_dict(data)

        assert new_inventory.get_item_count("package") == 5
        assert new_inventory.get_item_count("health_pack") == 3

    def test_add_invalid_item(self):
        """Test that adding an invalid item fails."""
        inventory = InventoryManager()
        result = inventory.add_item("nonexistent_item", 5)

        assert result is False
        assert inventory.get_item_count("nonexistent_item") == 0

    def test_backwards_compatibility_old_inventory_format(self):
        """Test loading old save format (list instead of dict)."""
        inventory = InventoryManager()

        # Old format: list of item IDs
        old_format_data = ["package", "health_pack", "package"]
        inventory.from_dict(old_format_data)

        # Should convert to new format with counts
        assert inventory.get_item_count("package") >= 1
        assert inventory.get_item_count("health_pack") >= 1

        # New format: dict with "items" key
        inventory2 = InventoryManager()
        new_format_data = {"items": {"package": 5, "health_pack": 3}}
        inventory2.from_dict(new_format_data)

        assert inventory2.get_item_count("package") == 5
        assert inventory2.get_item_count("health_pack") == 3
