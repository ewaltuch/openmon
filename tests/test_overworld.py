import pytest
from src.engine.overworld_scene import OverworldScene

class DummyManager:
    def __init__(self):
        self.scenes = []
        self.captured_mascot_name = None

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
