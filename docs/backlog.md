# Open-Mon Backlog

**Last updated:** 2026-10-20. Task details are in [ROADMAP.md](./ROADMAP.md).

## Next up (in order)

| # | Task | Notes |
|---|------|-------|
| 1.1 (rest) | Pixel font; real sprites for Gopher/Elephpant/Konqi | No verified OFL font source yet |
| 1.5 | Battle feel | Damage formula review |

Then Milestone 2, starting with **2.1 Progression (XP and levels)**.

## In progress

None.

## Done

**2026-10-20: Milestone 1 mostly landed**
- 1.1 SVG→PNG pipeline works (`make assets`), mascot/NPC/player sprites (font and 3 new species' art outstanding)
- 1.2 Roster of 6, full type cycle, `docs/design.md` (per-area encounter tables wait for 2.3)
- 1.3 Audio module, per-scene music, SFX via `BattleMessage.sound`, mute (`beepbox2wav.py` unverified; mute only applied on load)
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
