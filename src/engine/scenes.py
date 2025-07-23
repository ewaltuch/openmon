"""
Scene definitions for Open-Mon: Title, Overworld, Battle, Credits.
"""
import pygame

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
    def draw(self, surface):
        surface.fill((255, 255, 255))
        font = pygame.font.SysFont("Arial", 16)
        text = font.render("Open-Mon", True, (0, 0, 0))
        surface.blit(text, (40, 60))

from .overworld_scene import OverworldScene

from .battle_scene import BattleScene

class CreditsScene(Scene):
    pass
