"""
Constants for Open-Mon. All global settings and palette definitions.
"""

# Game Boy Advance native resolution
SCREEN_WIDTH = 240
SCREEN_HEIGHT = 160
FPS = 60

# Largest party the battle switch menu can display
PARTY_MAX = 5

# Repository (storage box) capacity for mascots beyond the party
STORAGE_MAX = 30

# Game Boy 4-shade palette (lightest to darkest)
GB_PALETTE = [
    (224, 248, 208),  # White
    (136, 192, 112),  # Light gray
    (52, 104, 86),  # Dark gray
    (8, 24, 32),  # Black
]

# Asset paths
ASSET_DIR = "assets/"
SPRITE_DIR = ASSET_DIR + "sprites/"
MAP_DIR = ASSET_DIR + "maps/"
DEFAULT_MAP = "town"
SFX_DIR = ASSET_DIR + "sfx/"

# Save path
SAVE_PATH = ".openmon/save1.json"
