"""
Scene definitions for Open-Mon: Title, Overworld, Battle, Credits.
"""

import pygame

from src.constants import GB_PALETTE, SCREEN_WIDTH
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


CONFIRM_KEYS = (pygame.K_z, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


class TitleScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.idx = 0
        audio.play_music("title")
        self.refresh_options()

    def refresh_options(self):
        """Continue is only offered when a save exists."""
        from .save import SaveManager

        self.options = ["New Game"]
        if SaveManager.load() is not None:
            self.options.append("Continue")
        self.options.append("Credits")
        self.idx = min(self.idx, len(self.options) - 1)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_UP:
            self.idx = (self.idx - 1) % len(self.options)
        elif event.key == pygame.K_DOWN:
            self.idx = (self.idx + 1) % len(self.options)
        elif event.key in CONFIRM_KEYS:
            self._select(self.options[self.idx])

    def _select(self, option):
        from .overworld_scene import OverworldScene

        if option == "New Game":
            self.manager.push(OverworldScene(self.manager))
        elif option == "Continue":
            overworld = OverworldScene(self.manager)
            overworld._load_game()
            self.manager.push(overworld)
        elif option == "Credits":
            self.manager.push(CreditsScene(self.manager))

    def draw(self, surface):
        surface.fill(GB_PALETTE[0])
        font = get_font(16)
        text = font.render("Open-Mon", True, GB_PALETTE[3])
        surface.blit(text, ((SCREEN_WIDTH - text.get_width()) // 2, 28))
        small = get_font(12)
        for i, option in enumerate(self.options):
            selected = i == self.idx
            color = GB_PALETTE[3] if selected else GB_PALETTE[2]
            label = small.render(f"> {option}" if selected else option, True, color)
            surface.blit(label, (80, 70 + i * 18))


CREDITS_LINES = [
    "Open-Mon",
    "A Game Boy-style RPG made",
    "with Pygame.",
    "",
    "Mascots and their origins",
    "Tux - the Linux kernel",
    "BSD Daemon - the BSD family",
    "Octocat - GitHub",
    "",
    "Open-source mascots belong",
    "to their projects and",
    "communities.",
    "Thanks for playing!",
]


class CreditsScene(Scene):
    VISIBLE = 9
    LINE_H = 13

    def __init__(self, manager):
        super().__init__(manager)
        self.scroll = 0

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_z, pygame.K_ESCAPE, pygame.K_x, pygame.K_RETURN):
            self.manager.pop()
        elif event.key == pygame.K_DOWN:
            self.scroll = min(len(CREDITS_LINES) - self.VISIBLE, self.scroll + 1)
        elif event.key == pygame.K_UP:
            self.scroll = max(0, self.scroll - 1)

    def draw(self, surface):
        surface.fill(GB_PALETTE[0])
        font = get_font(10)
        title = get_font(12).render("Credits", True, GB_PALETTE[3])
        surface.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 4))
        lines = CREDITS_LINES[self.scroll : self.scroll + self.VISIBLE]
        for i, line in enumerate(lines):
            text = font.render(line, True, GB_PALETTE[3])
            surface.blit(text, (12, 24 + i * self.LINE_H))
        hint = font.render("Up/Down: scroll  Z/Esc: back", True, GB_PALETTE[2])
        surface.blit(hint, (12, 146))
