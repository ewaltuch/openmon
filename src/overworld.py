"""
Overworld MVP for Open-Mon: tile map, grid-based player movement, collision.
"""

import csv

import pygame

TILE_SIZE = 8

FLOOR, WALL, GRASS = 0, 1, 2

# Direction -> (dx, dy) in tiles
DIRECTIONS = {
    "left": (-1, 0),
    "right": (1, 0),
    "up": (0, -1),
    "down": (0, 1),
}
# Held arrow key -> direction, checked in this order
KEY_DIRECTIONS = [
    (pygame.K_LEFT, "left"),
    (pygame.K_RIGHT, "right"),
    (pygame.K_UP, "up"),
    (pygame.K_DOWN, "down"),
]


class TileMap:
    def __init__(self, csv_path):
        self.tiles = []
        with open(csv_path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                self.tiles.append([int(cell) for cell in row])
        self.width = len(self.tiles[0])
        self.height = len(self.tiles)

    def tile_at(self, tx, ty):
        """Tile id at tile coords, or None outside the map."""
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.tiles[ty][tx]
        return None

    def is_walkable(self, tx, ty):
        tile = self.tile_at(tx, ty)
        return tile is not None and tile != WALL

    def draw(self, surface, camera_x, camera_y, tile_images):
        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                img = tile_images[tile]
                surface.blit(img, (x * TILE_SIZE - camera_x, y * TILE_SIZE - camera_y))


class Player:
    """Moves one tile at a time, sliding between tiles like Pokemon Red/Blue."""

    def __init__(self, x, y, images):
        self.x = x
        self.y = y
        self.images = images
        self.image = images[0]
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.speed = 40  # px/sec, i.e. 5 tiles per second
        self.facing = "down"
        self.target = None  # Pixel position being walked to, if mid-step

    @property
    def tile(self):
        return int(self.x // TILE_SIZE), int(self.y // TILE_SIZE)

    @property
    def moving(self):
        return self.target is not None

    def facing_tile(self):
        dx, dy = DIRECTIONS[self.facing]
        tx, ty = self.tile
        return tx + dx, ty + dy

    def place(self, tx, ty):
        """Snap to a tile, cancelling any step in progress."""
        self.x, self.y = tx * TILE_SIZE, ty * TILE_SIZE
        self.target = None
        self.rect.topleft = (self.x, self.y)

    def try_step(self, direction, tilemap, is_blocked=lambda tx, ty: False):
        """Face direction and start walking there if the tile is free."""
        self.facing = direction
        tx, ty = self.facing_tile()
        if not tilemap.is_walkable(tx, ty) or is_blocked(tx, ty):
            return False
        self.target = (tx * TILE_SIZE, ty * TILE_SIZE)
        return True

    def update(self, dt):
        """Advance the current step. Returns True on the frame a step ends."""
        if self.target is None:
            return False
        tx, ty = self.target
        step = self.speed * dt
        self.x += max(-step, min(step, tx - self.x))
        self.y += max(-step, min(step, ty - self.y))
        self.rect.topleft = (self.x, self.y)
        if (self.x, self.y) == (tx, ty):
            self.target = None
            return True
        return False

    def draw(self, surface, camera_x, camera_y):
        surface.blit(self.image, (self.x - camera_x, self.y - camera_y))
