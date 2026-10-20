"""
Pause-menu screens for Open-Mon: the party view (Mascots) and the Bag.

Both are duck-typed scenes pushed on top of the overworld. They edit the
overworld's party state dicts and InventoryManager in place, so changes are
picked up by the next save.
"""

import pygame

from src.constants import GB_PALETTE
from src.engine.fonts import get_font
from src.engine.inventory import Item

CONFIRM_KEYS = (pygame.K_z, pygame.K_RETURN, pygame.K_KP_ENTER)
BACK_KEYS = (pygame.K_x, pygame.K_ESCAPE)


class StateTarget:
    """Lets Item.use work on a party state dict (hp/max_hp attributes)."""

    def __init__(self, state):
        self.state = state

    @property
    def hp(self):
        return self.state["hp"]

    @hp.setter
    def hp(self, value):
        self.state["hp"] = value

    @property
    def max_hp(self):
        return self.state["max_hp"]


def selectable_targets(item, party):
    """Indices of party states the item can be used on (mirrors the battle menu)."""
    if "revive" in (item.effect or {}):
        return [i for i, s in enumerate(party) if s.get("fainted") or s["hp"] <= 0]
    return [
        i
        for i, s in enumerate(party)
        if not s.get("fainted") and 0 < s["hp"] < s["max_hp"]
    ]


def use_item_on_state(inventory, item, state):
    """Use a consumable on a party state, keeping `fainted` in sync."""
    if not inventory.use_item(item.id, StateTarget(state)):
        return False
    if state["hp"] > 0:
        state["fainted"] = False
    return True


def _box(surface, rect):
    pygame.draw.rect(surface, GB_PALETTE[0], rect)
    pygame.draw.rect(surface, GB_PALETTE[3], rect, 1)


def _draw_party_rows(surface, party, cursor=None, top=18, row_h=26):
    font = get_font(10)
    for i, s in enumerate(party):
        y = top + i * row_h
        color = GB_PALETTE[3] if i == cursor else GB_PALETTE[2]
        marker = ">" if i == cursor else " "
        status = " (fainted)" if s.get("fainted") else ""
        surface.blit(
            font.render(
                f"{marker}{s['name']} Lv{s.get('level', 5)}{status}", True, color
            ),
            (6, y),
        )
        hp = f"{s['hp']}/{s['max_hp']}"
        surface.blit(font.render(hp, True, color), (240 - 6 - font.size(hp)[0], y))
        bar = pygame.Rect(14, y + 13, 212, 5)
        pygame.draw.rect(surface, GB_PALETTE[3], bar, 1)
        fill = int((bar.w - 2) * max(0, s["hp"]) / max(1, s["max_hp"]))
        if fill > 0:
            pygame.draw.rect(surface, GB_PALETTE[2], (bar.x + 1, bar.y + 1, fill, 3))


class PartyScreen:
    """Read-only list of party mascots with HP."""

    def __init__(self, manager, party):
        self.manager = manager
        self.party = party

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in BACK_KEYS + CONFIRM_KEYS:
            self.manager.pop()

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(GB_PALETTE[0])
        _box(surface, (0, 0, 240, 160))
        surface.blit(get_font(12).render("Mascots", True, GB_PALETTE[3]), (6, 2))
        _draw_party_rows(surface, self.party)


class BagScreen:
    """Item list; consumables then ask for a party member to use them on."""

    MODE_ITEMS = "items"
    MODE_TARGET = "target"

    def __init__(self, manager, party, inventory):
        self.manager = manager
        self.party = party
        self.inventory = inventory
        self.mode = self.MODE_ITEMS
        self.item_idx = 0
        self.target_idx = 0
        self.pending_item = None
        self.message = ""

    def _items(self):
        return self.inventory.get_all_items()

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.mode == self.MODE_ITEMS:
            self._handle_items(event.key)
        else:
            self._handle_target(event.key)

    def _handle_items(self, key):
        items = self._items()
        if key in BACK_KEYS:
            self.manager.pop()
        elif not items:
            return
        elif key == pygame.K_UP:
            self.item_idx = (self.item_idx - 1) % len(items)
        elif key == pygame.K_DOWN:
            self.item_idx = (self.item_idx + 1) % len(items)
        elif key in CONFIRM_KEYS:
            item, _ = items[self.item_idx]
            if item.type != Item.TYPE_CONSUMABLE:
                self.message = "Can't use that here!"
                return
            targets = selectable_targets(item, self.party)
            if not targets:
                self.message = f"{item.name} would have no effect!"
                return
            self.pending_item = item
            self.target_idx = targets[0]
            self.mode = self.MODE_TARGET
            self.message = ""

    def _handle_target(self, key):
        targets = selectable_targets(self.pending_item, self.party)
        if key in BACK_KEYS:
            self.mode = self.MODE_ITEMS
            self.pending_item = None
        elif key in (pygame.K_UP, pygame.K_DOWN) and targets:
            step = -1 if key == pygame.K_UP else 1
            pos = targets.index(self.target_idx) if self.target_idx in targets else 0
            self.target_idx = targets[(pos + step) % len(targets)]
        elif key in CONFIRM_KEYS and self.target_idx in targets:
            item = self.pending_item
            state = self.party[self.target_idx]
            if use_item_on_state(self.inventory, item, state):
                self.message = f"Used {item.name} on {state['name']}!"
            else:
                self.message = f"{item.name} had no effect!"
            self.pending_item = None
            self.mode = self.MODE_ITEMS
            self.item_idx = min(self.item_idx, max(0, len(self._items()) - 1))

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(GB_PALETTE[0])
        _box(surface, (0, 0, 240, 160))
        title_font = get_font(12)
        font = get_font(10)
        if self.mode == self.MODE_TARGET:
            prompt = f"Use {self.pending_item.name} on:"
            surface.blit(title_font.render(prompt, True, GB_PALETTE[3]), (6, 2))
            _draw_party_rows(surface, self.party, self.target_idx)
            return
        surface.blit(title_font.render("Bag", True, GB_PALETTE[3]), (6, 2))
        items = self._items()
        if not items:
            surface.blit(font.render("Empty", True, GB_PALETTE[2]), (10, 24))
        for i, (item, qty) in enumerate(items):
            y = 20 + i * 14
            color = GB_PALETTE[3] if i == self.item_idx else GB_PALETTE[2]
            marker = ">" if i == self.item_idx else " "
            surface.blit(font.render(f"{marker}{item.name}", True, color), (6, y))
            q = f"x{qty}"
            surface.blit(font.render(q, True, color), (234 - font.size(q)[0], y))
        if items:
            desc = items[self.item_idx][0].description
            from src.engine.fonts import wrap_text

            for j, line in enumerate(wrap_text(font, desc, 226)[:2]):
                surface.blit(font.render(line, True, GB_PALETTE[3]), (6, 112 + j * 12))
        if self.message:
            surface.blit(font.render(self.message, True, GB_PALETTE[3]), (6, 144))
