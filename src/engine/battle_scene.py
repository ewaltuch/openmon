"""
BattleScene implementation for Open-Mon: simple turn-based battle, UI, capture.
"""

import pygame
import random
from src.constants import GB_PALETTE, SCREEN_WIDTH, SCREEN_HEIGHT
from PIL import Image, ImageDraw
import os

class Mascot:
    def __init__(self, name, hp, atk, defense, spd, sprite, moves):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.defense = defense
        self.spd = spd
        self.sprite = sprite
        self.moves = moves

class Move:
    def __init__(self, name, power):
        self.name = name
        self.power = power


class BattleScene:
    MENU_FIGHT = 0
    MENU_PACKAGE = 1
    MENU_FLEE = 2
    MENU_SWITCH = 3

    def __init__(self, manager, party=None):
        self.manager = manager
        self.party = party or [self.make_mascot("Tux"), self.make_mascot("BSD Daemon")]
        self.active_idx = 0
        self.player = self.party[self.active_idx]
        self.opponent = self.make_mascot("Octocat")
        self.menu_idx = 0
        self.state = "menu"  # menu, anim, result
        self.msg = "A wild Octocat appeared!"
        self.captured = False
        self.battle_over = False

    @property
    def menu_names(self):
        names = ["Fight", "Package", "Flee"]
        if len(self.party) > 1:
            names.append("Switch")
        return names

    def make_mascot(self, name):
        if name == "Tux":
            return Mascot(
                "Tux", 24, 8, 6, 7, self._generate_tux_sprite(), [Move("Peck", 6), Move("Code", 8)]
            )
        elif name == "BSD Daemon":
            img = Image.new("RGB", (32, 32), GB_PALETTE[0])
            draw = ImageDraw.Draw(img)
            draw.ellipse([8, 8, 24, 24], fill=GB_PALETTE[2])
            draw.rectangle([12, 24, 20, 28], fill=GB_PALETTE[1])
            return Mascot(
                "BSD Daemon", 22, 7, 7, 5, pygame.image.fromstring(img.tobytes(), img.size, img.mode), [Move("Fork Bomb", 7), Move("Daemonize", 5)]
            )
        elif name == "Octocat":
            return Mascot(
                "Octocat", 20, 7, 5, 6, self._generate_octocat_sprite(), [Move("Fork", 7), Move("PR", 5)]
            )
        # Default fallback
        return Mascot(
            name, 20, 5, 5, 5, self._generate_tux_sprite(), [Move("Peck", 5)]
        )

    def _generate_tux_sprite(self):
        img = Image.new("RGB", (32, 32), GB_PALETTE[0])
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 8, 24, 24], fill=GB_PALETTE[2])
        draw.rectangle([14, 20, 18, 28], fill=GB_PALETTE[3])
        return pygame.image.fromstring(img.tobytes(), img.size, img.mode)

    def _generate_octocat_sprite(self):
        img = Image.new("RGB", (32, 32), GB_PALETTE[0])
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 8, 24, 24], fill=GB_PALETTE[1])
        draw.rectangle([12, 24, 20, 28], fill=GB_PALETTE[3])
        return pygame.image.fromstring(img.tobytes(), img.size, img.mode)

    def handle_event(self, event):
        if self.battle_over:
            if event.type == pygame.KEYDOWN:
                self.manager.pop()
            return
        if self.state != "menu":
            return
        if event.type == pygame.KEYDOWN:
            menu_len = len(self.menu_names)
            if event.key == pygame.K_UP:
                self.menu_idx = (self.menu_idx - 1) % menu_len
            elif event.key == pygame.K_DOWN:
                self.menu_idx = (self.menu_idx + 1) % menu_len
            elif event.key in (pygame.K_z, pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.menu_idx == self.MENU_FIGHT:
                    self._player_attack()
                elif self.menu_idx == self.MENU_PACKAGE:
                    self._try_capture()
                elif self.menu_idx == self.MENU_FLEE:
                    self.msg = "You fled!"
                    self.battle_over = True
                elif len(self.party) > 1 and self.menu_idx == self.menu_names.index("Switch"):
                    self._switch_party()

    def _switch_party(self):
        # Switch to next mascot in party
        if len(self.party) > 1:
            self.active_idx = (self.active_idx + 1) % len(self.party)
            self.player = self.party[self.active_idx]
            self.msg = f"Go, {self.player.name}!"

    def _player_attack(self):
        move = self.player.moves[0]
        dmg = max(1, move.power + self.player.atk - self.opponent.defense)
        self.opponent.hp -= dmg
        self.msg = f"{self.player.name} used {move.name}! ({dmg} dmg)"
        if self.opponent.hp <= 0:
            self.msg = "Octocat fainted!"
            self.battle_over = True
        else:
            self._opponent_attack()

    def _opponent_attack(self):
        move = random.choice(self.opponent.moves)
        dmg = max(1, move.power + self.opponent.atk - self.player.defense)
        self.player.hp -= dmg
        self.msg += f"\nOctocat used {move.name}! ({dmg} dmg)"
        if self.player.hp <= 0:
            self.msg += "\nTux fainted!"
            self.battle_over = True

    def _try_capture(self):
        # Simple probability: higher if opponent HP is low
        prob = max(0.2, 1.0 - self.opponent.hp / self.opponent.max_hp)
        if random.random() < prob:
            self.msg = f"You captured {self.opponent.name}!"
            self.captured = True
            # Add to party for this battle
            if not any(m.name == self.opponent.name for m in self.party):
                self.party.append(self.opponent)
            # Persist captured mascot name on the manager for the overworld
            setattr(self.manager, "captured_mascot_name", self.opponent.name)
            self.battle_over = True
        else:
            self.msg = "Capture failed!"
            self._opponent_attack()

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(GB_PALETTE[0])
        # Draw mascots
        surface.blit(self.player.sprite, (16, 64))
        surface.blit(self.opponent.sprite, (112, 16))
        # HP bars
        pygame.draw.rect(surface, GB_PALETTE[3], (16, 56, 40, 4))
        pygame.draw.rect(surface, GB_PALETTE[1], (16, 56, int(40 * self.player.hp / self.player.max_hp), 4))
        pygame.draw.rect(surface, GB_PALETTE[3], (112, 8, 40, 4))
        pygame.draw.rect(surface, GB_PALETTE[2], (112, 8, int(40 * self.opponent.hp / self.opponent.max_hp), 4))

        # Use a pixel font for crisp text if available, else fallback
        font_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sprites", "pixel.ttf")
        # Use a larger font for battle UI text
        menu_font_size = 12
        msg_font_size = 12
        if os.path.exists(font_path):
            menu_font = pygame.font.Font(font_path, menu_font_size)
            msg_font = pygame.font.Font(font_path, msg_font_size)
        else:
            menu_font = pygame.font.SysFont("Arial", menu_font_size, bold=True)
            msg_font = pygame.font.SysFont("Arial", msg_font_size, bold=True)

        # Draw a UI window background for menu and message
        window_y = SCREEN_HEIGHT - 56
        menu_names = self.menu_names
        # Separate Switch if present
        if "Switch" in menu_names:
            vert_names = menu_names[:-1]
            switch_name = menu_names[-1]
        else:
            vert_names = menu_names
            switch_name = None
        menu_lines = len(vert_names)
        msg_lines = len(self.msg.split("\n"))
        window_height = 4 + max(menu_lines, msg_lines) * 14 + 4 + (18 if switch_name else 0)
        pygame.draw.rect(surface, GB_PALETTE[1], (0, window_y, SCREEN_WIDTH, window_height))
        pygame.draw.rect(surface, GB_PALETTE[3], (0, window_y, SCREEN_WIDTH, window_height), 1)

        # Vertical menu
        for i, name in enumerate(vert_names):
            color = GB_PALETTE[3] if self.menu_idx == i else GB_PALETTE[2]
            text = menu_font.render(name, True, color)
            surface.blit(text, (8, window_y + 4 + i * 14))

        # Switch option directly under the vertical menu options, left-aligned
        if switch_name:
            idx = len(vert_names)
            color = GB_PALETTE[3] if self.menu_idx == idx else GB_PALETTE[2]
            text = menu_font.render(switch_name, True, color)
            surface.blit(text, (8, window_y + 4 + menu_lines * 14))
        # Message
        msg_lines = self.msg.split("\n")
        for i, line in enumerate(msg_lines):
            text = msg_font.render(line, True, GB_PALETTE[3])
            surface.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, window_y + 4 + i * 14))
