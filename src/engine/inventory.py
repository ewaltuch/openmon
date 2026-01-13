"""
Inventory system for Open-Mon: items, packages, consumables.
"""


class Item:
    """Base class for all items in the game."""

    TYPE_CONSUMABLE = "consumable"
    TYPE_KEY = "key"
    TYPE_PACKAGE = "package"

    def __init__(self, id, name, description, type_, effect=None):
        self.id = id
        self.name = name
        self.description = description
        self.type = type_
        self.effect = effect  # Dictionary describing effect, e.g., {"heal": 20}

    def use(self, target):
        """Apply item effect to target. Returns True if item was consumed."""
        if self.type == self.TYPE_KEY:
            return False  # Key items are not consumed

        if self.effect:
            if "heal" in self.effect:
                heal_amount = self.effect["heal"]
                if target.hp < target.max_hp:
                    target.hp = min(target.max_hp, target.hp + heal_amount)
                    return True
            elif "full_heal" in self.effect:
                if target.hp < target.max_hp:
                    target.hp = target.max_hp
                    return True
            elif "revive" in self.effect:
                if target.hp <= 0:
                    target.hp = target.max_hp // 2
                    return True

        return False


class InventoryManager:
    """Manages the player's inventory."""

    def __init__(self):
        self.items = {}  # {item_id: quantity}
        self._item_definitions = self._load_item_definitions()

    def _load_item_definitions(self):
        """Define all available items in the game."""
        return {
            "package": Item(
                "package",
                "Package",
                "Used to capture wild mascots. Higher success rate when opponent HP is low.",
                Item.TYPE_PACKAGE
            ),
            "health_pack": Item(
                "health_pack",
                "Health Pack",
                "Restores 20 HP to a mascot.",
                Item.TYPE_CONSUMABLE,
                {"heal": 20}
            ),
            "full_restore": Item(
                "full_restore",
                "Full Restore",
                "Fully restores HP to a mascot.",
                Item.TYPE_CONSUMABLE,
                {"full_heal": True}
            ),
            "revive": Item(
                "revive",
                "Revive",
                "Revives a fainted mascot with half HP.",
                Item.TYPE_CONSUMABLE,
                {"revive": True}
            ),
            "repo_key": Item(
                "repo_key",
                "Repository Key",
                "A key to unlock the main repository.",
                Item.TYPE_KEY
            )
        }

    def add_item(self, item_id, quantity=1):
        """Add items to inventory."""
        if item_id in self._item_definitions:
            self.items[item_id] = self.items.get(item_id, 0) + quantity
            return True
        return False

    def remove_item(self, item_id, quantity=1):
        """Remove items from inventory. Returns True if successful."""
        if item_id in self.items and self.items[item_id] >= quantity:
            self.items[item_id] -= quantity
            if self.items[item_id] == 0:
                del self.items[item_id]
            return True
        return False

    def has_item(self, item_id, quantity=1):
        """Check if player has enough of an item."""
        return self.items.get(item_id, 0) >= quantity

    def get_item_count(self, item_id):
        """Get quantity of a specific item."""
        return self.items.get(item_id, 0)

    def get_item(self, item_id):
        """Get item definition by ID."""
        return self._item_definitions.get(item_id)

    def get_all_items(self):
        """Get list of (item, quantity) tuples for all items in inventory."""
        result = []
        for item_id, quantity in self.items.items():
            item = self._item_definitions.get(item_id)
            if item:
                result.append((item, quantity))
        return result

    def use_item(self, item_id, target):
        """Use an item on a target. Returns True if item was consumed."""
        if not self.has_item(item_id):
            return False

        item = self.get_item(item_id)
        if not item:
            return False

        # For packages, don't consume here (handled in battle scene)
        if item.type == Item.TYPE_PACKAGE:
            return True

        consumed = item.use(target)
        if consumed:
            self.remove_item(item_id)

        return consumed

    def to_dict(self):
        """Serialize inventory to dictionary for saving."""
        return {"items": self.items}

    def from_dict(self, data):
        """Load inventory from dictionary."""
        self.items = data.get("items", {})
