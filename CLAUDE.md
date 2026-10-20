# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open-Mon is a Game Boy-style RPG featuring open-source mascots (Tux, Octocat, BSD Daemon, etc.), inspired by Pokemon Red/Blue. Built with Pygame, targeting 240x160 resolution with a 4-shade Game Boy palette.

## Commands

### Running the game
```bash
python -m src.engine.game
```

### Setup
```bash
pip install -r requirements.txt
```

### Testing
```bash
pytest                          # Run all tests
pytest tests/test_battle.py     # Run specific test file
pytest tests/test_battle.py::test_name   # Run a single test
pytest -k "trainer"             # Run tests matching a keyword
pytest -v                       # Verbose output
```
Run commands from the repo root: asset paths in `src/constants.py` are relative (`assets/...`), and CI does `pip install -e .` so `src.*` imports resolve. Locally the venv is `myenv/` (`myenv/bin/python -m pytest`). `tests/conftest.py` makes tests headless, gives every test a fresh pygame display, and redirects `SAVE_PATH` to a tmp dir, so tests never touch `~/.openmon`.

### Linting & Formatting
```bash
ruff check src/ tests/          # Lint
black --check src/ tests/       # Format check (drop --check to auto-format)
```
CI (`.github/workflows/ci.yml`) runs ruff, black --check, and pytest on every push/PR to `main`.

### Asset Pipeline
```bash
make assets                     # Build all sprites and audio assets
```

The Makefile converts SVG mascot graphics to Game Boy-style PNGs (`scripts/svg2gb.py`). SVG sources live in `mascots/` (32x32 battle sprites) and `mascots/overworld/` (8x8 NPC and player-facing sprites); the generated PNGs are committed so the game and CI don't need to build them. `svg2gb.py` takes `input.svg output.png [size]`. There is no `music/` source dir: audio is generated in code (`src/engine/audio.py`). `cairosvg` is in the optional `tools` extra (`pip install -e .[tools]`). The game doesn't need it to run.

## Architecture

### Scene-Based State Machine

The game uses a stack-based scene manager (`src/engine/scene_manager.py`) that pushes/pops scenes:

- **TitleScene** - Entry point, shows title screen
- **OverworldScene** - Top-down exploration with tile map, player movement, NPCs, and random encounters
- **BattleScene** - Turn-based battles with moves, type effectiveness, and capture mechanics
- **CreditsScene** - Scrollable credits, reached from the title menu (New Game / Continue / Credits)

The SceneManager maintains a stack where the top scene receives events and updates. Scenes can push new scenes on top (e.g., transitioning from overworld to battle) or pop themselves to return to the previous scene. Scenes are duck-typed (`handle_event`/`update`/`draw`, constructed with the manager); only `TitleScene`/`CreditsScene` subclass the `Scene` base in `scenes.py`. Quitting from the overworld pause menu replaces the stack outright (`manager.scenes = [TitleScene(...)]`).

**Cross-scene state passing**: Scenes don't return values. `BattleScene._finish_battle` builds one `BattleResult` (`src/engine/battle_result.py`), sets it as `manager.battle_result`, then pops. `OverworldScene.update()` applies it (`_apply_battle_result`) and resets `manager.battle_result = None`. Fields:
- `party_states`: the party's HP/state (incl. xp/level) after battle; on a loss, revived to full HP
- `lost`: whole player party fainted, so the player is moved back to spawn
- `won`: whole opponent party fainted; the overworld marks its `_pending_trainer` defeated only then
- `reward`: money for a trainer win (`reward` on the NPC); only paid when `won`
- `captured_name`: the capture is already in `party_states` (at full HP); the overworld only adds it itself if no party sync came with it

To add a battle outcome, add a field with a default to `BattleResult`, fill it in `_finish_battle`, and consume it in `_apply_battle_result`. No per-field cleanup is needed.

### Core Engine Loop

`src/engine/game.py` contains the main game loop:
1. Initialize pygame and scene manager
2. 60 FPS game loop
3. Event handling -> Scene update -> Scene draw -> Display flip

### Overworld System

The overworld (`src/engine/overworld_scene.py` and `src/overworld.py`) consists of:

