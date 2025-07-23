"""
Save/load system for Open-Mon. Serializes party, inventory, position to JSON.
"""
import os
import json
from src.constants import SAVE_PATH

class SaveManager:
    @staticmethod
    def save(game_state):
        os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
        with open(os.path.expanduser(f"~/{SAVE_PATH}"), "w") as f:
            json.dump(game_state, f, indent=2)

    @staticmethod
    def load():
        try:
            with open(os.path.expanduser(f"~/{SAVE_PATH}"), "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
