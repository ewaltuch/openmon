# Open-Mon

A Game Boy–style RPG starring open-source mascots. Inspired by Pokémon Red/Blue.

## Features
- 240×160 px native resolution, 4-shade Game Boy palette
- Grid-based overworld, turn-based battles, capture, trainers, save/load
- Mascots so far: Tux, BSD Daemon, Octocat (more planned; see [docs/ROADMAP.md](docs/ROADMAP.md))

Early prototype: placeholder art, one map, no sound yet.

## Quickstart
```sh
pip install -r requirements.txt
python -m src.engine.game
```

## Controls

### Title Screen
- **Any Key** - Start game

### Overworld
- **Arrow Keys** - Walk one tile at a time
- **Z / Space** - Talk to the NPC you're facing / advance dialogue
- **S** - Save your game
- **L** - Load your saved game
- **Esc** - Pause menu

### Battle
- **Arrow Keys** - Navigate menus
- **Z / Enter** - Confirm selection / advance messages
- **X** - Cancel / Go back

#### Battle Menu Options
- **Fight** - Choose a move to attack the opponent
  - Each move has an elemental type (Kernel, Shell, Browser, Editor)
  - Type effectiveness affects damage (e.g., Kernel > Shell)
  - The faster mascot attacks first
- **Item** - Use items from your inventory
  - **Package** - Attempt to capture a wild mascot (success rate increases when opponent HP is low)
  - **Health Pack** - Restore 20 HP to a party mascot
  - **Full Restore** - Fully restore HP to a party mascot
  - **Revive** - Revive a fainted mascot with half HP
- **Flee** - Escape from a wild battle (not from trainers)
- **Switch** - Change your active mascot (only available if you have multiple mascots in your party)

### Gameplay Tips
- Walk through **tall grass** to encounter wild mascots
- Capture mascots using **Packages** to add them to your party (up to 5)
- Talk to **Linus** to heal your party
- **Richard** is a trainer: beat his whole party to win
- Losing every mascot sends you back to the start with a healed party

## Saving and Loading
Your save file includes:
- Player position
- Party composition (captured mascots)
- Inventory (items and quantities)
- Which trainers you've defeated

Save files are stored in `~/.openmon/save1.json`

## Contributing
See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) and [docs/ROADMAP.md](docs/ROADMAP.md).

## License
- Code: MIT
- Assets: CC-BY-SA 4.0
