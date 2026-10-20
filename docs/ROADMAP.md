# Open-Mon Roadmap

**Last updated:** 2026-10-20

## Where things stand

Open-Mon is an early prototype: one 30×21 tile map, three mascot species, one
trainer and placeholder art. In October 2026 the code was re-audited and the
core loop was fixed and put on firmer foundations:

- Battles: trainer parties switch mascots on faint, turns are narrated through
  a message queue (in `spd` order), HP is clamped, and capture, revive and item
  targeting work.
- Overworld: grid-based movement with facing, per-tile encounter rolls, a
  healer NPC, and trainers are only marked defeated when you win.
- Data: mascot species, the type chart and wild encounters are in
  `assets/mascots.yaml`; fonts are cached; tests can't touch the real save.

Not there yet: real sprites, sound, more than one map, progression (XP/levels),
and anything to do after beating Richard.

Each milestone is ordered by dependency. Do tasks roughly in order.

---

## Milestone 1: Playable slice

Goal: a 10-minute loop that feels like a game. Explore, catch, fight a trainer,
heal, save. With real art and sound.

### 1.1 Art pipeline and real sprites (mostly done)

Remaining: the pixel font, and real sprites for Gopher, Elephpant and Konqi. The rest below shipped 2026-10-20.

- Ship an OFL pixel font as `assets/sprites/pixel.ttf` (`fonts.get_font` already
  prefers it). The bold Arial fallback renders differently on every OS.
- Fix `scripts/svg2gb.py`: it is missing `import io` and outputs 16×16. Battle
  sprites need 32×32 (drawn at 2×); overworld sprites need 8×8.
- Create the `mascots/` SVG source dir the Makefile expects, or change the
  Makefile to the real location.
- Add a `sprite:` key to `assets/mascots.yaml`; `mascots.get_sprite` loads the
  PNG and falls back to the placeholder.
- Draw NPCs from their `sprite` field (currently ignored; drawn as circles),
  and give the player 4 facing frames (`Player.facing` exists).

**Done when:** `make assets` succeeds from a clean checkout and every mascot,
NPC and the player have a real sprite.

### 1.2 Roster and type chart (done; per-area encounters moved to 2.3)
- Grow from 3 to 6 species: add Gopher, Elephpant and Konqi (already named in the
  Makefile).
- Every type needs at least one species; Editor currently has none.
- The type chart has only 4 entries. Design a full matchup table (e.g. a
  Kernel → Shell → Browser → Editor → Kernel cycle) and document it in
  `docs/design.md`.
- Expand `wild_encounters` so grass areas differ (done in 2.3: per-map tables).

**Done when:** 6 species with 3–4 moves each, every type both strong and weak
against something, covered by a test that loads every species.

### 1.3 Audio (done; `beepbox2wav.py` unverified, apply saved mute at launch)
- Small `src/engine/audio.py` wrapper around `pygame.mixer` that is a no-op
  when audio init fails (CI, no device).
- Music per scene; SFX for menu move/confirm, hit, faint, capture.
- Battle SFX hook into the message queue: add an optional `sound` to
  `BattleMessage` and play it when that message is shown.
- `M` toggles mute; persist the setting in the save.
- Verify `scripts/beepbox2wav.py` and add `music/` sources.

### 1.4 Title, credits and the bag (done)
- Title menu: New Game / Continue (Continue only when a save exists).
- `CreditsScene` is an empty placeholder and unreachable; make it real.
- Pause menu entries: **Mascots** (party view) and **Bag** (use healing items
  outside battle; reuse the battle's party-target logic).

### 1.5 Battle feel (done)
- Done: damage is `power * atk / defense` scaled, with type multiplier and a
  seedable random factor (see `docs/design.md`).
- Done: typewriter text and a blinking "▼" prompt; Z completes scrolling text
  first. Hit flash/shake via `BattleMessage.effect`.
- Wild opponents keep picking moves at random; trainer AI comes in 2.2.

---

## Milestone 2: A world to explore

### 2.1 Progression: XP and levels
The biggest gap versus Pokemon Red/Blue: nothing grows. Add XP on win, levels,
stat growth per species and learnsets in `mascots.yaml`. Saved party states gain
`level`/`xp`; loading old saves defaults them.

### 2.2 Trainers that act like trainers
- Move choice: prefer super-effective and high-power moves.
- Line-of-sight challenge: a trainer spots you and walks up.
- Rewards (money, see 2.4) on win.

### 2.3 Multiple maps and warps (done)
- Maps live in `assets/maps/` (`<id>.csv` tiles + `<id>.yaml` with spawn,
  warps, NPCs and an optional encounter table); `town` and `route1` exist.
- Warps fade out/in on `OverworldScene._on_step_finished`; saves store `map`
  and defeated trainers as `map:npc_id`.
- Decide on Tiled `.tmx` (`pytmx`) once there are more than about 5 maps. CSV
  plus YAML is fine until then.

### 2.4 Items, money and a shop (done)
- Done: items in `assets/items.yaml` with prices, money in `InventoryManager`
  (saved, default 100), `ShopScreen`, shop NPC, trainer `reward`. Status
  cures still wait for status effects.
- Move item definitions out of `inventory.py` into YAML (same pattern as
  mascots).
- Money, a shop NPC, and new items (status cures once status effects exist).

### 2.5 Storage beyond the party
`PARTY_MAX` is 5 because the switch menu fits 5 rows. Add a "Repository"
storage box (Pokemon's PC) so captures beyond 5 aren't blocked.

### 2.6 Save versioning and slots
- Add `"version"` to save data and explicit migrations. The current
  format-sniffing for old saves is ad hoc.
- 3 save slots with a summary (location, party, play time).

---

## Milestone 3: Maintainer gyms

Needs M2 (maps, progression, trainer AI).

- 8 themed gyms ("maintainer gyms"), each with trainers and a leader whose
  party uses one type.
- Badges stored in the save; badge checks on warps gate progress.
- The final challenge: the "mainline merge".

---

## Later / maybe

Achievements, localization, an in-game map editor, itch.io/Steam packaging,
performance work (profile first; the game currently idles well under budget).

---

## Ongoing tech debt

Address these opportunistically when touching the code nearby:

- `OverworldScene` holds the HUD, pause menu, dialogue, save/load and
  encounters. Extract UI pieces as they grow.
- Cross-scene results are ad-hoc `SceneManager` attributes
  (`last_battle_party_states`, `battle_loss_reset`, `captured_mascot_name`,
  `last_battle_won`). If more outcomes appear, replace them with a single
  `BattleResult` object.
- Asset paths mix relative (`SPRITE_DIR`) and `__file__`-relative styles. Pick
  `__file__`-relative.
- `TileMap.draw` blits every tile each frame. That's fine at 30×21; cull to the
  camera once maps grow.
