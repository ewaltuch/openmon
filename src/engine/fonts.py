"""
Shared font loading for Open-Mon. Fonts are created once per size instead of
on every frame.
"""

import os

import pygame

PIXEL_FONT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "assets", "sprites", "pixel.ttf"
)

_cache = {}


def _clear_cache():
    # Font objects die with pygame.quit(); drop them so a later init rebuilds
    _cache.clear()


pygame.register_quit(_clear_cache)


def get_font(size):
    """Pixel font at size if assets/sprites/pixel.ttf exists, else bold Arial."""
    font = _cache.get(size)
    if font is None:
        if not pygame.font.get_init():
            pygame.font.init()
        if os.path.exists(PIXEL_FONT_PATH):
            font = pygame.font.Font(PIXEL_FONT_PATH, size)
        else:
            font = pygame.font.SysFont("Arial", size, bold=True)
        _cache[size] = font
    return font


def wrap_text(font, text, max_width):
    """Split text into lines no wider than max_width; keeps explicit newlines."""
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split():
            test = current + (" " if current else "") + word
            if current and font.size(test)[0] > max_width:
                lines.append(current)
                current = word
            else:
                current = test
        lines.append(current)
    return lines
