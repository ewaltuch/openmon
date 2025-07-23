"""
BattleScene implementation for Open-Mon: simple turn-based battle, UI, capture.
"""
import pygame
import random
from src.constants import GB_PALETTE
from PIL import Image, ImageDraw

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
    MENU_NAMES = ["Fight", "Package", "Flee"]

    def __init__(self, manager):
        self.manager = manager
        self.player = Mascot(
            "Tux", 24, 8, 6, 7, self._generate_tux_sprite(), [Move("Peck", 6), Move("Code", 8)]
        )
        self.opponent = Mascot(
            "Octocat", 20, 7, 5, 6, self._generate_octocat_sprite(), [Move("Fork", 7), Move("PR", 5)]
        )
        self.menu_idx = 0
        self.state = "menu"  # menu, anim, result
        self.msg = "A wild Octocat appeared!"
        self.captured = False
        self.battle_over = False

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
        if self.state != "menu" or self.battle_over:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.menu_idx = (self.menu_idx - 1) % 3
            elif event.key == pygame.K_DOWN:
                self.menu_idx = (self.menu_idx + 1) % 3
            elif event.key == pygame.K_z:
                if self.menu_idx == self.MENU_FIGHT:
                    self._player_attack()
                elif self.menu_idx == self.MENU_PACKAGE:
                    self._try_capture()
                elif self.menu_idx == self.MENU_FLEE:
                    self.msg = "You fled!"
                    self.battle_over = True

    def _player_attack(self):
        move = self.player.moves[0]
        dmg = max(1, move.power + self.player.atk - self.opponent.defense)
        self.opponent.hp -= dmg
        self.msg = f"Tux used {move.name}! ({dmg} dmg)"
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
            self.msg = "You captured Octocat!"
            self.captured = True
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
        # Menu
        font = pygame.font.SysFont("Arial", 8)
        for i, name in enumerate(self.MENU_NAMES):
            color = GB_PALETTE[3] if i == self.menu_idx else GB_PALETTE[2]
            text = font.render(name, True, color)
            surface.blit(text, (8, 120 + i * 10))
        # Message
        msg_lines = self.msg.split("\n")
        for i, line in enumerate(msg_lines):
            text = font.render(line, True, GB_PALETTE[3])
            surface.blit(text, (64, 120 + i * 10))
