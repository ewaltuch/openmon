import pytest
import pygame
from src.engine.overworld_scene import OverworldScene

class DummyManager:
    def __init__(self):
        self.scenes = []
        self.captured_mascot_name = None
    def push(self, scene):
        self.scenes.append(scene)

def test_party_adds_captured():
    mgr = DummyManager()
    scene = OverworldScene(mgr)
    mgr.captured_mascot_name = "Octocat"
    scene.update(0.1)
    assert "Octocat" in scene.party

def test_party_initial():
    mgr = DummyManager()
    scene = OverworldScene(mgr)
    assert "Tux" in scene.party
    assert "BSD Daemon" in scene.party

def test_encounter_only_in_grass():
    mgr = DummyManager()
    scene = OverworldScene(mgr)
    # Place player in tall grass
    scene.player.x = 10 * 8
    scene.player.y = 2 * 8
    scene.steps = scene.encounter_steps - 1
    prev_scenes = len(mgr.scenes)
    # Patch pygame.key.get_pressed to simulate movement
    class FakeKeys:
        def __getitem__(self, key):
            return key == pygame.K_RIGHT
    orig_get_pressed = pygame.key.get_pressed
    pygame.key.get_pressed = lambda: FakeKeys()
    scene.update(0.1)
    pygame.key.get_pressed = orig_get_pressed
    # Should trigger encounter
    assert len(mgr.scenes) > prev_scenes
    # Move player out of grass
    scene.player.x = 1 * 8
    scene.player.y = 1 * 8
    scene.steps = scene.encounter_steps - 1
    prev_scenes = len(mgr.scenes)
    # Simulate movement again
    pygame.key.get_pressed = lambda: FakeKeys()
    scene.update(0.1)
    pygame.key.get_pressed = orig_get_pressed
    # Should NOT trigger encounter
    assert len(mgr.scenes) == prev_scenes
