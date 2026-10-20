"""
BattleScene implementation for Open-Mon: simple turn-based battle, UI, capture.

Game logic resolves a whole turn immediately; what happened is queued as
BattleMessages (text plus an HP snapshot) that the player steps through with
Z, so the screen shows the turn in order. Sounds and hit effects ride on the
same queue: a message can carry a `sound` and an `effect`.
"""

import random
from collections import deque, namedtuple

import pygame

from src.constants import GB_PALETTE, PARTY_MAX, SCREEN_HEIGHT, SCREEN_WIDTH
from src.engine import audio, mascots
from src.engine.fonts import get_font, wrap_text
from src.engine.mascots import (  # noqa: F401 - re-exported for callers/tests
    ELEMENT_TYPES,
    TYPE_EFFECTIVENESS,
    Mascot,
    Move,
)

CONFIRM_KEYS = (pygame.K_z, pygame.K_RETURN, pygame.K_KP_ENTER)
# Arrow key -> cursor step in a two-column grid menu
GRID_STEPS = {pygame.K_UP: -2, pygame.K_DOWN: 2, pygame.K_LEFT: -1, pygame.K_RIGHT: 1}

# What the screen shows while a message is up
BattleMessage = namedtuple(
    "BattleMessage",
    "text player player_hp opponent opponent_hp sound effect",
    defaults=(None, None),
)

# Characters revealed per second by the typewriter text; 0 shows text at once
TEXT_CPS = 45
PROMPT_BLINK = 0.4  # seconds per on/off phase of the "next" arrow
EFFECT_TIME = 0.4  # seconds a hit flash/shake lasts
HIT_PLAYER = "hit_player"
HIT_OPPONENT = "hit_opponent"

# Damage = power * atk / defense * DAMAGE_SCALE * type multiplier * random
DAMAGE_SCALE = 0.7
DAMAGE_RANDOM = (0.85, 1.0)
# Own generator so tests can seed damage without disturbing other randomness
damage_rng = random.Random()

BOX_H = 48
BOX_Y = SCREEN_HEIGHT - BOX_H
LINE_H = 14
SPRITE_SCALE = 2


