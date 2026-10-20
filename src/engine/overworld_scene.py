"""
OverworldScene implementation for Open-Mon.
"""

import os
import random

import pygame
from PIL import Image, ImageDraw

from src.constants import GB_PALETTE, SCREEN_HEIGHT, SCREEN_WIDTH, SPRITE_DIR
from src.overworld import (
    GRASS,
    KEY_DIRECTIONS,
    TILE_SIZE,
    Player,
    TileMap,
    load_overworld_sprite,
    load_player_images,
)

from . import audio, mascots
from .fonts import get_font, wrap_text
from .save import SaveManager

INTERACT_KEYS = (pygame.K_SPACE, pygame.K_z, pygame.K_RETURN, pygame.K_KP_ENTER)


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
        self.tilemap = TileMap(os.path.join(SPRITE_DIR, "tiles.csv"))
        # Initialize party as state dictionaries
        self.party = self._initialize_party(["Tux", "BSD Daemon"])
        sx, sy = self.SPAWN_TILE
        self.player = Player(
            sx * TILE_SIZE,
            sy * TILE_SIZE,
            load_player_images() or [self._generate_player_sprite()],
        )
        self.camera_x = 0
        self.camera_y = 0
        self.steps = 0
        self.encounter_steps = random.randint(10, 20)
        self._pending_trainer = None
        # Load NPCs
        from src.engine.npc import load_npcs

        self.npcs = load_npcs(
            os.path.join(os.path.dirname(__file__), "..", "..", "assets", "npcs.yaml")
        )
        self.active_dialogue = None
        self.active_npc = None
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
        hud_h = 30

        pygame.draw.rect(surface, GB_PALETTE[1], (hud_x, hud_y, hud_w, hud_h))
        pygame.draw.rect(surface, GB_PALETTE[3], (hud_x, hud_y, hud_w, hud_h), 1)

        # Draw name and type
        name_text = font.render(f"{active['name']}", True, GB_PALETTE[3])
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
        # Save defeated trainer states
        defeated_npcs = {}
        for npc in self.npcs:
            if npc.trainer and npc.defeated:
                defeated_npcs[npc.id] = True

        SaveManager.save(
            {
                "player": {"x": self.player.x, "y": self.player.y},
                "party": self.party,
                "inventory": self.inventory.to_dict(),
                "defeated_npcs": defeated_npcs,
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
            if not self.tilemap.is_walkable(tx, ty) or self.npc_at(tx, ty):
                tx, ty = self.SPAWN_TILE
            self.player.place(tx, ty)

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

            audio.set_muted(data.get("muted", False))

            if "inventory" in data:
                self.inventory.from_dict(data["inventory"])

            # Reset all trainers to undefeated, then restore from save
            for npc in self.npcs:
                if npc.trainer:
                    npc.defeated = False

            # Restore defeated trainer states from save file
            defeated_npcs = data.get("defeated_npcs", {})
            for npc in self.npcs:
                if npc.id in defeated_npcs:
                    npc.defeated = True

            # Clear dialogue state (NPCs are freshly loaded, old references are invalid)
            self.active_dialogue = None
            self.active_npc = None

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
                            mascots.make_mascot(name) for name in self.active_npc.party
                        ]
                        battle = BattleScene(
                            self.manager,
                            party_states=self.party,
                            inventory=self.inventory,
                            opponent_party=trainer_party,
                            is_trainer_battle=True,
                        )
                        self.manager.push(battle)
                        # Marked defeated on return, and only if the player won
                        self._pending_trainer = self.active_npc
                    elif self.active_npc.heals:
                        self.heal_party()
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
                self.player.place(*self.SPAWN_TILE)
                delattr(self.manager, "battle_loss_reset")

            # A trainer only counts as defeated if the battle was won
            won = getattr(self.manager, "last_battle_won", False)
            if won:
                delattr(self.manager, "last_battle_won")
            if self._pending_trainer is not None:
                if won:
                    self._pending_trainer.defeated = True
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

        # Camera follows player, bounded to the map
        map_w = self.tilemap.width * TILE_SIZE
        map_h = self.tilemap.height * TILE_SIZE
        self.camera_x = max(
            0, min(self.player.x - SCREEN_WIDTH // 2, map_w - SCREEN_WIDTH)
        )
        self.camera_y = max(
            0, min(self.player.y - SCREEN_HEIGHT // 2, map_h - SCREEN_HEIGHT)
        )

    def _on_step_finished(self):
        """Roll for an encounter each time the player enters a tall grass tile."""
        if self.tilemap.tile_at(*self.player.tile) != GRASS:
            return
        self.steps += 1
        if self.steps >= self.encounter_steps:
            from .battle_scene import BattleScene

            # Pass party states to battle
            self.manager.push(
                BattleScene(
                    self.manager, party_states=self.party, inventory=self.inventory
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

        if self.is_paused:
            self.draw_pause_menu(surface)
            return
