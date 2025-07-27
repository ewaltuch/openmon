"""
Overworld MVP for Open-Mon: tile map, player movement, collision, camera.
"""
import pygame
import csv
from src.constants import SCREEN_WIDTH, SCREEN_HEIGHT, GB_PALETTE, SPRITE_DIR

TILE_SIZE = 8
MAP_WIDTH = SCREEN_WIDTH // TILE_SIZE
MAP_HEIGHT = SCREEN_HEIGHT // TILE_SIZE

class TileMap:
    def __init__(self, csv_path):
        self.tiles = []
        with open(csv_path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                self.tiles.append([int(cell) for cell in row])
        self.width = len(self.tiles[0])
        self.height = len(self.tiles)

    def draw(self, surface, camera_x, camera_y, tile_images):
        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                img = tile_images[tile]
                surface.blit(img, (x * TILE_SIZE - camera_x, y * TILE_SIZE - camera_y))

class Player:
    def __init__(self, x, y, images):
        self.x = x
        self.y = y
        self.images = images
        self.image = images[0]
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.speed = 48  # px/sec

    def move(self, dx, dy, tilemap):
        nx, ny = self.x + dx, self.y + dy
        if not self.collides(nx, ny, tilemap):
            self.x, self.y = nx, ny
            self.rect.topleft = (self.x, self.y)

    def collides(self, x, y, tilemap):
        tx, ty = int(x // TILE_SIZE), int(y // TILE_SIZE)
        if 0 <= tx < tilemap.width and 0 <= ty < tilemap.height:
            return tilemap.tiles[ty][tx] == 1  # 1 = wall
        return True

    def update(self, dt, keys, tilemap):
        dx = dy = 0
        if keys[pygame.K_LEFT]:
            dx = -self.speed * dt
        elif keys[pygame.K_RIGHT]:
            dx = self.speed * dt
        if keys[pygame.K_UP]:
            dy = -self.speed * dt
        elif keys[pygame.K_DOWN]:
            dy = self.speed * dt
        if dx or dy:
            self.move(dx, dy, tilemap)

    def draw(self, surface, camera_x, camera_y):
        surface.blit(self.image, (self.x - camera_x, self.y - camera_y))
