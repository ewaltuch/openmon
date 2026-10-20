"""Items from YAML, money persistence, the shop and trainer rewards."""

import pygame
import pytest

from src.engine.battle_scene import BattleScene
from src.engine.inventory import STARTING_MONEY, InventoryManager, get_item
from src.engine.menu_screens import BagScreen, ShopScreen
from src.engine.overworld_scene import OverworldScene
from src.engine.save import SaveManager
from src.engine.scene_manager import SceneManager


def press(screen, key):
    screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))


def test_items_load_from_yaml():
    item = get_item("health_pack")
    assert item.effect == {"heal": 20}
    assert item.price > 0
    assert get_item("repo_key").type == "key"
    assert InventoryManager().get_item("revive").name == "Revive"


def test_unknown_item_raises():
    with pytest.raises(ValueError):
        get_item("nope")
    with pytest.raises(ValueError):
        ShopScreen(SceneManager(), InventoryManager(), ["nope"])


def test_buy_checks_money():
    inv = InventoryManager()
    price = get_item("health_pack").price
    inv.money = price * 2
    assert inv.buy("health_pack", 3) is False
    assert inv.money == price * 2
    assert inv.buy("health_pack", 2) is True
    assert inv.money == 0
    assert inv.get_item_count("health_pack") == 2


def test_sell_half_price_and_key_items_refused():
    inv = InventoryManager()
    inv.add_item("health_pack", 2)
    inv.add_item("repo_key")
    before = inv.money
    assert inv.sell("health_pack", 2) is True
    assert inv.money == before + 2 * (get_item("health_pack").price // 2)
    assert inv.sell("health_pack") is False  # none left
    assert inv.sell("repo_key") is False
    assert inv.has_item("repo_key")


def test_shop_screen_buy_and_sell_flow():
    inv = InventoryManager()
    shop = ShopScreen(SceneManager(), inv, ["health_pack"])
    price = get_item("health_pack").price
    press(shop, pygame.K_z)  # Buy
    press(shop, pygame.K_z)  # pick item
    press(shop, pygame.K_UP)  # qty 2
    press(shop, pygame.K_z)  # confirm
    assert inv.get_item_count("health_pack") == 2
    assert inv.money == STARTING_MONEY - 2 * price
    press(shop, pygame.K_x)  # back to main
    press(shop, pygame.K_DOWN)
    press(shop, pygame.K_z)  # Sell
    assert [i.id for i, _ in shop._entries()] == ["health_pack"]
    press(shop, pygame.K_z)
    press(shop, pygame.K_z)
    assert inv.get_item_count("health_pack") == 1
    shop.draw(pygame.display.get_surface())


def test_shop_sell_list_hides_key_items():
    inv = InventoryManager()
    inv.add_item("repo_key")
    shop = ShopScreen(SceneManager(), inv, ["package"])
    shop.buying = False
    assert shop._entries() == []


def test_shop_cannot_buy_when_broke():
    inv = InventoryManager()
    inv.money = 0
    shop = ShopScreen(SceneManager(), inv, ["package"])
    press(shop, pygame.K_z)
    press(shop, pygame.K_z)
    assert shop.mode == shop.MODE_LIST
    assert "money" in shop.message
    assert inv.get_item_count("package") == 0


def test_money_saves_and_old_saves_default():
    scene = OverworldScene(SceneManager())
    scene.inventory.money = 321
    scene._save_game()
    other = OverworldScene(SceneManager())
    other._load_game()
    assert other.inventory.money == 321

    data = SaveManager.load()
    del data["money"]
    SaveManager.save(data)
    other.inventory.money = 5
    other._load_game()
    assert other.inventory.money == STARTING_MONEY


def test_bag_draws_money():
    bag = BagScreen(SceneManager(), [], InventoryManager())
    bag.draw(pygame.display.get_surface())


def test_shop_npc_opens_shop():
    manager = SceneManager()
    scene = OverworldScene(manager)
    npc = next(n for n in scene.npcs if n.shop)
    assert scene.tilemap.is_walkable(npc.x, npc.y)
    scene.active_npc = npc
    scene.active_dialogue = "x"
    npc.dialogue_idx = len(npc.dialogue)
    press(scene, pygame.K_z)
    assert isinstance(manager.scenes[-1], ShopScreen)


def test_trainer_reward_paid_once_and_flag_cleaned():
    manager = SceneManager()
    scene = OverworldScene(manager)
    trainer = next(n for n in scene.npcs if n.trainer)
    assert trainer.reward > 0
    scene._pending_trainer = trainer
    before = scene.inventory.money
    manager.last_battle_party_states = scene.party
    manager.last_battle_won = True
    manager.last_battle_reward = trainer.reward
    scene.update(0.016)
    assert scene.inventory.money == before + trainer.reward
    assert not hasattr(manager, "last_battle_reward")
    scene.update(0.016)
    assert scene.inventory.money == before + trainer.reward


def _trainer_battle(manager, reward):
    helper = BattleScene(manager)
    return BattleScene(
        manager,
        party_states=[helper.make_mascot_state("Tux")],
        inventory=InventoryManager(),
        opponent_party=[helper.hydrate_mascot(helper.make_mascot_state("Octocat"))],
        is_trainer_battle=True,
        reward=reward,
    )


def test_battle_sets_reward_only_on_win():
    manager = SceneManager()
    battle = _trainer_battle(manager, 50)
    battle.opponent.hp = 0
    battle._finish_battle()
    assert manager.last_battle_reward == 50

    manager = SceneManager()
    battle = _trainer_battle(manager, 50)
    battle.player.hp = 0
    battle._finish_battle()
    assert not hasattr(manager, "last_battle_reward")
