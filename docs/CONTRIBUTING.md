# Contributing to Open-Mon

This guide is for human contributors and for AI agents given a task from
[ROADMAP.md](./ROADMAP.md).

## Setup and commands

Run everything from the repo root (some asset paths are relative).

```bash
pip install -r requirements.txt && pip install -e .
python -m src.engine.game        # play
pytest                           # tests (headless; conftest sets SDL dummy driver)
ruff check src/ tests/           # lint
black src/ tests/                # format (CI runs black --check)
pip install -e .[tools]          # cairosvg, only needed for `make assets`
```

CI runs ruff, black --check and pytest on every push and PR to `main`.

## How the code fits together

- **Scenes** (`src/engine/`): a stack in `SceneManager`; only the top scene gets
  events, updates and draws. Scenes are duck-typed (`handle_event`, `update`,
  `draw`).
- **Mascot data**: species, moves, the type chart and wild encounters live in
  `assets/mascots.yaml`. Use `src/engine/mascots.py` (`make_state`, `hydrate`,
  `make_mascot`, `get_sprite`); don't hardcode stats in scene code.
- **Party members are state dicts** (`name`, `hp`, `max_hp`, `atk`, `defense`,
  `spd`, `type`, `fainted`), so they serialize straight into saves.
- **Battle flow**: logic resolves a whole turn at once and queues
  `BattleMessage`s (text plus HP snapshot) with `_say()`. The screen plays them
  back one Z press at a time. Use `self.msg = ...` only for one-off feedback
  that isn't part of a turn ("You can't flee..."). Future animations and SFX
  belong on the queue.
- **Battle results** reach the overworld as a `BattleResult`
  (`src/engine/battle_result.py`) that `BattleScene._finish_battle` sets on
  `manager.battle_result` before `pop()`. `OverworldScene.update()` applies it
  and resets it to None. To add an outcome, add a defaulted field, fill it in
  `_finish_battle`, and consume it in `_apply_battle_result`.
- **Overworld** movement is grid-based (`src/overworld.py` `Player.try_step` /
  `update`). Gameplay hooks belong in `OverworldScene._on_step_finished`.
- **Text**: use `fonts.get_font(size)` and `fonts.wrap_text`; never build fonts
  in `draw()`.
- **Screen**: 240×160, 4-color `GB_PALETTE` from `src/constants.py`. Check that
  new UI fits: render the scene to a PNG headlessly and look at it.

## Tests

- Every bug fix gets a regression test; every feature gets tests for its rules.
- `tests/conftest.py` gives each test a fresh pygame display and a temporary
  `SAVE_PATH`. Don't write to `~/.openmon`.
- Each test file must pass on its own (`pytest tests/test_x.py`), not only as
  part of the full run.
- Drive scenes the way the game does (`handle_event` with KEYDOWN events,
  `update(dt)` with `dt` in **seconds**) rather than poking internals, where
  practical.

## Task brief template

Use this when handing a roadmap task to someone (or an agent):

```markdown
Task: <ROADMAP id and name>

Goal: <one or two sentences on the player-visible outcome>

Context:
- Relevant code: <files / functions>
- Patterns to follow: <e.g. mascots.yaml registry, BattleMessage queue>

Requirements:
- <specific, testable requirement>

Done when:
- <measurable acceptance criteria>
- New tests cover the change; pytest, ruff and black pass
- Docs updated (ROADMAP/backlog status, README if controls/features change)

Out of scope:
- <what not to touch>
```

When the work lands, move the task to **Done** in [backlog.md](./backlog.md).