class BattleScene:
    MENU_FIGHT = 0
    MENU_ITEM = 1
    MENU_FLEE = 2
    MENU_SWITCH = 3

    STATE_MENU = "menu"
    STATE_MOVE_SELECT = "move_select"
    STATE_ITEM_SELECT = "item_select"
    STATE_PARTY_SELECT = "party_select"
    STATE_MESSAGE = "message"

    def __init__(
        self,
        manager,
        party_states=None,
        inventory=None,
        opponent_party=None,
        is_trainer_battle=False,
        wild_species=None,
        reward=0,
        wild_level=None,
    ):
        self.manager = manager
        self.is_trainer_battle = is_trainer_battle
        self.reward = reward  # Money for a win (trainer battles)
        audio.play_music("battle")

        # Default party if none provided
        if party_states is None:
            party_states = [
                self.make_mascot_state("Tux"),
                self.make_mascot_state("BSD Daemon"),
            ]

        # Store party states for syncing later (ensure fainted field exists)
        self.party_states = []
        for state in party_states:
            if "fainted" not in state:
                state["fainted"] = False
            self.party_states.append(state)

        # Hydrate mascots from states
        self.party = [self.hydrate_mascot(state) for state in self.party_states]

        self.active_idx = 0
        # If first mascot is fainted, find first non-fainted one
        for i in range(len(self.party)):
            if not self.party_states[i].get("fainted", False):
                self.active_idx = i
                break

        self.player = self.party[self.active_idx]

        self.messages = deque()
        self._status = None  # One-off feedback shown next to the menu
        self._last_text = ""
        self._next_state = self.STATE_MENU

        # Set up opponent based on battle type
        if is_trainer_battle and opponent_party:
            # Trainer battle - use first mascot from opponent party
            self.opponent_party = list(opponent_party)
            self.opponent = self.opponent_party[0]
            self._say(f"Trainer challenges you with {self.opponent.name}!")
        else:
            # Wild encounter
            if wild_species is None:
                wild_species = mascots.roll_wild_encounter()
            if wild_level is None:
                wild_level = mascots.wild_level(wild_species)
            self.opponent = self.make_mascot(wild_species, wild_level)
            self.opponent_party = [self.opponent]
            self._say(f"A wild {self.opponent.name} appeared!")

        self._reset_message_timers()
        self.menu_idx = 0
        self.state = self.STATE_MESSAGE
        self.captured = False
        self.battle_over = False
        self.move_idx = 0
        self.item_idx = 0
        self.party_select_idx = 0
        self.forced_switch = False
        self.inventory = inventory
        self.pending_item = None
        # Party indices that have fought the current opponent (they share XP)
        self._participants = {self.active_idx}

    @property
    def msg(self):
        """The most recent battle text, queued or status."""
        return self._last_text

    @msg.setter
    def msg(self, text):
        # Status feedback (e.g. "You can't flee...") that isn't part of a turn
        self._status = text
        self._last_text = text

    def _say(self, text, sound=None, effect=None):
        """Queue a turn message, snapshotting what the screen should show.

        `sound` (an audio.SFX name) plays when the message is first shown;
        `effect` (HIT_PLAYER / HIT_OPPONENT) flashes and shakes that sprite.
        """
        self.messages.append(
            BattleMessage(
                text,
                self.player,
                self.player.hp,
                self.opponent,
                self.opponent.hp,
                sound,
                effect,
            )
        )
        self._last_text = text

    def _reset_message_timers(self):
        self._text_pos = 0.0
        self._effect_t = 0.0
        self._clock = 0.0

    def _show(self, message):
        """A queued message just became the current one."""
        self._reset_message_timers()
        if message.sound:
            audio.play_sfx(message.sound)

    def _text_done(self):
        if not self.messages:
            return True
        return TEXT_CPS <= 0 or self._text_pos >= len(self.messages[0].text)

    @property
    def menu_names(self):
        names = ["Fight", "Item", "Flee"]
        if len(self.party) > 1:
            names.append("Switch")
        return names

    # Thin wrappers over the species registry (src/engine/mascots.py)
    def make_mascot(self, name, level=None):
        return mascots.make_mascot(name, level)

    def make_mascot_state(self, name, hp=None, level=None):
        return mascots.make_state(name, hp, level)

    def hydrate_mascot(self, state):
        return mascots.hydrate(state)

    def get_party_states(self):
        """
        Extract current HP from Mascot objects and return list of state dictionaries.
        """
        states = []
        for i, mascot in enumerate(self.party):
            states.append(
                {
                    "name": mascot.name,
                    "level": mascot.level,
                    "xp": mascot.xp,
                    "hp": mascot.hp,
                    "max_hp": mascot.max_hp,
                    "atk": mascot.atk,
                    "defense": mascot.defense,
                    "spd": mascot.spd,
                    "type": mascot.type,
                    "fainted": self.party_states[i].get("fainted", False),
                }
            )
        return states

    def _get_available_party_indices(self):
        """Get list of indices for non-fainted party members."""
        return [
            i
            for i in range(len(self.party))
            if not self.party_states[i].get("fainted", False)
        ]

    def _get_selectable_party_indices(self):
        """Indices the party menu may select: item targets or switch candidates."""
        item = self.pending_item
        if item is not None:
            if "revive" in item.effect:
                return [
                    i
                    for i in range(len(self.party))
                    if self.party_states[i].get("fainted", False)
                ]
            return [
                i
                for i in self._get_available_party_indices()
                if self.party[i].hp < self.party[i].max_hp
            ]
        return [i for i in self._get_available_party_indices() if i != self.active_idx]

    def _check_all_fainted(self):
        """Check if all party members have fainted."""
        return all(state.get("fainted", False) for state in self.party_states)

    def _opponent_party_fainted(self):
        """Check if every opponent mascot has fainted."""
        return all(m.hp <= 0 for m in self.opponent_party)

    def _calc_damage(self, move, attacker, defender):
        """Return (damage, type multiplier) for attacker using move on defender.

        power * atk / defense, scaled, times type effectiveness and a small
        random factor (seed `damage_rng` in tests); always at least 1.
        """
        multiplier = TYPE_EFFECTIVENESS.get((move.type, defender.type), 1.0)
        base = move.power * attacker.atk / max(1, defender.defense) * DAMAGE_SCALE
        dmg = int(base * multiplier * damage_rng.uniform(*DAMAGE_RANDOM))
        return max(1, dmg), multiplier

    def _attack(self, attacker, defender, move):
        """Apply one attack and narrate it."""
        dmg, multiplier = self._calc_damage(move, attacker, defender)
        defender.hp = max(0, defender.hp - dmg)
        effect = HIT_PLAYER if defender is self.player else HIT_OPPONENT
        self._say(f"{attacker.name} used {move.name}!", "hit", effect)
        if multiplier > 1.0:
            self._say("It's super effective!")
        elif multiplier < 1.0:
            self._say("It's not very effective...")

    def _execute_switch(self, new_idx):
        """Execute a party switch to the given index."""
        self.active_idx = new_idx
        self.player = self.party[self.active_idx]
        self._participants.add(new_idx)
        self._say(f"Go, {self.player.name}!")
        self.state = self.STATE_MENU

    def _finish_battle(self):
        """Hand the outcome to the overworld and leave the battle."""
        if self._check_all_fainted():
            # Revive all mascots for overworld
            revived_states = self.get_party_states()
            for state in revived_states:
                state["hp"] = state["max_hp"]
                state["fainted"] = False
            self.manager.last_battle_party_states = revived_states
            self.manager.battle_loss_reset = True
        else:
            self.manager.last_battle_party_states = self.get_party_states()
            if self._opponent_party_fainted():
                self.manager.last_battle_won = True
                if self.reward:
                    self.manager.last_battle_reward = self.reward
        audio.play_music("overworld")
        self.manager.pop()

    def _advance_message(self):
        if self.messages:
            self.messages.popleft()
        if self.messages:
            self._show(self.messages[0])
            return
        if self.battle_over:
            self._finish_battle()
        else:
            self._status = None
            self.state = self._next_state

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.state == self.STATE_MESSAGE:
            if event.key in CONFIRM_KEYS or event.key == pygame.K_x:
                if self._text_done():
                    self._advance_message()
                else:
                    self._text_pos = len(self.messages[0].text)
            return
        if self.battle_over:
            self._finish_battle()
            return

        handlers = {
            self.STATE_MENU: self._handle_menu,
            self.STATE_MOVE_SELECT: self._handle_move_select,
            self.STATE_ITEM_SELECT: self._handle_item_select,
            self.STATE_PARTY_SELECT: self._handle_party_select,
        }
        if event.key in GRID_STEPS:
            audio.play_sfx("move")
        elif event.key in CONFIRM_KEYS:
            audio.play_sfx("confirm")
        handlers[self.state](event.key)

        # If the action produced narration, play it before continuing
        if self.messages:
            self._show(self.messages[0])
            self._next_state = self.state
            self.state = self.STATE_MESSAGE

    @staticmethod
    def _grid_move(idx, key, count):
        """Move a cursor in a two-column grid of count entries."""
        new_idx = idx + GRID_STEPS.get(key, 0)
        return new_idx if 0 <= new_idx < count else idx

    def _handle_menu(self, key):
        # Check if current mascot is fainted - shouldn't be in menu state if so
        if self.party_states[self.active_idx].get("fainted", False):
            return

        if key in GRID_STEPS:
            self.menu_idx = self._grid_move(self.menu_idx, key, len(self.menu_names))
        elif key in CONFIRM_KEYS:
            if self.menu_idx == self.MENU_FIGHT:
                self.state = self.STATE_MOVE_SELECT
                self.move_idx = 0
            elif self.menu_idx == self.MENU_ITEM:
                if self.inventory and self.inventory.get_all_items():
                    self.state = self.STATE_ITEM_SELECT
                    self.item_idx = 0
                else:
                    self.msg = "No items available!"
            elif self.menu_idx == self.MENU_FLEE:
                if self.is_trainer_battle:
                    self.msg = "You can't flee from a trainer battle!"
                    self.state = self.STATE_MENU
                else:
                    self._say("You fled!")
                    self.battle_over = True
            elif self.menu_idx == self.MENU_SWITCH:
                self._switch_party()

    def _handle_move_select(self, key):
        # Check if current mascot is fainted
        if self.party_states[self.active_idx].get("fainted", False):
            self.state = self.STATE_MENU
            return

        if key in GRID_STEPS:
            self.move_idx = self._grid_move(self.move_idx, key, len(self.player.moves))
        elif key in CONFIRM_KEYS:
            self._player_attack(self.move_idx)
            # Only return to menu if not in forced switch (player fainted)
            if self.state != self.STATE_PARTY_SELECT:
                self.state = self.STATE_MENU
        elif key == pygame.K_x:
            self.state = self.STATE_MENU

    def _handle_item_select(self, key):
        items = self.inventory.get_all_items()
        if key == pygame.K_UP:
            self.item_idx = (self.item_idx - 1) % len(items)
        elif key == pygame.K_DOWN:
            self.item_idx = (self.item_idx + 1) % len(items)
        elif key in CONFIRM_KEYS:
            self._use_item(self.item_idx)
        elif key == pygame.K_x:
            self.state = self.STATE_MENU

    def _handle_party_select(self, key):
        available = self._get_selectable_party_indices()
        if not available:
            # Nothing selectable (shouldn't happen): back out
            if not self.forced_switch:
                self.pending_item = None
                self.state = self.STATE_MENU
            return

        if key in (pygame.K_UP, pygame.K_DOWN):
            current_pos = (
                available.index(self.party_select_idx)
                if self.party_select_idx in available
                else 0
            )
            step = -1 if key == pygame.K_UP else 1
            self.party_select_idx = available[(current_pos + step) % len(available)]
        elif key in CONFIRM_KEYS:
            if self.party_select_idx not in available:
                return
            if self.pending_item is not None:
                self._use_item_on(self.party_select_idx)
            else:
                self._execute_switch(self.party_select_idx)
                # If not forced, opponent gets a free attack
                if not self.forced_switch:
                    self._opponent_attack()
                self.forced_switch = False
        elif key == pygame.K_x:
            # Can only cancel if not forced
            if not self.forced_switch:
                self.pending_item = None
                self.state = self.STATE_MENU

    def _switch_party(self):
        """Open party selection menu for voluntary switching."""
        self.pending_item = None
        candidates = self._get_selectable_party_indices()
        if candidates:
            self.party_select_idx = candidates[0]
            self.forced_switch = False
            self.state = self.STATE_PARTY_SELECT
        else:
            self.msg = "No other mascots available!"

    def _player_attack(self, move_idx):
        # Don't allow fainted mascots to attack
        if self.party_states[self.active_idx].get("fainted", False):
            self.msg = f"{self.player.name} is unable to battle!"
            return

        move = self.player.moves[move_idx]
        # Faster mascot moves first; ties go to the player
        if self.player.spd < self.opponent.spd:
            self._opponent_attack()
            if self.player.hp <= 0:
                return
            self._attack(self.player, self.opponent, move)
            if self.opponent.hp <= 0:
                self._on_opponent_fainted()
        else:
            self._attack(self.player, self.opponent, move)
            if self.opponent.hp <= 0:
                self._on_opponent_fainted()
            else:
                self._opponent_attack()

    def _on_opponent_fainted(self):
        self._say(f"{self.opponent.name} fainted!", "faint")
        self._award_xp(self.opponent)
        next_opponent = next((m for m in self.opponent_party if m.hp > 0), None)
        if next_opponent is None:
            if self.is_trainer_battle:
                self._say("You defeated the trainer!")
            self.battle_over = True
        else:
            self.opponent = next_opponent
            self._participants = {self.active_idx}
            self._say(f"Trainer sent out {self.opponent.name}!")

    def _award_xp(self, defeated):
        """Share the defeated mascot's XP among the mascots that fought it."""
        total = mascots.xp_yield(defeated.name, defeated.level, self.is_trainer_battle)
        winners = [
            i
            for i in sorted(self._participants)
            if not self.party_states[i].get("fainted", False)
        ]
        if not winners:
            return
        share = max(1, total // len(winners))
        for i in winners:
            mascot = self.party[i]
            self._say(f"{mascot.name} gained {share} XP!")
            self._gain_xp(mascot, share)

    def _gain_xp(self, mascot, amount):
        """Add XP, applying every level-up it pays for (narrated)."""
        mascot.xp += amount
        while mascot.level < mascots.MAX_LEVEL:
            need = mascots.xp_to_next(mascot.level)
            if mascot.xp < need:
                break
            mascot.xp -= need
            self._level_up(mascot)
        if mascot.level >= mascots.MAX_LEVEL:
            mascot.xp = 0

    def _level_up(self, mascot):
        mascot.level += 1
        stats = mascots.stats_at(mascot.name, mascot.level)
        gained = stats["hp"] - mascot.max_hp
        mascot.max_hp = stats["hp"]
        if mascot.hp > 0:
            mascot.hp = min(mascot.max_hp, mascot.hp + max(0, gained))
        mascot.atk = stats["atk"]
        mascot.defense = stats["defense"]
        mascot.spd = stats["spd"]
        self._say(f"{mascot.name} grew to level {mascot.level}!", "levelup")
        for move in mascots.moves_learned_at(mascot.name, mascot.level):
            if any(m.name == move["name"] for m in mascot.moves):
                continue
            new = Move(move["name"], move["power"], move["type"])
            if len(mascot.moves) >= mascots.MAX_MOVES:
                old = mascot.moves.pop(0)
                self._say(f"{mascot.name} forgot {old.name}!")
            mascot.moves.append(new)
            self._say(f"{mascot.name} learned {new.name}!")

    def _opponent_attack(self):
        move = random.choice(self.opponent.moves)
        self._attack(self.opponent, self.player, move)
        if self.player.hp <= 0:
            self.party_states[self.active_idx]["fainted"] = True
            self._say(f"{self.player.name} fainted!", "faint")

            # Check if all party members have fainted
            if self._check_all_fainted():
                self._say("You have no mascots left to battle!")
                self.battle_over = True
            else:
                # Trigger forced switch to another mascot
                available = self._get_available_party_indices()
                self.party_select_idx = available[0]
                self.forced_switch = True
                self.state = self.STATE_PARTY_SELECT

    def _use_item(self, item_idx):
        """Use an item from inventory during battle."""
        items = self.inventory.get_all_items()
        if item_idx >= len(items):
            return

        item, _quantity = items[item_idx]

        # Handle packages (capture)
        if item.type == item.TYPE_PACKAGE:
            self._try_capture()
            return

        # Consumables (healing, revive) need a target: pick one from the party
        if item.type == item.TYPE_CONSUMABLE:
            self.pending_item = item
            self.forced_switch = False
            targets = self._get_selectable_party_indices()
            if not targets:
                self.msg = f"{item.name} would have no effect!"
                self.pending_item = None
                self.state = self.STATE_MENU
                return
            self.party_select_idx = targets[0]
            self.state = self.STATE_PARTY_SELECT
            return

        # Key items can't be used in battle
        self.msg = "Can't use that here!"
        self.state = self.STATE_MENU

    def _use_item_on(self, idx):
        """Apply the pending consumable to party member idx."""
        item = self.pending_item
        self.pending_item = None
        target = self.party[idx]
        self.state = self.STATE_MENU
        if not self.inventory.use_item(item.id, target):
            self.msg = f"{item.name} had no effect!"
            return
        if "revive" in item.effect:
            self.party_states[idx]["fainted"] = False
            self._say(f"{target.name} was revived!")
        else:
            self._say(f"Used {item.name} on {target.name}!")
        self._opponent_attack()

    def _try_capture(self):
        """Attempt to capture wild mascot using a package."""
        self.state = self.STATE_MENU
        # Cannot capture trainer's mascots
        if self.is_trainer_battle:
            self.msg = "You can't capture a trainer's mascot!"
            return

        # Check if player has packages
        if not self.inventory or not self.inventory.has_item("package"):
            self.msg = "No packages available!"
            return

        if len(self.party) >= PARTY_MAX:
            self.msg = "Your party is full!"
            return

        # Consume a package
        self.inventory.remove_item("package")

        # Simple probability: higher if opponent HP is low
        prob = max(0.2, 1.0 - self.opponent.hp / self.opponent.max_hp)
        if random.random() < prob:
            self._say(f"You captured {self.opponent.name}!", "capture")
            self.captured = True

            # The captured mascot joins at full HP, not with its battle damage
            captured_state = self.make_mascot_state(
                self.opponent.name, level=self.opponent.level
            )
            self.party.append(self.hydrate_mascot(captured_state))
            self.party_states.append(captured_state)

            # Persist captured mascot name on the manager for the overworld
            self.manager.captured_mascot_name = self.opponent.name
            self.battle_over = True
        else:
            self._say("Capture failed!")
            self._opponent_attack()

    def update(self, dt):
        self._clock += dt
        self._effect_t += dt
        if self.messages and not self._text_done():
            self._text_pos += TEXT_CPS * dt

    # --- Drawing ---

    def _draw_box(self, surface, rect, width=1):
        pygame.draw.rect(surface, GB_PALETTE[1], rect)
        pygame.draw.rect(surface, GB_PALETTE[3], rect, width)

    def _draw_info(self, surface, mascot, hp, x, y):
        """Name, type, HP bar and HP numbers for one side."""
        font = get_font(12)
        small = get_font(10)
        surface.blit(font.render(mascot.name, True, GB_PALETTE[3]), (x, y))
        surface.blit(
            small.render(f"[{mascot.type}] Lv{mascot.level}", True, GB_PALETTE[2]),
            (x, y + LINE_H),
        )
        bar_w, bar_h = 64, 6
        bar_y = y + 2 * LINE_H + 2
        fill = int((bar_w - 2) * hp / mascot.max_hp) if mascot.max_hp else 0
        pygame.draw.rect(surface, GB_PALETTE[3], (x, bar_y, bar_w, bar_h), 1)
        if fill > 0:
            pygame.draw.rect(
                surface, GB_PALETTE[2], (x + 1, bar_y + 1, fill, bar_h - 2)
            )
        hp_text = small.render(f"{hp}/{mascot.max_hp}", True, GB_PALETTE[3])
        surface.blit(hp_text, (x + bar_w + 4, bar_y - 3))

    def _draw_grid(self, surface, labels, selected, x, y, col_w):
        """Two-column menu with a '>' cursor."""
        font = get_font(12)
        for i, label in enumerate(labels):
            lx = x + (i % 2) * col_w
            ly = y + (i // 2) * LINE_H * 1.5
            color = GB_PALETTE[3] if i == selected else GB_PALETTE[2]
            if i == selected:
                surface.blit(font.render(">", True, GB_PALETTE[3]), (lx, ly))
            surface.blit(font.render(label, True, color), (lx + 10, ly))

    def _draw_text_lines(self, surface, text, x, y, width, reveal=None):
        """Draw wrapped text; `reveal` limits how many characters show."""
        font = get_font(12)
        for i, line in enumerate(wrap_text(font, text, width)[:3]):
            if reveal is not None:
                line = line[: max(0, reveal)]
                reveal -= len(line) + 1  # wrapping swallowed a space
            surface.blit(font.render(line, True, GB_PALETTE[3]), (x, y + i * LINE_H))

    def _draw_prompt(self, surface):
        """Blinking down-arrow at the box corner: a message waits for Z."""
        if int(self._clock / PROMPT_BLINK) % 2:
            return
        x, y = SCREEN_WIDTH - 14, SCREEN_HEIGHT - 10
        pygame.draw.polygon(
            surface, GB_PALETTE[3], [(x, y), (x + 6, y), (x + 3, y + 4)]
        )

    def _sprite_offset(self, view, side):
        """(dx, dy, visible) for a sprite while a hit effect plays on it."""
        if self.state != self.STATE_MESSAGE or view.effect != side:
            return 0, 0, True
        if self._effect_t >= EFFECT_TIME:
            return 0, 0, True
        phase = int(self._effect_t / 0.05)
        return (2 if phase % 2 else -2), 0, phase % 3 != 2

    def draw(self, surface):
        menu_font = msg_font = get_font(12)

        # While narrating, show the HP/mascots as of the current message
        if self.state == self.STATE_MESSAGE and self.messages:
            view = self.messages[0]
        else:
            view = BattleMessage(
                "", self.player, self.player.hp, self.opponent, self.opponent.hp
            )

        surface.fill(GB_PALETTE[0])
        # Opponent: info top-left, sprite top-right
        self._draw_info(surface, view.opponent, view.opponent_hp, 8, 4)
        dx, dy, visible = self._sprite_offset(view, HIT_OPPONENT)
        if view.opponent_hp > 0 and visible:
            sprite = mascots.get_sprite(view.opponent.name, SPRITE_SCALE)
            surface.blit(sprite, (160 + dx, 4 + dy))
        # Player: sprite bottom-left, info on the right
        dx, dy, visible = self._sprite_offset(view, HIT_PLAYER)
        if view.player_hp > 0 and visible:
            sprite = mascots.get_sprite(view.player.name, SPRITE_SCALE)
            surface.blit(sprite, (16 + dx, 46 + dy))
        self._draw_info(surface, view.player, view.player_hp, 120, 62)

        box = (0, BOX_Y, SCREEN_WIDTH, BOX_H)
        if self.state == self.STATE_MESSAGE:
            self._draw_box(surface, box)
            reveal = None if TEXT_CPS <= 0 else int(self._text_pos)
            self._draw_text_lines(
                surface, view.text, 8, BOX_Y + 4, SCREEN_WIDTH - 16, reveal
            )
            if self._text_done():
                self._draw_prompt(surface)
        elif self.state == self.STATE_MENU:
            self._draw_box(surface, box)
            status = self._status or f"What will {self.player.name} do?"
            self._draw_text_lines(surface, status, 8, BOX_Y + 4, 104)
            self._draw_box(surface, (120, BOX_Y, SCREEN_WIDTH - 120, BOX_H))
            self._draw_grid(surface, self.menu_names, self.menu_idx, 124, BOX_Y + 6, 58)
        elif self.state == self.STATE_MOVE_SELECT:
            moves = self.player.moves
            self._draw_box(surface, (0, BOX_Y, 160, BOX_H))
            self._draw_grid(
                surface, [m.name for m in moves], self.move_idx, 4, BOX_Y + 6, 78
            )
            # Selected move's details
            move = moves[self.move_idx]
            self._draw_box(surface, (160, BOX_Y, SCREEN_WIDTH - 160, BOX_H))
            surface.blit(
                menu_font.render(f"PWR {move.power}", True, GB_PALETTE[3]),
                (166, BOX_Y + 6),
            )
            surface.blit(
                menu_font.render(move.type, True, GB_PALETTE[3]),
                (166, BOX_Y + 6 + LINE_H * 1.5),
            )
        elif self.state == self.STATE_ITEM_SELECT:
            self._draw_box(surface, box)
            items = self.inventory.get_all_items() if self.inventory else []
            # Show a 3-row window that scrolls with the cursor
            first = min(max(0, self.item_idx - 1), max(0, len(items) - 3))
            for row, (item, quantity) in enumerate(items[first : first + 3]):
                i = first + row
                y = BOX_Y + 4 + row * LINE_H
                color = GB_PALETTE[3] if i == self.item_idx else GB_PALETTE[2]
                if i == self.item_idx:
                    surface.blit(menu_font.render(">", True, GB_PALETTE[3]), (8, y))
                surface.blit(menu_font.render(item.name, True, color), (18, y))
                qty = menu_font.render(f"x{quantity}", True, color)
                surface.blit(qty, (SCREEN_WIDTH - 12 - qty.get_width(), y))
        elif self.state == self.STATE_PARTY_SELECT:
            self._draw_party_select(surface, menu_font, msg_font)

    def _draw_party_select(self, surface, menu_font, msg_font):
        # Draw party selection menu - Pokemon Red/Blue style full-screen overlay
        # Semi-transparent background (draw pattern for GB aesthetic)
        for y in range(0, SCREEN_HEIGHT, 2):
            pygame.draw.line(surface, GB_PALETTE[2], (0, y), (SCREEN_WIDTH, y))

        if self.pending_item is not None:
            prompt = f"Use {self.pending_item.name} on:"
        elif self.forced_switch:
            prompt = "Choose next mascot!"
        else:
            prompt = "Switch to:"
        selectable = self._get_selectable_party_indices()

        # Calculate menu dimensions
        menu_item_height = 16  # Reduced from 18 for compactness
        menu_padding = 8
        menu_width = SCREEN_WIDTH - 16
        menu_x = 8

        # Start higher on screen to fit more mascots
        menu_y = 30
        header_height = 18
        footer_height = 14
        party_list_height = len(self.party) * menu_item_height
        menu_height = (
            header_height + party_list_height + footer_height + menu_padding * 2
        )

        # Draw main menu box
        pygame.draw.rect(
            surface, GB_PALETTE[1], (menu_x, menu_y, menu_width, menu_height)
        )
        pygame.draw.rect(
            surface, GB_PALETTE[3], (menu_x, menu_y, menu_width, menu_height), 2
        )

        # Draw prompt/header
        text = msg_font.render(prompt, True, GB_PALETTE[3])
        surface.blit(text, (menu_x + menu_padding, menu_y + menu_padding))

        # Draw party members
        list_start_y = menu_y + header_height + menu_padding
        for i, mascot in enumerate(self.party):
            y_offset = list_start_y + i * menu_item_height
            is_fainted = self.party_states[i].get("fainted", False)
            # The active mascot is only off-limits when switching
            is_active = i == self.active_idx and self.pending_item is None
            is_selected = i == self.party_select_idx and i in selectable

            # Determine color based on state
            if is_fainted:
                color = GB_PALETTE[3] if is_selected else GB_PALETTE[2]
                status = "FNT"
            elif is_active:
                color = GB_PALETTE[2]  # Can't switch to active
                status = "ACT"
            elif is_selected:
                color = GB_PALETTE[3]  # Highlighted
                status = ""
            else:
                color = GB_PALETTE[2]  # Normal
                status = ""

            # Draw cursor for selected
            if is_selected:
                cursor_text = menu_font.render(">", True, GB_PALETTE[3])
                surface.blit(cursor_text, (menu_x + menu_padding, y_offset))

            # Draw name (shortened to fit better)
            name_x = menu_x + menu_padding + 12
            name_text = menu_font.render(
                f"{mascot.name[:10]} L{mascot.level}", True, color
            )  # Truncate long names
            surface.blit(name_text, (name_x, y_offset))

            # Draw HP bar or status
            bar_x = menu_x + 110
            if is_fainted or is_active:
                status_text = menu_font.render(status, True, color)
                surface.blit(status_text, (bar_x, y_offset))
            else:
                # Draw compact HP bar
                bar_width = 50
                bar_height = 6
                hp_ratio = mascot.hp / mascot.max_hp if mascot.max_hp > 0 else 0

                # HP bar outline, then fill (same style as the main HP bars)
                pygame.draw.rect(
                    surface,
                    GB_PALETTE[3],
                    (bar_x, y_offset + 4, bar_width, bar_height),
                    1,
                )
                fill_width = int((bar_width - 2) * hp_ratio)
                if fill_width > 0:
                    pygame.draw.rect(
                        surface,
                        GB_PALETTE[2],
                        (bar_x + 1, y_offset + 5, fill_width, bar_height - 2),
                    )

                # HP text
                hp_text = menu_font.render(f"{mascot.hp}/{mascot.max_hp}", True, color)
                surface.blit(hp_text, (bar_x + bar_width + 4, y_offset))

        # Draw controls hint at bottom
        footer_y = list_start_y + party_list_height + 4
        cancel_text = "" if self.forced_switch else " X:Back"
        hint = f"Z/Enter:OK{cancel_text}"
        text = msg_font.render(hint, True, GB_PALETTE[3])
        surface.blit(text, (menu_x + menu_padding, footer_y))
