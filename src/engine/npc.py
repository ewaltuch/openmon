import yaml


class NPC:
    def __init__(
        self,
        id,
        name,
        x,
        y,
        sprite,
        dialogue,
        trainer=False,
        party=None,
        defeated=False,
        defeated_dialogue=None,
        heals=False,
        reward=0,
        shop=False,
        stock=None,
        facing="down",
        sight=4,
    ):
        self.id = id
        self.name = name
        self.x = x
        self.y = y
        self.home = (x, y)  # where a trainer returns to after walking up
        self.sprite = sprite
        self.dialogue = dialogue
        self.defeated_dialogue = (
            defeated_dialogue or dialogue
        )  # Fallback to regular dialogue if none provided
        self.dialogue_idx = 0
        self.trainer = trainer
        self.party = party or []  # Mascot names or {name, level} for trainers
        self.defeated = defeated  # Track if trainer has been beaten
        self.heals = heals  # Restores the party after talking
        self.reward = reward  # Money awarded for beating this trainer
        self.shop = shop  # Opens a ShopScreen after talking
        self.stock = stock or []  # Item ids on sale
        self.facing = facing  # Direction a trainer looks (and spots you along)
        self.sight = sight  # Tiles a trainer can see ahead

    def talk(self):
        # Use defeated dialogue if trainer has been beaten
        active_dialogue = (
            self.defeated_dialogue
            if (self.trainer and self.defeated)
            else self.dialogue
        )

        if self.dialogue_idx < len(active_dialogue):
            msg = active_dialogue[self.dialogue_idx]
            self.dialogue_idx += 1
            return msg
        else:
            self.dialogue_idx = 0
            return None

    def is_trainer(self):
        """Check if this NPC is a trainer who can battle."""
        return self.trainer and not self.defeated


def load_npcs(yaml_path):
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    return [NPC(**npc) for npc in data]