- **TileMap**: CSV-based tile grid (0=floor, 1=wall, 2=tall grass); `tile_at`/`is_walkable`
- **Player**: grid-based, Pokemon-style. `try_step(direction, tilemap, is_blocked)` starts a one-tile step, `update(dt)` slides toward it and returns True when the step ends; `facing`/`facing_tile()`/`place(tx, ty)`
- **Camera**: Follows player, bounded to the tilemap's size
- **Encounter system**: `OverworldScene._on_step_finished` counts grass tiles entered; reaching `encounter_steps` pushes a wild battle (species rolled from `wild_encounters`)
- **Interaction**: Z/Space talks to the NPC on the faced tile only; movement and S/L are blocked while dialogue is open
- **Party system**: List of mascot state dicts (built via `mascots.make_state`, which includes `level`/`xp`) that persists across battles and saves
- **Maps and warps**: `assets/maps/<id>.csv` + `<id>.yaml` (spawn, warps, NPCs, optional `encounters`), loaded by `src/engine/maps.py` (`load_map`). Stepping on a warp tile fades out/in via `OverworldScene.start_warp`/`enter_map`; maps without `encounters` fall back to `wild_encounters` in `mascots.yaml`. Maps: `town`, `route1`

NPCs are loaded from each map's YAML (`assets/maps/*.yaml`) with position, sprite reference, and multi-line dialogue sequences. NPCs can also be trainers (`trainer: true` with a `party` list of mascot names or `{name, level}` entries, and optional `reward` money): talking to an undefeated trainer starts a battle (`is_trainer_battle=True` on `BattleScene`) against their party instead of a dialogue-only interaction. Defeated state persists per-NPC and is saved/restored like the rest of game state. NPCs with `heals: true` (Linus) fully heal the party when their dialogue ends. NPCs with `shop: true` and a `stock` list (Grace) open a `ShopScreen` after dialogue.

### Battle System

Turn-based combat (`src/engine/battle_scene.py`) features:

- **Species registry** (`src/engine/mascots.py` + `assets/mascots.yaml`): species stats/moves/placeholder sprites, `TYPE_EFFECTIVENESS`, `wild_encounters`. `make_state`, `hydrate`, `make_mascot`, cached `get_sprite(name, scale)`. Unknown species raise `ValueError`. `BattleScene.make_mascot*`/`hydrate_mascot` are thin wrappers kept for callers/tests; `Mascot`, `Move`, `TYPE_EFFECTIVENESS` are re-exported from `battle_scene`
- **Message queue**: turn logic resolves immediately (HP changes at once), and every step is queued with `_say(text)` as a `BattleMessage` (text + HP snapshot) that the player advances with Z; `draw()` shows the snapshot of the current message. After the queue empties the scene goes to `_next_state` or finishes the battle. `self.msg = ...` is for one-off status lines outside a turn; `msg` reads the latest text either way
- **Turn order**: higher `spd` acts first (ties: player)
- **Item targeting**: consumables open the party menu (`pending_item`); revive targets fainted mascots and clears `fainted`
- **Type effectiveness**: Rock-paper-scissors style matchups (Kernel > Shell, Browser > Editor, etc.)
- **Capture mechanics**: Package item with probability based on opponent HP; capped at `PARTY_MAX` (5, what the switch menu fits); duplicates allowed
- **Move learning**: a full moveset (4) prompts via `STATE_FORGET` (the message carries `learn=(mascot, move)`; the new move is the last row, X declines). The chosen moveset is saved as `moves` (names) in the party state; `hydrate` falls back to the learnset-derived moves when absent. The player info box has an XP bar (`mascots.xp_fraction`)
- **Party switching**: Can switch active mascot mid-battle if party has multiple members
- **Trainer battles**: NPC-initiated battles against a multi-mascot opponent party (`is_trainer_battle=True`); captures are disabled and the opponent auto-switches on faint instead of the battle ending

Battle flow: intro message -> Menu (2x2 grid: Fight/Item/Flee/Switch) -> action -> turn resolved and narrated via the message queue -> back to menu, forced switch, or battle end on the last message.

Battle results reach the overworld through SceneManager attributes (see "Cross-scene state passing" above).

### Inventory System

`src/engine/inventory.py` loads `Item` definitions (with `price`) from `assets/items.yaml` (unknown ids raise `ValueError`) and defines `Item` (consumable/key/package types with an `effect` dict, e.g. `{"heal": 20}`) and `InventoryManager`, which also holds `money` and tracks `{item_id: quantity}` and is the source of truth for what the battle Item menu can use. Serialized via `to_dict()`/`from_dict()` as part of save data.

