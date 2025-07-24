"""
Save/load system for Open-Mon. Serializes party, inventory, position to JSON.
"""
import os
import json
from src.constants import SAVE_PATH

class SaveManager:
    @staticmethod
    def save(game_state):
        # If SAVE_PATH is absolute, use as is; else, prepend home dir
        path = SAVE_PATH
        if not os.path.isabs(path):
            path = os.path.expanduser(f"~/{path}")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(game_state, f, indent=2)

    @staticmethod
    def load():
        path = SAVE_PATH
        if not os.path.isabs(path):
            path = os.path.expanduser(f"~/{path}")
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
