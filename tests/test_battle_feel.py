import pygame

from src.engine import battle_scene as bs
from src.engine.battle_scene import BattleMessage, BattleScene, Move


class DummyManager:
    pass


def _scene(player="Tux", wild="Octocat"):
    state = BattleScene(DummyManager()).make_mascot_state(player)
    return BattleScene(DummyManager(), party_states=[state], wild_species=wild)


def _press(scene, key=pygame.K_z):
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))


def test_damage_scales_with_power_and_ratio():
    scene = _scene()
    tux, octo = scene.player, scene.opponent
    bs.damage_rng.seed(1)
    weak = scene._calc_damage(Move("a", 4, "Kernel"), tux, octo)[0]
    bs.damage_rng.seed(1)
    strong = scene._calc_damage(Move("b", 12, "Kernel"), tux, octo)[0]
    assert strong > weak
    # Higher defense takes less from the same hit
    bs.damage_rng.seed(1)
    tank = scene.make_mascot("BSD Daemon")
    tank.defense = 20
    soft = scene._calc_damage(Move("c", 8, "Kernel"), tux, octo)[0]
    bs.damage_rng.seed(1)
    assert scene._calc_damage(Move("c", 8, "Kernel"), tux, tank)[0] < soft


def test_damage_applies_type_multiplier_and_min_one():
    scene = _scene()
    tux, octo = scene.player, scene.opponent
    bs.damage_rng.seed(3)
    normal, m1 = scene._calc_damage(Move("n", 10, "Kernel"), tux, octo)
    bs.damage_rng.seed(3)
    good, m2 = scene._calc_damage(Move("s", 10, "Shell"), tux, octo)
    assert (m1, m2) == (1.0, 2.0)
    assert good >= 2 * normal - 1
    octo.defense = 999
    assert scene._calc_damage(Move("z", 1, "Kernel"), tux, octo)[0] == 1


def test_damage_random_factor_is_seedable_and_bounded():
    scene = _scene()
    tux, octo = scene.player, scene.opponent
    move = Move("m", 10, "Kernel")
    rolls = []
    for seed in (5, 5):
        bs.damage_rng.seed(seed)
        rolls.append(scene._calc_damage(move, tux, octo)[0])
    assert rolls[0] == rolls[1]
    base = move.power * tux.atk / octo.defense * bs.DAMAGE_SCALE
    for seed in range(30):
        bs.damage_rng.seed(seed)
        dmg = scene._calc_damage(move, tux, octo)[0]
        assert int(base * 0.85) <= dmg <= int(base)


def test_battles_have_reasonable_length():
    names = ["Tux", "BSD Daemon", "Octocat", "Gopher", "Elephpant", "Konqi"]
    scene = _scene()
    bs.damage_rng.seed(0)
    for a in names:
        for b in names:
            atk, dfn = scene.make_mascot(a), scene.make_mascot(b)
            avg = sum(scene._calc_damage(m, atk, dfn)[0] for m in atk.moves) / len(
                atk.moves
            )
            assert 2 <= dfn.max_hp / avg <= 10, (a, b, avg)


def test_attack_message_carries_hit_effect_for_defender():
    scene = _scene()
    scene.messages.clear()
    scene._attack(scene.player, scene.opponent, scene.player.moves[0])
    assert scene.messages[0].effect == bs.HIT_OPPONENT
    scene.messages.clear()
    scene._attack(scene.opponent, scene.player, scene.opponent.moves[0])
    assert scene.messages[0].effect == bs.HIT_PLAYER
    assert scene.messages[0].sound == "hit"
    assert BattleMessage("x", None, 0, None, 0).effect is None


def test_typewriter_reveals_then_z_completes_then_advances(monkeypatch):
    monkeypatch.setattr(bs, "TEXT_CPS", 10)
    scene = _scene()
    text = scene.messages[0].text
    assert not scene._text_done()
    scene.update(0.5)
    assert int(scene._text_pos) == 5
    _press(scene)  # completes the text, message stays
    assert scene._text_done() and len(scene.messages) == 1
    assert scene.state == scene.STATE_MESSAGE
    _press(scene)  # now advances
    assert scene.state == scene.STATE_MENU
    assert len(text) > 5


def test_next_message_restarts_typewriter(monkeypatch):
    monkeypatch.setattr(bs, "TEXT_CPS", 10)
    scene = _scene()
    scene.messages.clear()
    scene._say("one")
    scene._say("two")
    scene._text_pos = 99
    _press(scene)
    assert scene.messages[0].text == "two"
    assert scene._text_pos == 0 and not scene._text_done()


def test_draw_shows_partial_text_prompt_and_effect(monkeypatch):
    monkeypatch.setattr(bs, "TEXT_CPS", 10)
    surface = pygame.Surface((240, 160))
    scene = _scene()
    scene.messages.clear()
    scene._attack(scene.player, scene.opponent, scene.player.moves[0])
    scene._show(scene.messages[0])
    scene.state = scene.STATE_MESSAGE
    scene.draw(surface)  # mid-scroll, mid-effect
    view = scene.messages[0]
    offsets = {scene._sprite_offset(view, bs.HIT_OPPONENT)[:2] for _ in range(1)}
    assert offsets != {(0, 0)} or scene._sprite_offset(view, bs.HIT_OPPONENT)[2]
    scene.update(bs.EFFECT_TIME + 0.01)
    assert scene._sprite_offset(view, bs.HIT_OPPONENT) == (0, 0, True)
    # Other side never moves
    assert scene._sprite_offset(view, bs.HIT_PLAYER) == (0, 0, True)


def test_prompt_blinks_only_when_text_done(monkeypatch):
    monkeypatch.setattr(bs, "TEXT_CPS", 10)
    scene = _scene()
    calls = []
    monkeypatch.setattr(scene, "_draw_prompt", lambda s: calls.append(1))
    surface = pygame.Surface((240, 160))
    scene.draw(surface)
    assert not calls
    scene._text_pos = 999
    scene.draw(surface)
    assert calls
