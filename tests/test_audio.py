import pygame
import pytest

from src.engine import audio
from src.engine.battle_scene import BattleMessage, BattleScene
from src.engine.overworld_scene import OverworldScene
from src.engine.save import SaveManager
from src.engine.scene_manager import SceneManager


@pytest.fixture(autouse=True)
def fresh_audio(monkeypatch):
    monkeypatch.setattr(audio, "muted", False)
    monkeypatch.setattr(audio, "current_music", None)
    monkeypatch.setattr(audio, "played", [])
    monkeypatch.setattr(audio, "_ready", None)
    monkeypatch.setattr(audio, "_music_channel", None)


@pytest.fixture
def no_mixer(monkeypatch):
    def boom(*a, **k):
        raise pygame.error("no audio device")

    monkeypatch.setattr(pygame.mixer, "get_init", lambda: None)
    monkeypatch.setattr(pygame.mixer, "init", boom)


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def test_everything_is_noop_without_mixer(no_mixer):
    audio.play_music("battle")
    audio.play_sfx("hit")
    audio.stop_music()
    audio.toggle_mute()
    assert audio._ready is False


def test_synthesis_works_when_mixer_available():
    if not audio._init():
        pytest.skip("no audio device")
    for name in audio.SFX:
        audio.play_sfx(name)
    audio.play_music("overworld")
    audio.stop_music()


def test_music_tracks_scene_changes():
    manager = SceneManager()
    OverworldScene(manager)
    assert audio.current_music == "overworld"
    battle = BattleScene(manager, wild_species="Tux")
    assert audio.current_music == "battle"
    manager.push(battle)
    battle._finish_battle()
    assert audio.current_music == "overworld"


def test_mute_blocks_sfx_and_toggles_with_m():
    scene = OverworldScene(SceneManager())
    scene.handle_event(key(pygame.K_m))
    assert audio.muted
    audio.play_sfx("hit")
    scene.handle_event(key(pygame.K_m))
    assert not audio.muted


def test_mute_saved_and_old_saves_load():
    scene = OverworldScene(SceneManager())
    audio.set_muted(True)
    scene._save_game()
    assert SaveManager.load()["muted"] is True
    audio.set_muted(False)
    scene._load_game()
    assert audio.muted

    data = SaveManager.load()
    del data["muted"]
    SaveManager.save(data)
    scene._load_game()
    assert not audio.muted


def test_battle_message_sound_plays_when_shown():
    assert BattleMessage("x", None, 0, None, 0).sound is None
    battle = BattleScene(SceneManager(), wild_species="Tux")
    battle.messages.clear()
    battle._say("first")
    battle._say("Ouch", "hit")
    battle._say("Gone", "faint")
    audio.played.clear()
    battle._advance_message()
    assert audio.played == ["hit"]
    battle._advance_message()
    assert audio.played == ["hit", "faint"]


def test_battle_menu_sfx():
    battle = BattleScene(SceneManager(), wild_species="Tux")
    battle.messages.clear()
    battle.state = battle.STATE_MENU
    audio.played.clear()
    battle.handle_event(key(pygame.K_RIGHT))
    battle.handle_event(key(pygame.K_z))
    assert audio.played[:2] == ["move", "confirm"]
