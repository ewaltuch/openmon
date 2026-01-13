# Open-Mon

A Game Boy–style RPG starring open-source mascots. Inspired by Pokémon Red/Blue.

## Features
- 160×144 px native resolution, 4-shade Game Boy palette
- Overworld, turn-based battles, capture, save/load
- Mascots: Tux, Octocat, BSD Daemon, Elephpant, Konqi, Gopher, and more

## Screenshots
![Title](docs/screenshots/title.png)
![Overworld](docs/screenshots/overworld.png)
![Battle](docs/screenshots/battle.png)


## Quickstart
```sh
pip install -r requirements.txt
python -m src.engine.game
```

## Controls

### Title Screen
- **Any Key** - Start game

### Overworld
- **Arrow Keys** (Up/Down/Left/Right) - Move your character
- **Space** - Interact with NPCs / Close dialogue
- **S** - Save your game
- **L** - Load your saved game

### Battle
- **Up/Down Arrow Keys** - Navigate menus
- **Z / Enter** - Confirm selection
- **X** - Cancel / Go back

#### Battle Menu Options
- **Fight** - Choose a move to attack the opponent
  - Each move has an elemental type (Kernel, Shell, Browser, Editor)
  - Type effectiveness affects damage (e.g., Kernel > Shell)
- **Item** - Use items from your inventory
  - **Package** - Attempt to capture a wild mascot (success rate increases when opponent HP is low)
  - **Health Pack** - Restore 20 HP to your active mascot
  - **Full Restore** - Fully restore HP to your active mascot
  - **Revive** - Revive a fainted mascot with half HP
- **Flee** - Escape from battle
- **Switch** - Change your active mascot (only available if you have multiple mascots in your party)

### Gameplay Tips
- Walk through **tall grass** to encounter wild mascots
- Capture mascots using **Packages** to add them to your party
- Save frequently to preserve your progress
- Talk to NPCs to learn more about the world
- Successfully captured mascots are automatically added to your party

## Saving and Loading
Your save file includes:
- Player position
- Party composition (captured mascots)
- Inventory (items and quantities)

Save files are stored in `~/.openmon/save1.json`

## License
- Code: MIT
- Assets: CC-BY-SA 4.0
