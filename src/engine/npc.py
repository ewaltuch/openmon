import yaml
import os

class NPC:
    def __init__(self, id, name, x, y, sprite, dialogue):
        self.id = id
        self.name = name
        self.x = x
        self.y = y
        self.sprite = sprite
        self.dialogue = dialogue
        self.dialogue_idx = 0

    def talk(self):
        if self.dialogue_idx < len(self.dialogue):
            msg = self.dialogue[self.dialogue_idx]
            self.dialogue_idx += 1
            return msg
        else:
            self.dialogue_idx = 0
            return None


def load_npcs(yaml_path):
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    return [NPC(**npc) for npc in data]
