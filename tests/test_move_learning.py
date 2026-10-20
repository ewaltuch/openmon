"""Forget-a-move prompt, persisted movesets and the XP bar (ROADMAP 2.1)."""

import pygame

from src.engine import mascots
from src.engine.battle_scene import BattleScene
from src.engine.save import SaveManager


class DummyManager:
    pass


def _key(scene, key):
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))


def _scene(level=13):
    scene = BattleScene(
        DummyManager(),
        party_states=[mascots.make_state("Tux", level=level)],
        wild_species="Octocat",
        wild_level=5,
    )
    scene.messages.clear()
    return scene


def _to_prompt(scene, extra=None):
    """Level Tux 13 -> 14 and read messages up to the forget menu."""
    scene._gain_xp(scene.player, mascots.xp_to_next(13))
    if extra:
        scene._say(extra)
    scene._show(scene.messages[0])
    scene.state = scene.STATE_MESSAGE
    for _ in range(10):
        if scene.state == scene.STATE_FORGET:
            return
        scene._text_pos = 999
        _key(scene, pygame.K_z)
    raise AssertionError("forget menu never opened")


def _drain(scene):
    texts = []
    while scene.state == scene.STATE_MESSAGE and scene.messages:
        texts.append(scene.messages[0].text)
        scene._text_pos = 999
        _key(scene, pygame.K_z)
    return texts


def test_full_moveset_prompts_instead_of_auto_forgetting():
    scene = _scene()
    before = [m.name for m in scene.player.moves]
    _to_prompt(scene)
    assert [m.name for m in scene.player.moves] == before
    assert scene._learning[1].name == "Kernel Panic"


def test_forget_chosen_move_replaces_it():
    scene = _scene()
    old = scene.player.moves[1].name
    _to_prompt(scene)
    for _ in range(3):  # new move (row 4) -> row 1
        _key(scene, pygame.K_UP)
    _key(scene, pygame.K_z)
    names = [m.name for m in scene.player.moves]
    assert old not in names and names[1] == "Kernel Panic"
    assert len(names) == 4
    texts = _drain(scene)
    assert texts == [f"Tux forgot {old}...", "... and learned Kernel Panic!"]
    assert scene.state == scene.STATE_MENU


def test_declining_keeps_moves():
    scene = _scene()
    before = [m.name for m in scene.player.moves]
    _to_prompt(scene)
    assert scene.forget_idx == mascots.MAX_MOVES
    _key(scene, pygame.K_z)  # cursor starts on the new move
    assert [m.name for m in scene.player.moves] == before
    assert _drain(scene) == ["Tux did not learn Kernel Panic."]


def test_x_declines_and_remaining_messages_follow():
    scene = _scene()
    _to_prompt(scene, extra="later message")
    _key(scene, pygame.K_UP)
    _key(scene, pygame.K_x)
    texts = _drain(scene)
    assert texts[0] == "Tux did not learn Kernel Panic."
    assert texts[-1] == "later message"
    assert "Kernel Panic" not in [m.name for m in scene.player.moves]


def test_draw_forget_menu_headless():
    scene = _scene()
    _to_prompt(scene)
    scene.draw(pygame.Surface((240, 160)))


def test_chosen_moveset_persists_through_save_load():
    scene = _scene()
    _to_prompt(scene)
    for _ in range(4):  # row 0
        _key(scene, pygame.K_UP)
    _key(scene, pygame.K_z)
    states = scene.get_party_states()
    assert states[0]["moves"][0] == "Kernel Panic"
    SaveManager.save({"player": {"x": 8, "y": 8}, "party": states})
    loaded = SaveManager.load()["party"][0]
    mascot = mascots.hydrate(loaded)
    assert [m.name for m in mascot.moves] == states[0]["moves"]


def test_state_without_moves_uses_derived_moves():
    state = mascots.make_state("Tux", level=14)
    assert "moves" not in state
    mascot = mascots.hydrate(state)
    assert [m.name for m in mascot.moves] == [
        m["name"] for m in mascots.learnset_moves("Tux", 14)
    ]


def test_xp_fraction():
    need = mascots.xp_to_next(5)
    assert mascots.xp_fraction(5, 0) == 0.0
    assert mascots.xp_fraction(5, need // 2) == (need // 2) / need
    assert mascots.xp_fraction(mascots.MAX_LEVEL, 0) == 0.0


def test_battle_draws_xp_bar_for_player():
    scene = _scene(level=5)
    scene.state = scene.STATE_MENU
    scene.player.xp = mascots.xp_to_next(5) // 2
    surface = pygame.Surface((240, 160))
    scene.draw(surface)
    half = pygame.image.tobytes(surface, "RGB")
    scene.player.xp = 0
    scene.draw(surface)
    assert half != pygame.image.tobytes(surface, "RGB")
