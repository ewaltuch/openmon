"""
Inventory system for Open-Mon: items, packages, consumables.
"""

import os
from functools import cache

import yaml

ITEMS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "items.yaml")
STARTING_MONEY = 100


class Item:
    """Base class for all items in the game."""

    TYPE_CONSUMABLE = "consumable"
    TYPE_KEY = "key"
    TYPE_PACKAGE = "package"

    def __init__(self, id, name, description, type_, effect=None, price=0):
        self.id = id
        self.name = name
        self.description = description
        self.type = type_
        self.price = price
        self.effect = effect  # Dictionary describing effect, e.g., {"heal": 20}

    def use(self, target):
        """Apply item effect to target. Returns True if item was consumed."""
        if self.type == self.TYPE_KEY:
            return False  # Key items are not consumed

        if self.effect:
            # Healing can't bring back a fainted mascot; that takes a revive
            if target.hp <= 0 and "revive" not in self.effect:
                return False
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

    @property
    def sell_price(self):
        """Half the buy price; key items can't be sold (0)."""
        return 0 if self.type == self.TYPE_KEY else self.price // 2


@cache
def load_items():
    """Item definitions from assets/items.yaml, keyed by id."""
    with open(ITEMS_PATH) as f:
        data = yaml.safe_load(f)
    return {
        item_id: Item(
            item_id,
            d["name"],
            d["description"],
            d["type"],
            d.get("effect"),
            d.get("price", 0),
        )
        for item_id, d in data.items()
    }


def get_item(item_id):
    """Look up an item; unknown ids raise ValueError."""
    try:
        return load_items()[item_id]
    except KeyError:
        raise ValueError(f"Unknown item: {item_id!r}") from None


ITEMS = load_items()


class InventoryManager:
    """Manages the player's inventory."""

    def __init__(self):
        self.items = {}  # {item_id: quantity}
        self.money = STARTING_MONEY
        self._item_definitions = ITEMS

    def add_item(self, item_id, quantity=1):
        """Add items to inventory. Unknown items raise ValueError."""
        get_item(item_id)
        self.items[item_id] = self.items.get(item_id, 0) + quantity
        return True

    def buy(self, item_id, quantity=1):
        """Spend money on items. Returns True if affordable."""
        cost = get_item(item_id).price * quantity
        if quantity < 1 or cost > self.money:
            return False
        self.money -= cost
        self.add_item(item_id, quantity)
        return True

    def sell(self, item_id, quantity=1):
        """Sell items at half price. Key items and missing stock are refused."""
        item = get_item(item_id)
        if item.type == Item.TYPE_KEY or quantity < 1:
            return False
        if not self.remove_item(item_id, quantity):
            return False
        self.money += item.sell_price * quantity
        return True

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
        # Handle old format (list) and new format (dict with "items" key)
        if isinstance(data, list):
            # Old format: list of item IDs - convert to dict with count 1
            self.items = {item_id: 1 for item_id in data}
        elif isinstance(data, dict):
            # New format: dict with "items" key
            self.items = data.get("items", {})
        else:
            # Fallback to empty inventory
            self.items = {}
