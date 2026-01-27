"""
OverworldScene implementation for Open-Mon.
"""

import os
import random

import pygame
from PIL import Image, ImageDraw

from src.constants import GB_PALETTE, SCREEN_HEIGHT, SCREEN_WIDTH, SPRITE_DIR
from src.overworld import MAP_HEIGHT, MAP_WIDTH, TILE_SIZE, Player, TileMap

from .save import SaveManager


class OverworldScene:
    def npc_collides(self, x, y):
        # Check if player's bounding box overlaps any NPC tile
        player_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        for npc in self.npcs:
            npc_rect = pygame.Rect(
                npc.x * TILE_SIZE, npc.y * TILE_SIZE, TILE_SIZE, TILE_SIZE
            )
            if player_rect.colliderect(npc_rect):
                return True
        return False

    def __init__(self, manager, inventory=None):
        self.manager = manager
        self.tile_images = self._generate_tiles()
        self.tilemap = TileMap(os.path.join(SPRITE_DIR, "tiles.csv"))
        # Initialize party as state dictionaries
        self.party = self._initialize_party(["Tux", "BSD Daemon"])
        self.player = Player(
            2 * TILE_SIZE, 2 * TILE_SIZE, [self._generate_player_sprite()]
        )
        self.camera_x = 0
        self.camera_y = 0
        self.steps = 0
        self.encounter_steps = random.randint(10, 20)
        self._pending_captured = None
        self._last_battle_captured_name = None
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
        self.pause_menu_options = ["Continue", "Save", "Load", "Toggle Hints", "Quit"]

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
        from .battle_scene import BattleScene

        bs = BattleScene(self.manager)
        return [bs.make_mascot_state(name) for name in names]

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
        font_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "assets", "sprites", "pixel.ttf"
        )
        if os.path.exists(font_path):
            font = pygame.font.Font(font_path, 10)
        else:
            font = pygame.font.SysFont("Arial", 10, bold=True)

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
        font_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "assets", "sprites", "pixel.ttf"
        )
        if os.path.exists(font_path):
            font = pygame.font.Font(font_path, 12)
        else:
            font = pygame.font.SysFont("Arial", 12, bold=True)

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
            font_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "assets", "sprites", "pixel.ttf"
            )
            if os.path.exists(font_path):
                font = pygame.font.Font(font_path, 12)
            else:
                font = pygame.font.SysFont("Arial", 12, bold=True)

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
            }
        )
        self.notification_text = "Game saved!"
        self.notification_timer = 2

    def _load_game(self):
        """Load game state with notification."""
        data = SaveManager.load()
        if data:
            self.player.x = data["player"]["x"]
            self.player.y = data["player"]["y"]
            self.player.rect.topleft = (self.player.x, self.player.y)

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
                    if not all(
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
        if self.show_controls_hint:
            font_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "assets", "sprites", "pixel.ttf"
            )
            if os.path.exists(font_path):
                font = pygame.font.Font(font_path, 12)
            else:
                font = pygame.font.SysFont("Arial", 12, bold=True)

            hint_text = "Arrows:Move | Space:Talk | S:Save | L:Load | ESC:Menu"
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

        if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
            self._save_game()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_l:
            self._load_game()
        # Interact with NPCs (spacebar)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
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
                        trainer_party_states = self._initialize_party(
                            self.active_npc.party
                        )
                        bs = BattleScene(self.manager)
                        trainer_party = [
                            bs.hydrate_mascot(state) for state in trainer_party_states
                        ]
                        battle = BattleScene(
                            self.manager,
                            party_states=self.party,
                            inventory=self.inventory,
                            opponent_party=trainer_party,
                            is_trainer_battle=True,
                        )
                        self.manager.push(battle)
                        # Mark trainer as defeated (will be set when returning from battle)
                        self.active_npc.defeated = True
                    # Close the dialogue box
                    self.active_dialogue = None
                    self.active_npc = None
            else:
                # Try to interact with NPC
                for npc in self.npcs:
                    if (
                        abs(self.player.x // TILE_SIZE - npc.x) <= 1
                        and abs(self.player.y // TILE_SIZE - npc.y) <= 1
                    ):
                        self.active_npc = npc
                        self.active_dialogue = npc.talk()
                        break

    def _execute_pause_action(self):
        """Execute selected pause menu action."""
        selected_option = self.pause_menu_options[self.pause_menu_idx]
        if selected_option == "Continue":
            self.is_paused = False
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
                self.player.x = 2 * TILE_SIZE
                self.player.y = 2 * TILE_SIZE
                delattr(self.manager, "battle_loss_reset")

        # Check if a mascot was captured in the last battle and add to party
        captured_name = getattr(self.manager, "captured_mascot_name", None)
        if captured_name:
            # Check if already in party (comparing against state dicts)
            if not any(state["name"] == captured_name for state in self.party):
                # Create fresh state with full HP
                from .battle_scene import BattleScene

                bs = BattleScene(self.manager)
                self.party.append(bs.make_mascot_state(captured_name))
            # Clear the flag so we don't add it again
            delattr(self.manager, "captured_mascot_name")

        keys = pygame.key.get_pressed()
        prev_pos = (self.player.x, self.player.y)
        # Calculate intended movement
        dx = dy = 0
        if keys[pygame.K_LEFT]:
            dx = -self.player.speed * dt
        elif keys[pygame.K_RIGHT]:
            dx = self.player.speed * dt
        if keys[pygame.K_UP]:
            dy = -self.player.speed * dt
        elif keys[pygame.K_DOWN]:
            dy = self.player.speed * dt
        target_x = self.player.x + dx
        target_y = self.player.y + dy
        if not self.npc_collides(target_x, target_y):
            self.player.move(dx, dy, self.tilemap)
        # Count steps only in tall grass
        tx, ty = int(self.player.x // TILE_SIZE), int(self.player.y // TILE_SIZE)
        in_grass = (
            0 <= tx < self.tilemap.width
            and 0 <= ty < self.tilemap.height
            and self.tilemap.tiles[ty][tx] == 2
        )
        if (self.player.x, self.player.y) != prev_pos and in_grass:
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

        # Camera follows player
        self.camera_x = max(
            0,
            min(
                self.player.x - SCREEN_WIDTH // 2, MAP_WIDTH * TILE_SIZE - SCREEN_WIDTH
            ),
        )
        self.camera_y = max(
            0,
            min(
                self.player.y - SCREEN_HEIGHT // 2,
                MAP_HEIGHT * TILE_SIZE - SCREEN_HEIGHT,
            ),
        )

    def draw(self, surface):
        self.tilemap.draw(surface, self.camera_x, self.camera_y, self.tile_images)
        self.player.draw(surface, self.camera_x, self.camera_y)
        # Draw NPCs (simple circle for now)
        for npc in self.npcs:
            px = npc.x * TILE_SIZE - self.camera_x
            py = npc.y * TILE_SIZE - self.camera_y
            pygame.draw.circle(
                surface,
                GB_PALETTE[2],
                (px + TILE_SIZE // 2, py + TILE_SIZE // 2),
                TILE_SIZE // 2,
            )
        # Draw dialogue box if active
        if self.active_dialogue:
            font = pygame.font.SysFont("Arial", 12, bold=True)
            box_w, box_h = 200, 32
            # Word wrap
            words = self.active_dialogue.split()
            lines = []
            current = ""
            for word in words:
                test = current + (" " if current else "") + word
                if font.size(test)[0] <= box_w - 20:
                    current = test
                else:
                    lines.append(current)
                    current = word
            if current:
                lines.append(current)
            box_h = 20 + 16 * len(lines)
            pygame.draw.rect(
                surface, GB_PALETTE[1], (20, SCREEN_HEIGHT - box_h - 10, box_w, box_h)
            )
            pygame.draw.rect(
                surface,
                GB_PALETTE[3],
                (20, SCREEN_HEIGHT - box_h - 10, box_w, box_h),
                1,
            )
            for i, line in enumerate(lines):
                text = font.render(line, True, GB_PALETTE[3])
                surface.blit(text, (30, SCREEN_HEIGHT - box_h + 8 + i * 16))

        self.draw_hud(surface)
        self.draw_control_hints(surface)
        self.draw_notification(surface)

        if self.is_paused:
            self.draw_pause_menu(surface)
            return
