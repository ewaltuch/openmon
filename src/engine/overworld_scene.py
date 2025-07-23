from .save import SaveManager
"""
OverworldScene implementation for Open-Mon.
"""
import pygame
from src.overworld import TileMap, Player, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT
from src.constants import GB_PALETTE, SPRITE_DIR
import os
from PIL import Image, ImageDraw


import random

class OverworldScene:
    def __init__(self, manager):
        self.manager = manager
        self.tile_images = self._generate_tiles()
        self.tilemap = TileMap(os.path.join(SPRITE_DIR, "tiles.csv"))
        self.player = Player(2 * TILE_SIZE, 2 * TILE_SIZE, [self._generate_player_sprite()])
        self.camera_x = 0
        self.camera_y = 0
        self.steps = 0
        self.encounter_steps = random.randint(10, 20)

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
            # Example: Save game state
            SaveManager.save({
                "player": {"x": self.player.x, "y": self.player.y},
                "party": ["Tux"],
                "inventory": [],
            })
        if event.type == pygame.KEYDOWN and event.key == pygame.K_l:
            # Example: Load game state
            data = SaveManager.load()
            if data:
                self.player.x = data["player"]["x"]
                self.player.y = data["player"]["y"]
                self.player.rect.topleft = (self.player.x, self.player.y)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        prev_pos = (self.player.x, self.player.y)
        self.player.update(dt, keys, self.tilemap)
        # Count steps
        if (self.player.x, self.player.y) != prev_pos:
            self.steps += 1
            if self.steps >= self.encounter_steps:
                from .battle_scene import BattleScene
                self.manager.push(BattleScene(self.manager))
                self.steps = 0
                self.encounter_steps = random.randint(10, 20)
        # Camera follows player
        self.camera_x = max(0, min(self.player.x - SCREEN_WIDTH // 2, MAP_WIDTH * TILE_SIZE - SCREEN_WIDTH))
        self.camera_y = max(0, min(self.player.y - SCREEN_HEIGHT // 2, MAP_HEIGHT * TILE_SIZE - SCREEN_HEIGHT))

    def draw(self, surface):
        self.tilemap.draw(surface, self.camera_x, self.camera_y, self.tile_images)
        self.player.draw(surface, self.camera_x, self.camera_y)
