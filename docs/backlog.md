# Open-Mon Backlog

**Last updated:** 2026-10-20. Task details are in [ROADMAP.md](./ROADMAP.md).

## Next up (triaged 2026-10-20, in order)

| # | Task | Size | Why now / notes |
|---|------|------|-----------------|
| 1.3 (rest) | Apply saved `muted` at launch; verify `beepbox2wav.py` | S | Small bug-class fix: mute only applies after loading |
| 2.1 (rest) | Player prompt for which move to forget; XP bar | S | Auto-forgetting the oldest move is a gameplay wart |
| 2.2 | Trainer AI (effective/high-power moves), line-of-sight challenge | M | Unblocks Milestone 3; rewards already done |
| 2.5 | Repository storage box | M | Captures past 5 are currently blocked; touches party/battle capture |
| 2.3 (rest) | Interior map (house/shop) and a second trainer | S | Content, exercises warps; cheap |
| 2.6 | Save versioning and 3 slots | M | Do last in M2: save format now stable (map, money, level, xp) |
| 1.1 (rest) | Pixel font; art for Gopher/Elephpant/Konqi | S-M | Blocked: needs a verified OFL font and artwork; can run in parallel any time |

Then Milestone 3 (gyms), which needs 2.2 and 2.6. Parallelism: 2.2 and 2.5 touch
different files and can run together; 2.6 should follow them.
Tech debt worth doing soon: replace the ad-hoc `SceneManager` result attributes
(now five of them) with a `BattleResult` object, ideally before 2.2/2.5 add more.

## In progress

None.

## Done

**2.1 Progression: XP and levels**
- State dicts carry `level`/`xp`; stats = species base (level 5) + `growth` per level; `learnset` (level -> move, newest 4 kept); wild levels in `wild_encounters`, trainer party entries may be `{name, level}`
- XP split among live participants, trainer bonus x1.5, level-up messages with `levelup` SFX; old saves default to level 5 / xp 0
- Not done: evolutions, move-forget prompt (oldest is replaced automatically), XP bar in the UI

**1.5 Battle feel**
- Pokemon-like damage formula (seedable), typewriter text with blinking prompt, hit flash/shake via `BattleMessage.effect`

**2.4 Items, money and a shop**
- Items in `assets/items.yaml` (with prices), money saved/loaded and shown in HUD and Bag, `ShopScreen` (buy/sell at half, no key items), shop NPC Grace, trainer `reward` via `last_battle_reward`

**2026-10-20: 2.3 Multiple maps and warps**
- `assets/maps/` with town and route1 (CSV + YAML), fade warps both ways, per-map encounter tables, `map` in saves (old saves load into town), defeated trainers keyed `map:npc_id`

**2026-10-20: Milestone 1 mostly landed**
- 1.1 SVG→PNG pipeline works (`make assets`), mascot/NPC/player sprites (font and 3 new species' art outstanding)
- 1.2 Roster of 6, full type cycle, `docs/design.md` (per-area encounter tables wait for 2.3)
- 1.3 Audio module, per-scene music, SFX via `BattleMessage.sound`, mute; saved mute applied at launch; stale beepbox2wav script removed (music is generated in code)
- 1.4 Title menu with Continue, credits, Mascots and Bag pause screens
- Fixed ruff CI errors

**2026-10-18: re-audit and stabilization**
- Trainer battles switch to the next mascot on faint; trainer defeated only on a win
- Battle turns narrated via a message queue; turn order by `spd`
- Battle screen re-laid out to fit 240×160 (menus no longer run off-screen)
- HP clamped at 0; capture adds a full-HP mascot; party capped at 5
- Items target a party member; Revive works; heals don't affect fainted mascots
- Grid movement with facing; encounters per grass tile; walls block on all sides
- Healer NPC (Linus); Ada moved off the wall
- Mascot data in `assets/mascots.yaml` (species, type chart, wild encounters)
- Font cache; tests isolated from the real save file and from each other

**Earlier (prototype)**
- Scene stack, overworld, battles, capture, party switching, inventory,
  NPC dialogue in YAML, one trainer, save/load, HUD and pause menu, CI
