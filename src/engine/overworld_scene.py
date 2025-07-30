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
    def __init__(self, manager):
        self.manager = manager
        self.tile_images = self._generate_tiles()
        self.tilemap = TileMap(os.path.join(SPRITE_DIR, "tiles.csv"))
        self.party = ["Tux", "BSD Daemon"]
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

    def _generate_tiles(self):
        # Generate 2 placeholder tiles (floor, wall) in 4-shade palette
        tiles = []
        for i in range(2):
            img = Image.new("RGB", (TILE_SIZE, TILE_SIZE), GB_PALETTE[i])
            if i == 1:
                draw = ImageDraw.Draw(img)
                draw.rectangle([2, 2, 5, 5], fill=GB_PALETTE[3])
            tiles.append(pygame.image.fromstring(img.tobytes(), img.size, img.mode))
        return tiles

    def _generate_player_sprite(self):
        # Simple 8x8 Tux placeholder
        img = Image.new("RGB", (TILE_SIZE, TILE_SIZE), GB_PALETTE[0])
        draw = ImageDraw.Draw(img)
        draw.ellipse([2, 2, 6, 6], fill=GB_PALETTE[2])
        draw.rectangle([3, 5, 4, 7], fill=GB_PALETTE[3])
        return pygame.image.fromstring(img.tobytes(), img.size, img.mode)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
            # Save game state with party
            SaveManager.save({
                "player": {"x": self.player.x, "y": self.player.y},
                "party": self.party,
                "inventory": [],
            })
        if event.type == pygame.KEYDOWN and event.key == pygame.K_l:
            # Load game state with party
            data = SaveManager.load()
            if data:
                self.player.x = data["player"]["x"]
                self.player.y = data["player"]["y"]
                self.player.rect.topleft = (self.player.x, self.player.y)
                self.party = data.get("party", ["Tux"])
        # Interact with NPCs (spacebar)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            for npc in self.npcs:
                if abs(self.player.x // TILE_SIZE - npc.x) <= 1 and abs(self.player.y // TILE_SIZE - npc.y) <= 1:
                    self.active_dialogue = npc.talk()
                    break

    def update(self, dt):
        # Check if a mascot was captured in the last battle and add to party
        captured_name = getattr(self.manager, "captured_mascot_name", None)
        if captured_name:
            if captured_name not in self.party:
                self.party.append(captured_name)
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
        # Count steps
        if (self.player.x, self.player.y) != prev_pos:
            self.steps += 1
            if self.steps >= self.encounter_steps:
                from .battle_scene import BattleScene
                mascots = [self._make_party_mascot(name) for name in self.party]
                self.manager.push(BattleScene(self.manager, party=mascots))
                self.steps = 0
                self.encounter_steps = random.randint(10, 20)

    def _make_party_mascot(self, name):
        from .battle_scene import BattleScene
        return BattleScene(self.manager).make_mascot(name)
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
