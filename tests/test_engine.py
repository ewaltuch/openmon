import pytest
import pygame
from src.engine.game import Game

def test_game_init():
    game = Game()
    assert game.screen.get_width() == 240
    assert game.screen.get_height() == 160
    assert game.manager is not None
