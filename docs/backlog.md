# Open-Mon Backlog & Task Board

**Last Updated:** 2026-01-22

## MVP Complete ✅
- [x] Core engine, scene manager, 60 FPS
- [x] Overworld: tile map, player, collision, camera
- [x] Battle: encounter, UI, capture
- [x] Save/load system
- [x] Asset/data pipeline
- [x] Unit tests & CI
- [x] Docs & backlog

## Milestone 1: Core Gameplay (~70% complete)
- [x] Multiple mascots, party system
- [x] More moves, elemental types (Kernel, Shell, Browser, Editor…)
- [x] NPCs, dialogue in YAML
- [x] Inventory, items, packages (Package, Health Pack, Full Restore, Revive)
- [x] Faint mechanics
- [x] Tall grass encounters
- [x] Battle UI polish (move info, HP display, type effectiveness, party menu)
- [x] Overworld UI (HUD, pause menu, notifications, hints)
- [ ] More maps, Tiled .tmx support
- [ ] Battle animations
- [ ] Sound effects, music
- [ ] Title/credits polish

## Milestone 2: Maintainer Gyms
- [ ] 8 "maintainer gyms"
- [ ] Gym leader AI
- [ ] Final "mainline merge"
- [ ] Achievements
- [ ] Save slots

## Milestone 3: Polish & Release
- [ ] Full mascot roster
- [ ] Map editor
- [ ] Localization
- [ ] Steam/itch.io release

---

## Active Tasks

| Task | Assigned To | Status | Priority | Notes |
|------|-------------|--------|----------|-------|
| - | - | - | - | - |

Status: `Not Started` | `In Progress` | `Blocked` | `In Review` | `Complete`

---

## Recent Completions

**2026-01-22:**
- ✅ **Task 2.2: Battle UI Improvements** (Gemini Code Assistant)
  - Added move power display (e.g., "Peck 6 PWR [Kernel]")
  - Enhanced HP bars (6px height) with numeric display
  - Added mascot names with types
  - Type effectiveness visual indicator with timer
  - **Bug Fix:** Party selection menu redesigned as full-screen overlay (supports 5 mascots)
  - **Bug Fix:** Switch mechanism freeze when mascot faints

- ✅ **Task 2.4: Overworld UI Enhancements** (Gemini Code Assistant)
  - Party status HUD in top-right corner
  - Pause menu (ESC) with Save/Load/Toggle Hints/Quit
  - Save/load notification system
  - On-screen control hints (toggleable)
  - **Bug Fix:** Control hints readability improved (font size 12)

---

## Ready to Start (Agent-Friendly Tasks)

See [ROADMAP.md](./ROADMAP.md) for detailed task descriptions.

### Priority 1: Can Start Immediately
- [ ] **Task 1.3: Audio System** - Implement sound effects and music with pygame.mixer
- [x] **Task 2.2: Battle UI Improvements** - Polish battle interface, add move info, better layout ✅
- [ ] **Task 3.1: Expand Mascot Roster** - Add 20+ mascots with stats and moves
- [x] **Task 2.4: Overworld UI Enhancements** - Add HUD, party status, pause menu ✅
- [ ] **Task 3.3: Item System Expansion** - Add more items, shop system
- [ ] **Task 4.4: Save Slot System** - Support 3 save files with metadata

### Priority 2: Quick Wins (< 1 day)
- [ ] Add battle damage number animations
- [ ] Create mascot sprite templates
- [ ] Design type effectiveness icons
- [ ] Write gym leader dialogue
- [ ] Add mute toggle (M key)
- [x] Add on-screen control hints ✅
- [x] Create save/load confirmation messages ✅
- [x] Design pause menu UI ✅

### Blocked (Waiting on Dependencies)
- [ ] **Task 1.1: Tiled Integration** - Optional, nice to have
- [ ] **Task 1.2: Multiple Maps** - Needs Task 1.1 decision
- [ ] **Task 2.1: Battle Animations** - Can start anytime
- [ ] **Task 3.2: Move/Type Expansion** - Needs Task 3.1 first
- [ ] **Task 4.1: Gym System** - Needs maps + content (Tasks 1.2, 3.1, 3.2)

---

## Quick Reference

### Task Categories
- **Maps & World**: Tasks 1.1, 1.2, 4.1
- **Audio**: Task 1.3, 2.3
- **Battle System**: Tasks 2.1, 2.2, 3.2, 4.2
- **Content**: Tasks 3.1, 3.3
- **UI/UX**: Tasks 2.2, 2.3, 2.4
- **Meta Systems**: Tasks 4.3, 4.4

### Current Sprint Goals
- [ ] Complete Audio System (Task 1.3)
- [x] Polish Battle UI (Task 2.2) ✅
- [ ] Expand Mascot Roster (Task 3.1)

---

For detailed task descriptions, subtasks, file lists, and acceptance criteria, see **[ROADMAP.md](./ROADMAP.md)**.
