"""
Game loop and main engine entry point for Open-Mon.
"""

import pygame

from src.constants import SCREEN_HEIGHT, SCREEN_WIDTH

from . import audio
from .save import SaveManager
from .scene_manager import SceneManager
from .scenes import TitleScene

FPS = 60


class Game:
    """Main game engine class."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Open-Mon")
        self.clock = pygame.time.Clock()
        # Apply the saved mute setting before any music starts.
        save = SaveManager.load()
        if isinstance(save, dict):
            audio.set_muted(save.get("muted", False))
        self.manager = SceneManager()
        self.manager.push(TitleScene(self.manager))
        self.running = True

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.manager.handle_event(event)
            self.manager.update(dt)
            self.manager.draw(self.screen)
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