### Save/Load System

JSON-based persistence (`src/engine/save.py`):
- Press **S** in overworld to save
- Press **L** to load
- Saves player position, party composition, inventory, and defeated trainers (keyed `map:npc_id`), current map, money and mute; old saves without `map`/`money`/`level` get defaults; loading snaps the position to the grid (spawn if the tile is blocked)
- `SaveManager` reads `constants.SAVE_PATH` at call time, so it can be monkeypatched
- Default path: `~/.openmon/save1.json` (`SAVE_PATH` is relative and `SaveManager` puts it under `~`)

### Constants and Palette

All game constants live in `src/constants.py`:
- Screen dimensions (240x160), `PARTY_MAX`
- 4-color Game Boy palette: lightest to darkest
- Asset directory paths
- Save file path

### Asset Management

- **Sprites**: 8x8 tiles, 32x32 mascots (drawn at 2x in battle), currently PIL placeholders
- **Tile size**: 8x8 pixels
- **Map**: CSV tile grid + YAML per map in `assets/maps/`
- Mascot sprites: species with a `sprite:` key in `assets/mascots.yaml` load that PNG via `mascots.get_sprite`; others fall back to the generated `placeholder` (Gopher, Elephpant, Konqi still do). NPCs draw from their `sprite` field (`overworld.load_overworld_sprite`, circle fallback) and the player has 4 facing frames
- **Audio**: `src/engine/audio.py` wraps `pygame.mixer` (lazy init, every call a no-op if the mixer fails). Music per scene (`title`/`overworld`/`battle`), SFX generated in code. `BattleMessage` has an optional `sound` played when the message is shown. `M` toggles mute, saved as `muted` in the save
- **Menus**: `src/engine/menu_screens.py` has `PartyScreen` (Mascots) and `BagScreen` (use items outside battle), pushed from the pause menu
- **Fonts**: always use `src/engine/fonts.py` (`get_font(size)` cached, `wrap_text`); prefers `assets/sprites/pixel.ttf` (not shipped yet) and falls back to bold Arial

## Project Planning

- **[docs/ROADMAP.md](docs/ROADMAP.md)**: milestones and tasks in dependency order, with acceptance criteria and a tech-debt list
- **[docs/backlog.md](docs/backlog.md)**: what's next, in progress, and done
- **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)**: conventions, test expectations, and a task brief template for delegating work

## Development Notes

### Element Types

The game uses custom element types instead of traditional Pokemon types:
- Kernel
- Shell
- Browser
- Editor

Type effectiveness is defined under `type_effectiveness` in `assets/mascots.yaml` (loaded into `mascots.TYPE_EFFECTIVENESS`); unlisted pairs are 1.0. Roster: 6 species, covering all four types; the chart is a Kernel > Shell > Browser > Editor > Kernel cycle (see `docs/design.md`).

### Testing

Tests are organized by module:
- `test_engine.py` - Scene manager and game loop
- `test_overworld.py` - Player movement and collision
- `test_battle.py` - Battle mechanics and type effectiveness
- `test_save.py` - Save/load system
- `test_rng.py` - Random encounter logic
- `test_inventory.py` - Item effects and InventoryManager
- `test_hp_persistence.py` - Party HP persists across battles/saves
- `test_party_ui.py` - Party/switch menu rendering and selection
- `test_trainer_battle.py` - Trainer battle flow (multi-mascot opponent, no capture)
- `test_trainer_persistence.py` - Defeated-trainer state saved/restored
- `test_sprites.py` - SVG pipeline, species/NPC/player sprites
- `test_audio.py` - audio no-ops, mute, battle sounds
- `test_menus.py` - title, credits, party and bag screens
- `test_battle_feel.py` - damage formula, typewriter text, hit effects
- `test_progression.py` - XP, levels, learnsets, old-save defaults
- `test_maps.py` - map loading, warps, fade, per-map encounters
- `test_shop.py` - items.yaml, money, buy/sell, trainer rewards
- `conftest.py` - headless pygame per test, tmp `SAVE_PATH`; each file must pass in isolation

### Python Version

Requires Python 3.12+ (see pyproject.toml).

### Code Style

Configured for Black and Ruff with 88 character line length.
