"""
Save/load system for Open-Mon. Serializes party, inventory, position to JSON.
"""

import json
import os

from src import constants


def _save_path():
    # Read SAVE_PATH at call time so it can be redirected (e.g. in tests).
    # If it's absolute, use as is; else, put it under the home dir
    path = constants.SAVE_PATH
    if not os.path.isabs(path):
        path = os.path.expanduser(f"~/{path}")
    return path


class SaveManager:
    @staticmethod
    def save(game_state):
        path = _save_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(game_state, f, indent=2)

    @staticmethod
    def load():
        try:
            with open(_save_path()) as f:
                return json.load(f)
        except FileNotFoundError:
            return None
