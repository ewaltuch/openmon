import os

import pygame
import pytest

# Run headless (CI has no display)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


@pytest.fixture(autouse=True)
def isolated_save_path(tmp_path, monkeypatch):
    """Never let a test read or overwrite the player's real save file."""
    monkeypatch.setattr("src.constants.SAVE_PATH", str(tmp_path / "save1.json"))


@pytest.fixture(autouse=True)
def pygame_display():
    """Every test gets an initialised pygame, whatever earlier tests did."""
    pygame.init()
    pygame.display.set_mode((240, 160))
    yield


@pytest.fixture(autouse=True)
def instant_battle_text(monkeypatch):
    """Battle text appears at once, so one Z press advances one message."""
    monkeypatch.setattr("src.engine.battle_scene.TEXT_CPS", 0)
