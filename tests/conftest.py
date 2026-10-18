import pytest


@pytest.fixture(autouse=True)
def isolated_save_path(tmp_path, monkeypatch):
    """Never let a test read or overwrite the player's real save file."""
    monkeypatch.setattr("src.constants.SAVE_PATH", str(tmp_path / "save1.json"))
