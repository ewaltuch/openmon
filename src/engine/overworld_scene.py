from .save import SaveManager
"""
OverworldScene implementation for Open-Mon.
"""
import pygame
from src.overworld import TileMap, Player, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT
from src.constants import GB_PALETTE, SPRITE_DIR, SCREEN_WIDTH, SCREEN_HEIGHT
import os
from PIL import Image, ImageDraw


import random

class OverworldScene:
    def npc_collides(self, x, y):
        # Check if player's bounding box overlaps any NPC tile
        player_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        for npc in self.npcs:
            npc_rect = pygame.Rect(npc.x * TILE_SIZE, npc.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if player_rect.colliderect(npc_rect):
                return True
        return False
    def __init__(self, manager, inventory=None):
        self.manager = manager
        self.tile_images = self._generate_tiles()
        self.tilemap = TileMap(os.path.join(SPRITE_DIR, "tiles.csv"))
        # Initialize party as state dictionaries
        self.party = self._initialize_party(["Tux", "BSD Daemon"])
        self.player = Player(2 * TILE_SIZE, 2 * TILE_SIZE, [self._generate_player_sprite()])
        self.camera_x = 0
        self.camera_y = 0
        self.steps = 0
        self.encounter_steps = random.randint(10, 20)
        self._pending_captured = None
        self._last_battle_captured_name = None
        # Load NPCs
        from src.engine.npc import load_npcs
        self.npcs = load_npcs(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "npcs.yaml"))
        self.active_dialogue = None
        self.active_npc = None
        # Inventory system
        from src.engine.inventory import InventoryManager
        self.inventory = inventory or InventoryManager()
        # Give player starting items
        if not inventory:
            self.inventory.add_item("package", 5)
            self.inventory.add_item("health_pack", 3)

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

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
            # Save game state with party and inventory
            SaveManager.save({
                "player": {"x": self.player.x, "y": self.player.y},
                "party": self.party,
                "inventory": self.inventory.to_dict(),
            })
        if event.type == pygame.KEYDOWN and event.key == pygame.K_l:
            # Load game state with party and inventory
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
                        if not all(k in state for k in ["name", "hp", "max_hp", "atk", "defense", "spd", "type"]):
                            # Invalid state, reinitialize
                            self.party = self._initialize_party(["Tux"])
                            break

                if "inventory" in data:
                    self.inventory.from_dict(data["inventory"])
        # Interact with NPCs (spacebar)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if self.active_dialogue and self.active_npc:
                # Advance dialogue with the current NPC
                next_line = self.active_npc.talk()
                if next_line:
                    self.active_dialogue = next_line
                else:
                    # No more dialogue, close the dialogue box
                    self.active_dialogue = None
                    self.active_npc = None
            else:
                # Try to interact with NPC
                for npc in self.npcs:
                    if abs(self.player.x // TILE_SIZE - npc.x) <= 1 and abs(self.player.y // TILE_SIZE - npc.y) <= 1:
                        self.active_npc = npc
                        self.active_dialogue = npc.talk()
                        break

    def update(self, dt):
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
        in_grass = (0 <= tx < self.tilemap.width and 0 <= ty < self.tilemap.height and self.tilemap.tiles[ty][tx] == 2)
        if (self.player.x, self.player.y) != prev_pos and in_grass:
            self.steps += 1
            if self.steps >= self.encounter_steps:
                from .battle_scene import BattleScene
                # Pass party states to battle
                self.manager.push(BattleScene(self.manager, party_states=self.party, inventory=self.inventory))
                self.steps = 0
                self.encounter_steps = random.randint(10, 20)

        # Camera follows player
        self.camera_x = max(0, min(self.player.x - SCREEN_WIDTH // 2, MAP_WIDTH * TILE_SIZE - SCREEN_WIDTH))
        self.camera_y = max(0, min(self.player.y - SCREEN_HEIGHT // 2, MAP_HEIGHT * TILE_SIZE - SCREEN_HEIGHT))

    def draw(self, surface):
        self.tilemap.draw(surface, self.camera_x, self.camera_y, self.tile_images)
        self.player.draw(surface, self.camera_x, self.camera_y)
        # Draw NPCs (simple circle for now)
        for npc in self.npcs:
            px = npc.x * TILE_SIZE - self.camera_x
            py = npc.y * TILE_SIZE - self.camera_y
            pygame.draw.circle(surface, GB_PALETTE[2], (px + TILE_SIZE // 2, py + TILE_SIZE // 2), TILE_SIZE // 2)
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
            pygame.draw.rect(surface, GB_PALETTE[1], (20, SCREEN_HEIGHT - box_h - 10, box_w, box_h))
            pygame.draw.rect(surface, GB_PALETTE[3], (20, SCREEN_HEIGHT - box_h - 10, box_w, box_h), 1)
            for i, line in enumerate(lines):
                text = font.render(line, True, GB_PALETTE[3])
                surface.blit(text, (30, SCREEN_HEIGHT - box_h + 8 + i * 16))
