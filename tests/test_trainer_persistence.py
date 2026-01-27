"""
Test that defeated trainer state persists across save/load.
"""
import pygame
from src.engine.scene_manager import SceneManager
from src.engine.overworld_scene import OverworldScene


def test_trainer_defeated_state_saves_and_restores():
    """Test that defeated trainer status is saved and loaded correctly."""
    pygame.init()
    screen = pygame.display.set_mode((240, 160))

    # Create overworld scene
    manager = SceneManager()
    scene = OverworldScene(manager)

    # Find the trainer NPC
    trainer = None
    for npc in scene.npcs:
        if npc.trainer:
            trainer = npc
            break

    assert trainer is not None, "No trainer found in NPCs"
    initial_defeated_state = trainer.defeated

    # Mark trainer as defeated and save
    trainer.defeated = True
    defeated_trainer_id = trainer.id
    scene._save_game()

    # Create new scene and load
    scene2 = OverworldScene(manager)
    scene2._load_game()

    # Find trainer after load
    trainer_after_load = None
    for npc in scene2.npcs:
        if npc.id == defeated_trainer_id:
            trainer_after_load = npc
            break

    # Verify defeated state was restored
    assert trainer_after_load is not None, "Trainer not found after load"
    assert trainer_after_load.defeated is True, "Trainer defeated state should persist"

    # Clean up - restore initial state and save
    for npc in scene2.npcs:
        if npc.trainer:
            npc.defeated = initial_defeated_state
    scene2._save_game()

    pygame.quit()


def test_load_old_save_resets_trainer_state():
    """Test that loading an old save properly resets trainer defeated state."""
    pygame.init()
    screen = pygame.display.set_mode((240, 160))

    manager = SceneManager()
    scene = OverworldScene(manager)

    # Find trainer
    trainer = None
    for npc in scene.npcs:
        if npc.trainer:
            trainer = npc
            break

    assert trainer is not None
    initial_state = trainer.defeated

    # Step 1: Save with trainer undefeated
    scene._save_game()

    # Step 2: Defeat trainer (but don't save)
    trainer.defeated = True
    assert trainer.defeated is True

    # Step 3: Load old save (before defeat)
    scene._load_game()

    # Step 4: Trainer should be undefeated again
    assert trainer.defeated is False, "Loading old save should reset trainer to undefeated"
    assert trainer.is_trainer() is True, "Trainer should be able to battle again"

    # Clean up
    trainer.defeated = initial_state
    scene._save_game()

    pygame.quit()
