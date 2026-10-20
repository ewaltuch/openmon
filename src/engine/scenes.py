"""
Scene definitions for Open-Mon: Title, Overworld, Battle, Credits.
"""

import pygame

from src.constants import GB_PALETTE
from src.engine import audio
from src.engine.fonts import get_font


class Scene:
    def __init__(self, manager):
        self.manager = manager

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass


class TitleScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        audio.play_music("title")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            from .overworld_scene import OverworldScene

            self.manager.push(OverworldScene(self.manager))

    def draw(self, surface):
        surface.fill(GB_PALETTE[0])
        font = get_font(16)
        text = font.render("Open-Mon", True, GB_PALETTE[3])
        surface.blit(text, (32, 60))
        subtitle = font.render("Press any key...", True, GB_PALETTE[2])
        surface.blit(subtitle, (16, 90))


class CreditsScene(Scene):
    pass
