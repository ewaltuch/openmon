import os
import json
import pytest
from src.engine.save import SaveManager

def test_save_and_load(tmp_path, monkeypatch):
    # Patch SAVE_PATH to use tmp_path
    monkeypatch.setattr('src.constants.SAVE_PATH', str(tmp_path / "save1.json"))
    state = {"player": {"x": 5, "y": 7}, "party": ["Tux"], "inventory": ["Package"]}
    SaveManager.save(state)
    loaded = SaveManager.load()
    assert loaded == state
