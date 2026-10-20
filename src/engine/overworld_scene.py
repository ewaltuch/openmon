"""
OverworldScene implementation for Open-Mon.
"""

import random

import pygame
from PIL import Image, ImageDraw

from src.constants import DEFAULT_MAP, GB_PALETTE, SCREEN_HEIGHT, SCREEN_WIDTH
from src.overworld import (
    GRASS,
    KEY_DIRECTIONS,
    TILE_SIZE,
    Player,
    load_overworld_sprite,
    load_player_images,
)

from . import audio, mascots
from .fonts import get_font, wrap_text
from .inventory import STARTING_MONEY
from .maps import load_map, map_exists
from .save import SaveManager

INTERACT_KEYS = (pygame.K_SPACE, pygame.K_z, pygame.K_RETURN, pygame.K_KP_ENTER)
FADE_TIME = 0.25  # seconds for each half (fade out, then fade in) of a warp


class OverworldScene:
    SPAWN_TILE = (2, 2)

    def npc_at(self, tx, ty):
        """The NPC standing on tile (tx, ty), if any."""
        for npc in self.npcs:
            if (npc.x, npc.y) == (tx, ty):
                return npc
        return None

    def npc_collides(self, x, y):
        # Check if the tile at pixel (x, y) is occupied by an NPC
        return self.npc_at(int(x // TILE_SIZE), int(y // TILE_SIZE)) is not None

    def __init__(self, manager, inventory=None):
        self.manager = manager
        audio.play_music("overworld")
        self.tile_images = self._generate_tiles()
        # Defeated trainers, keyed "map_id:npc_id" so they stay correct across maps
        self.defeated_trainers = {}
        self.fade = None  # {"phase": "out"|"in", "t": seconds, "warp": Warp}
        self.map = None
        self._maps = {}
        # Initialize party as state dictionaries
        self.party = self._initialize_party(["Tux", "BSD Daemon"])
        self.player = Player(
            0,
            0,
            load_player_images() or [self._generate_player_sprite()],
        )
        self.camera_x = 0
        self.camera_y = 0
        self.steps = 0
        self.encounter_steps = random.randint(10, 20)
        self._pending_trainer = None
        self.active_dialogue = None
        self.active_npc = None
        self.npcs = []
        self.enter_map(DEFAULT_MAP)
        # Inventory system
        from src.engine.inventory import InventoryManager

        self.inventory = inventory or InventoryManager()
        # Give player starting items
        if not inventory:
            self.inventory.add_item("package", 5)
            self.inventory.add_item("health_pack", 3)

        self.is_paused = False
        self.pause_menu_idx = 0
        self.pause_menu_options = [
            "Continue",
            "Mascots",
            "Bag",
            "Save",
            "Load",
            "Toggle Hints",
            "Quit",
        ]

        self.notification_text = None
        self.notification_timer = 0

        self.show_controls_hint = True

    def enter_map(self, map_id, tx=None, ty=None, facing=None):
        """Switch to a map immediately and place the player (default: its spawn)."""
        if self.map is not None:
            self._sync_defeated()  # remember the map being left
        if map_id not in self._maps:  # keep NPC objects stable per scene
            self._maps[map_id] = load_map(map_id)
        self.map = self._maps[map_id]
        self.tilemap = self.map.tilemap
        self.npcs = self.map.npcs
        for npc in self.npcs:
            if npc.trainer:
                npc.defeated = bool(self.defeated_trainers.get(f"{map_id}:{npc.id}"))
        if tx is None:
            tx, ty = self.map.spawn
        self.player.place(tx, ty)
        if facing:
            self.player.facing = facing
        self.active_dialogue = None
        self.active_npc = None
        self.steps = 0
        self._update_camera()

    def start_warp(self, warp):
        """Begin the fade-out that carries the player through a warp."""
        self.fade = {"phase": "out", "t": 0.0, "warp": warp}

    def _update_fade(self, dt):
        fade = self.fade
        fade["t"] += dt
        if fade["t"] < FADE_TIME:
            return
        if fade["phase"] == "out":
            w = fade["warp"]
            self._sync_defeated()
            self.enter_map(w.to, w.tx, w.ty, w.facing)
            self.fade = {"phase": "in", "t": 0.0, "warp": w}
        else:
            self.fade = None

    def _fade_alpha(self):
        if not self.fade:
            return 0
        ratio = min(1.0, self.fade["t"] / FADE_TIME)
        return int(255 * (ratio if self.fade["phase"] == "out" else 1 - ratio))

    def _update_camera(self):
        """Camera follows the player, bounded to the map."""
        map_w = self.tilemap.width * TILE_SIZE
        map_h = self.tilemap.height * TILE_SIZE
        self.camera_x = max(
            0, min(self.player.x - SCREEN_WIDTH // 2, map_w - SCREEN_WIDTH)
        )
        self.camera_y = max(
            0, min(self.player.y - SCREEN_HEIGHT // 2, map_h - SCREEN_HEIGHT)
        )

    def _sync_defeated(self):
        """Record the current map's trainers in defeated_trainers."""
        for npc in self.npcs:
            if npc.trainer:
                key = f"{self.map.id}:{npc.id}"
                if npc.defeated:
                    self.defeated_trainers[key] = True
                else:
                    self.defeated_trainers.pop(key, None)

    def _generate_tiles(self):
        # 0 = floor, 1 = wall, 2 = tall grass
        tiles = []
        # Floor
        img = Image.new("RGB", (TILE_SIZE, TILE_SIZE), GB_PALETTE[0])
        tiles.append(pygame.image.fromstring(img.tobytes(), img.size, img.mode))
        # Wall
        img = Image.new("RGB", (TILE_SIZE, TILE_SIZE), GB_PALETTE[1])
        draw = ImageDraw.Draw(img)
        draw.rectangle([2, 2, 5, 5], fill=GB_PALETTE[3])
        tiles.append(pygame.image.fromstring(img.tobytes(), img.size, img.mode))
        # Tall grass
        img = Image.new("RGB", (TILE_SIZE, TILE_SIZE), GB_PALETTE[2])
        draw = ImageDraw.Draw(img)
        for i in range(3):
            draw.line([1, 2 + i, 6, 2 + i], fill=GB_PALETTE[3], width=1)
        tiles.append(pygame.image.fromstring(img.tobytes(), img.size, img.mode))
        return tiles

    def _generate_player_sprite(self):
        # Simple 8x8 Tux placeholder
        img = Image.new("RGB", (TILE_SIZE, TILE_SIZE), GB_PALETTE[0])
        draw = ImageDraw.Draw(img)
        draw.ellipse([2, 2, 6, 6], fill=GB_PALETTE[2])
        draw.rectangle([3, 5, 4, 7], fill=GB_PALETTE[3])
        return pygame.image.fromstring(img.tobytes(), img.size, img.mode)

    def _initialize_party(self, names):
        """Initialize party from list of names, creating fresh states with full HP."""
        return [mascots.make_state(name) for name in names]

    def heal_party(self):
        """Restore every party mascot to full HP."""
        for state in self.party:
            state["hp"] = state["max_hp"]
            state["fainted"] = False
        self.notification_text = "Your mascots are fully healed!"
        self.notification_timer = 2

    def draw_hud(self, surface):
        """Draw the HUD with party status."""
        if not self.party:
            return

        # Get active mascot (first non-fainted)
        active = None
        for state in self.party:
            if not state.get("fainted", False):
                active = state
                break

        if not active:
            return

        # Use a pixel font for crisp text if available, else fallback
        font = get_font(10)

        # HUD box in top-right
        hud_x = SCREEN_WIDTH - 80
        hud_y = 4
        hud_w = 76
        hud_h = 40

        pygame.draw.rect(surface, GB_PALETTE[1], (hud_x, hud_y, hud_w, hud_h))
        pygame.draw.rect(surface, GB_PALETTE[3], (hud_x, hud_y, hud_w, hud_h), 1)

        # Draw name and type
        name_text = font.render(
            f"{active['name']} Lv{active.get('level', 5)}", True, GB_PALETTE[3]
        )
        surface.blit(name_text, (hud_x + 4, hud_y + 2))

        # Draw HP
        hp_text = font.render(
            f"HP: {active['hp']}/{active['max_hp']}", True, GB_PALETTE[3]
        )
        surface.blit(hp_text, (hud_x + 4, hud_y + 12))

        # HP bar
        bar_w = 68
        bar_h = 6
        hp_ratio = active["hp"] / active["max_hp"]

        bar_x = hud_x + 4
        bar_y = hud_y + 22

        money = font.render(f"${self.inventory.money}", True, GB_PALETTE[3])
        surface.blit(money, (hud_x + 4, hud_y + 29))

        # Draw the background of the HP bar
        pygame.draw.rect(surface, GB_PALETTE[3], (bar_x, bar_y, bar_w, bar_h), 1)

        # Draw the filled portion of the HP bar
        fill_width = int((bar_w - 2) * hp_ratio)
        if fill_width > 0:
            pygame.draw.rect(
                surface, GB_PALETTE[2], (bar_x + 1, bar_y + 1, fill_width, bar_h - 2)
            )

    def draw_pause_menu(self, surface):
        """Draw the pause menu overlay."""
        # Semi-transparent overlay using a solid color with alpha
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Black with 50% transparency
        surface.blit(overlay, (0, 0))

        # Menu box
        menu_w = 120
        menu_h = 20 + len(self.pause_menu_options) * 16
        menu_x = SCREEN_WIDTH // 2 - menu_w // 2
        menu_y = SCREEN_HEIGHT // 2 - menu_h // 2

        pygame.draw.rect(surface, GB_PALETTE[1], (menu_x, menu_y, menu_w, menu_h))
        pygame.draw.rect(surface, GB_PALETTE[3], (menu_x, menu_y, menu_w, menu_h), 2)

        # Menu items
        font = get_font(12)

        for i, item in enumerate(self.pause_menu_options):
            color = GB_PALETTE[3] if i == self.pause_menu_idx else GB_PALETTE[2]

            # Add a cursor to the selected item
            display_text = f"> {item}" if i == self.pause_menu_idx else item

            text = font.render(display_text, True, color)

            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, menu_y + 15 + i * 16))
            surface.blit(text, text_rect)

    def draw_notification(self, surface):
        """Draw the notification message box."""
        if self.notification_text:
            font = get_font(12)

            text_surf = font.render(self.notification_text, True, GB_PALETTE[3])
            text_rect = text_surf.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20)
            )

            box_rect = text_rect.inflate(20, 10)
            pygame.draw.rect(surface, GB_PALETTE[1], box_rect)
            pygame.draw.rect(surface, GB_PALETTE[3], box_rect, 1)

            surface.blit(text_surf, text_rect)

    def _save_game(self):
        """Save game state with notification."""
        self._sync_defeated()

        SaveManager.save(
            {
                "map": self.map.id,
                "player": {"x": self.player.x, "y": self.player.y},
                "party": self.party,
                "inventory": self.inventory.to_dict(),
                "money": self.inventory.money,
                "defeated_npcs": dict(self.defeated_trainers),
                "muted": audio.muted,
            }
        )
        self.notification_text = "Game saved!"
        self.notification_timer = 2

    def _load_game(self):
        """Load game state with notification."""
        data = SaveManager.load()
        if data:
            # Snap to the grid (older saves stored free-movement pixel positions)
            tx = round(data["player"]["x"] / TILE_SIZE)
            ty = round(data["player"]["y"] / TILE_SIZE)
            # Defeated trainers: "map:npc" keys; old saves had bare npc ids
            # from the single (default) map
            self.defeated_trainers = {}
            for key in data.get("defeated_npcs", {}):
                if ":" not in key:
                    key = f"{DEFAULT_MAP}:{key}"
                self.defeated_trainers[key] = True
            # Old saves have no map: they were made on the default one
            map_id = data.get("map", DEFAULT_MAP)
            if not map_exists(map_id):
                map_id = DEFAULT_MAP
                tx = None
            self.fade = None
            self.map = None  # nothing to sync: the save is the truth
            self.enter_map(map_id)
            if tx is not None and (
                not self.tilemap.is_walkable(tx, ty) or self.npc_at(tx, ty)
            ):
                tx = None
            if tx is None:
                tx, ty = self.map.spawn
            self.player.place(tx, ty)
            self._update_camera()

            # Load party - handle both old format (list of strings) and new format (list of dicts)
            party_data = data.get("party", ["Tux"])
            if party_data and isinstance(party_data[0], str):
                # Old format - migrate to new format
                self.party = self._initialize_party(party_data)
            else:
                # New format - validate and use
                self.party = party_data
                # Validate party states have required keys
                for state in self.party:
                    if state.get("name") not in mascots.SPECIES or not all(
                        k in state
                        for k in [
                            "name",
                            "hp",
                            "max_hp",
                            "atk",
                            "defense",
                            "spd",
                            "type",
                        ]
                    ):
                        # Invalid state, reinitialize
                        self.party = self._initialize_party(["Tux"])
                        break

            for state in self.party:
                mascots.normalize_state(state)  # old saves: level 5, xp 0

            audio.set_muted(data.get("muted", False))

            if "inventory" in data:
                self.inventory.from_dict(data["inventory"])
            # Old saves have no money: start from the default amount
            self.inventory.money = data.get("money", STARTING_MONEY)

            self._pending_trainer = None

            # Ensure game is not paused after loading
            self.is_paused = False

            self.notification_text = "Game loaded!"
            self.notification_timer = 2
        else:
            self.notification_text = "No save file found!"
            self.notification_timer = 2

    def draw_control_hints(self, surface):
        """Draw the control hints at the bottom of the screen."""
        if self.show_controls_hint and not self.active_dialogue:
            font = get_font(12)

            hint_text = "Arrows:Move  Z:Talk  S:Save  L:Load  Esc:Menu"
            text_surf = font.render(hint_text, True, GB_PALETTE[3])
            text_rect = text_surf.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 8)
            )
            surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.is_paused = not self.is_paused
            return

        if self.is_paused:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.pause_menu_idx = (self.pause_menu_idx - 1) % len(
                        self.pause_menu_options
                    )
                elif event.key == pygame.K_DOWN:
                    self.pause_menu_idx = (self.pause_menu_idx + 1) % len(
                        self.pause_menu_options
                    )
                elif event.key in (pygame.K_z, pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._execute_pause_action()
                elif event.key == pygame.K_x:
                    self.is_paused = False
            return

        if event.type == pygame.KEYDOWN and not self.active_dialogue:
            if event.key == pygame.K_m:
                audio.toggle_mute()
            elif event.key == pygame.K_s:
                self._save_game()
            elif event.key == pygame.K_l:
                self._load_game()
        # Interact with NPCs (Space/Z)
        if event.type == pygame.KEYDOWN and event.key in INTERACT_KEYS:
            if self.active_dialogue and self.active_npc:
                # Advance dialogue with the current NPC
                next_line = self.active_npc.talk()
                if next_line:
                    self.active_dialogue = next_line
                else:
                    # No more dialogue, check if this is a trainer battle
                    if self.active_npc.is_trainer():
                        # Start trainer battle
                        from .battle_scene import BattleScene

                        # Create trainer party states and hydrate to Mascot objects
                        trainer_party = [
                            mascots.make_mascot(*mascots.parse_party_entry(entry))
                            for entry in self.active_npc.party
                        ]
                        battle = BattleScene(
                            self.manager,
                            party_states=self.party,
                            inventory=self.inventory,
                            opponent_party=trainer_party,
                            is_trainer_battle=True,
                            reward=self.active_npc.reward,
                        )
                        self.manager.push(battle)
                        # Marked defeated on return, and only if the player won
                        self._pending_trainer = self.active_npc
                    elif self.active_npc.heals:
                        self.heal_party()
                    elif self.active_npc.shop:
                        from .menu_screens import ShopScreen

                        self.manager.push(
                            ShopScreen(
                                self.manager, self.inventory, self.active_npc.stock
                            )
                        )
                    # Close the dialogue box
                    self.active_dialogue = None
                    self.active_npc = None
            elif not self.player.moving:
                # Talk to the NPC the player is facing
                npc = self.npc_at(*self.player.facing_tile())
                if npc:
                    self.active_npc = npc
                    self.active_dialogue = npc.talk()

    def _execute_pause_action(self):
        """Execute selected pause menu action."""
        selected_option = self.pause_menu_options[self.pause_menu_idx]
        if selected_option == "Continue":
            self.is_paused = False
        elif selected_option == "Mascots":
            from .menu_screens import PartyScreen

            self.manager.push(PartyScreen(self.manager, self.party))
        elif selected_option == "Bag":
            from .menu_screens import BagScreen

            self.manager.push(BagScreen(self.manager, self.party, self.inventory))
        elif selected_option == "Save":
            self._save_game()
            self.is_paused = False
        elif selected_option == "Load":
            self._load_game()
            self.is_paused = False
        elif selected_option == "Toggle Hints":
            self.show_controls_hint = not self.show_controls_hint
            self.is_paused = False
        elif selected_option == "Quit":
            from .scenes import TitleScene

            self.manager.scenes = [TitleScene(self.manager)]

    def update(self, dt):
        if self.is_paused:
            return

        if self.notification_timer > 0:
            self.notification_timer -= dt
            if self.notification_timer <= 0:
                self.notification_text = None

        # Sync party HP from last battle
        battle_states = getattr(self.manager, "last_battle_party_states", None)
        if battle_states:
            self.party = battle_states
            delattr(self.manager, "last_battle_party_states")

            # Check if this was a battle loss - reset player to spawn
            if getattr(self.manager, "battle_loss_reset", False):
                self._sync_defeated()
                self.enter_map(DEFAULT_MAP, *self.SPAWN_TILE)
                delattr(self.manager, "battle_loss_reset")

            # A trainer only counts as defeated if the battle was won
            won = getattr(self.manager, "last_battle_won", False)
            if won:
                delattr(self.manager, "last_battle_won")
            reward = getattr(self.manager, "last_battle_reward", 0)
            if hasattr(self.manager, "last_battle_reward"):
                delattr(self.manager, "last_battle_reward")
            if won and reward:
                self.inventory.money += reward
                self.notification_text = f"Got ${reward}!"
                self.notification_timer = 2
            if self._pending_trainer is not None:
                if won:
                    self._pending_trainer.defeated = True
                    self._sync_defeated()
                self._pending_trainer = None

        # Check if a mascot was captured in the last battle and add to party
        captured_name = getattr(self.manager, "captured_mascot_name", None)
        if captured_name:
            # The synced battle party already includes the capture; only add it
            # when no party sync came with the flag
            if not battle_states:
                self.party.extend(self._initialize_party([captured_name]))
            # Clear the flag so we don't add it again
            delattr(self.manager, "captured_mascot_name")

        # Input is locked while the warp fade plays
        if self.fade:
            self._update_fade(dt)
            return

        # The player stands still while talking
        if self.active_dialogue:
            return

        # Grid movement: a held arrow key starts a one-tile step
        if not self.player.moving:
            keys = pygame.key.get_pressed()
            for key, direction in KEY_DIRECTIONS:
                if keys[key]:
                    self.player.try_step(
                        direction,
                        self.tilemap,
                        lambda tx, ty: self.npc_at(tx, ty) is not None,
                    )
                    break
        if self.player.update(dt):
            self._on_step_finished()

        self._update_camera()

    def _on_step_finished(self):
        """Take a warp if one is here, else roll an encounter on tall grass."""
        warp = self.map.warp_at(*self.player.tile)
        if warp:
            self.start_warp(warp)
            return
        if self.tilemap.tile_at(*self.player.tile) != GRASS:
            return
        if self.map.encounters is not None and not self.map.encounters:
            return  # an explicit empty table means no wild encounters here
        self.steps += 1
        if self.steps >= self.encounter_steps:
            from .battle_scene import BattleScene

            # Pass party states to battle
            self.manager.push(
                BattleScene(
                    self.manager,
                    party_states=self.party,
                    inventory=self.inventory,
                    wild_species=mascots.roll_wild_encounter(table=self.map.encounters),
                )
            )
            self.steps = 0
            self.encounter_steps = random.randint(10, 20)

    def draw(self, surface):
        self.tilemap.draw(surface, self.camera_x, self.camera_y, self.tile_images)
        self.player.draw(surface, self.camera_x, self.camera_y)
        for npc in self.npcs:
            px = npc.x * TILE_SIZE - self.camera_x
            py = npc.y * TILE_SIZE - self.camera_y
            image = load_overworld_sprite(npc.sprite)
            if image is not None:
                surface.blit(image, (px, py))
            else:  # No art for this sprite name: draw a circle
                pygame.draw.circle(
                    surface,
                    GB_PALETTE[2],
                    (px + TILE_SIZE // 2, py + TILE_SIZE // 2),
                    TILE_SIZE // 2,
                )
        # Draw dialogue box if active
        if self.active_dialogue:
            font = get_font(12)
            box_w = SCREEN_WIDTH - 16
            lines = wrap_text(font, self.active_dialogue, box_w - 16)
            box_h = 12 + 16 * len(lines)
            box_y = SCREEN_HEIGHT - box_h - 4
            pygame.draw.rect(surface, GB_PALETTE[1], (8, box_y, box_w, box_h))
            pygame.draw.rect(surface, GB_PALETTE[3], (8, box_y, box_w, box_h), 1)
            for i, line in enumerate(lines):
                text = font.render(line, True, GB_PALETTE[3])
                surface.blit(text, (16, box_y + 6 + i * 16))

        self.draw_hud(surface)
        self.draw_control_hints(surface)
        self.draw_notification(surface)

        alpha = self._fade_alpha()
        if alpha:
            veil = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            veil.fill(GB_PALETTE[3])
            veil.set_alpha(alpha)
            surface.blit(veil, (0, 0))

        if self.is_paused:
            self.draw_pause_menu(surface)
            return
