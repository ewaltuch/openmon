import pytest
import pygame
from src.engine.game import Game

def test_game_init():
    game = Game()
    assert game.screen.get_width() == 240
    assert game.screen.get_height() == 160
    assert game.manager is not None

def test_npc_collision_and_dialogue():
    from src.engine.overworld_scene import OverworldScene
    mgr = type("DummyManager", (), {"scenes": []})()
    scene = OverworldScene(mgr)
    # Place player on top of first NPC
    npc = scene.npcs[0]
    scene.player.x = npc.x * 8
    scene.player.y = npc.y * 8
    assert scene.npc_collides(scene.player.x, scene.player.y)
    # Simulate interaction
    scene.active_dialogue = npc.talk()
    assert isinstance(scene.active_dialogue, str)
