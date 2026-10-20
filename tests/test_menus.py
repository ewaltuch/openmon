"""Title menu, credits, and the pause-menu Mascots/Bag screens."""

import pygame

from src.engine.menu_screens import BagScreen, PartyScreen
from src.engine.overworld_scene import OverworldScene
from src.engine.save import SaveManager
from src.engine.scene_manager import SceneManager
from src.engine.scenes import CreditsScene, TitleScene


def press(mgr, key):
    mgr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))


def make_title():
    mgr = SceneManager()
    mgr.push(TitleScene(mgr))
    return mgr


def make_overworld():
    mgr = SceneManager()
    ow = OverworldScene(mgr)
    mgr.push(ow)
    return mgr, ow


def open_pause_entry(mgr, ow, name):
    press(mgr, pygame.K_ESCAPE)
    ow.pause_menu_idx = ow.pause_menu_options.index(name)
    press(mgr, pygame.K_z)


def select_item(bag, item_id):
    bag.item_idx = [i.id for i, _ in bag.inventory.get_all_items()].index(item_id)


def test_title_without_save_has_no_continue():
    mgr = make_title()
    assert mgr.scenes[-1].options == ["New Game", "Credits"]


def test_new_game_starts_overworld():
    mgr = make_title()
    press(mgr, pygame.K_z)
    assert isinstance(mgr.scenes[-1], OverworldScene)


def test_credits_reachable_and_returns():
    mgr = make_title()
    press(mgr, pygame.K_DOWN)
    press(mgr, pygame.K_z)
    assert isinstance(mgr.scenes[-1], CreditsScene)
    press(mgr, pygame.K_ESCAPE)
    assert isinstance(mgr.scenes[-1], TitleScene)
    press(mgr, pygame.K_z)  # re-enter credits via Z, leave via Z
    press(mgr, pygame.K_z)
    assert isinstance(mgr.scenes[-1], TitleScene)


def test_continue_loads_save():
    _, ow = make_overworld()
    ow.party[0]["hp"] = 3
    ow.inventory.add_item("revive", 2)
    ow._save_game()
    mgr = make_title()
    assert mgr.scenes[-1].options == ["New Game", "Continue", "Credits"]
    press(mgr, pygame.K_DOWN)
    press(mgr, pygame.K_z)
    loaded = mgr.scenes[-1]
    assert isinstance(loaded, OverworldScene)
    assert loaded.party[0]["hp"] == 3
    assert loaded.inventory.get_item_count("revive") == 2


def test_pause_mascots_screen_opens_and_closes():
    mgr, ow = make_overworld()
    open_pause_entry(mgr, ow, "Mascots")
    assert isinstance(mgr.scenes[-1], PartyScreen)
    press(mgr, pygame.K_x)
    assert mgr.scenes[-1] is ow


def test_bag_heals_chosen_member_and_persists():
    mgr, ow = make_overworld()
    ow.party[1]["hp"] = 1
    before = ow.inventory.get_item_count("health_pack")
    open_pause_entry(mgr, ow, "Bag")
    bag = mgr.scenes[-1]
    assert isinstance(bag, BagScreen)
    select_item(bag, "health_pack")
    press(mgr, pygame.K_z)
    assert bag.mode == BagScreen.MODE_TARGET
    assert bag.target_idx == 1  # only the hurt member is selectable
    press(mgr, pygame.K_z)
    assert ow.party[1]["hp"] == 21
    assert ow.inventory.get_item_count("health_pack") == before - 1
    ow._save_game()
    assert SaveManager.load()["party"][1]["hp"] == 21


def test_bag_revive_only_targets_fainted():
    mgr, ow = make_overworld()
    ow.inventory.add_item("revive")
    ow.party[0]["hp"] = 0
    ow.party[0]["fainted"] = True
    open_pause_entry(mgr, ow, "Bag")
    bag = mgr.scenes[-1]
    select_item(bag, "revive")
    press(mgr, pygame.K_z)
    assert bag.target_idx == 0
    press(mgr, pygame.K_z)
    assert ow.party[0]["hp"] == ow.party[0]["max_hp"] // 2
    assert ow.party[0]["fainted"] is False


def test_bag_no_valid_target_keeps_item():
    mgr, ow = make_overworld()
    open_pause_entry(mgr, ow, "Bag")
    bag = mgr.scenes[-1]
    select_item(bag, "health_pack")
    press(mgr, pygame.K_z)
    assert bag.mode == BagScreen.MODE_ITEMS
    assert "no effect" in bag.message
    assert ow.inventory.get_item_count("health_pack") == 3


def test_screens_render_at_native_size(tmp_path):
    mgr, ow = make_overworld()
    ow.party[1]["hp"] = 1
    target = BagScreen(mgr, ow.party, ow.inventory)
    select_item(target, "health_pack")
    press_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z)
    target.handle_event(press_event)
    shots = {
        "title": TitleScene(mgr),
        "credits": CreditsScene(mgr),
        "party": PartyScreen(mgr, ow.party),
        "bag": BagScreen(mgr, ow.party, ow.inventory),
        "bag_target": target,
    }
    for name, scene in shots.items():
        surf = pygame.Surface((240, 160))
        scene.draw(surf)
        pygame.image.save(surf, str(tmp_path / f"{name}.png"))
        assert surf.get_size() == (240, 160)
