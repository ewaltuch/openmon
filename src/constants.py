"""
Constants for Open-Mon. All global settings and palette definitions.
"""

# Game Boy native resolution
SCREEN_WIDTH = 160
SCREEN_HEIGHT = 144
FPS = 60

# Game Boy 4-shade palette (lightest to darkest)
GB_PALETTE = [
    (224, 248, 208),  # White
    (136, 192, 112),  # Light gray
    (52, 104, 86),    # Dark gray
    (8, 24, 32),      # Black
]

# Asset paths
ASSET_DIR = "assets/"
SPRITE_DIR = ASSET_DIR + "sprites/"
SFX_DIR = ASSET_DIR + "sfx/"
MUSIC_DIR = ASSET_DIR + "music/"

# Save path
SAVE_PATH = ".openmon/save1.json"
