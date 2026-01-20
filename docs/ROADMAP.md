# Open-Mon Development Roadmap

**Last Updated:** 2026-01-20

## Project Status Overview

### ✅ Completed Features (MVP + Milestone 1 Core)
- Core engine with scene manager running at 60 FPS
- Overworld with tile map, player movement, collision detection, camera system
- Turn-based battle system with type effectiveness
- Mascot capture mechanics with probability based on HP
- Party system with multiple mascots and switching
- Full inventory system (Package, Health Pack, Full Restore, Revive)
- Faint mechanics for mascots in battle
- NPC system with YAML-based dialogue
- Tall grass random encounters
- Save/load system with JSON persistence
- Unit tests with pytest
- Asset pipeline with Makefile
- Documentation (README, CLAUDE.md, design docs)

### 🚧 Current Milestone: Milestone 1 - Core Gameplay Polish

**Progress:** ~60% complete

#### Remaining Tasks:
- [ ] More maps and Tiled .tmx support
- [ ] Battle UI polish and animations
- [ ] Sound effects and music system
- [ ] Title/credits scene polish

---

## Task Breakdown for Agent Delegation

### Priority 1: Critical Gameplay Features

#### Task 1.1: Tiled Map Editor Integration
**Complexity:** Medium | **Estimated Scope:** 3-5 files | **Dependencies:** None

**Objective:** Replace CSV tile maps with Tiled .tmx format for easier map creation

**Subtasks:**
- [ ] Research and add pytmx library to requirements.txt
- [ ] Create TiledMapLoader class in `src/engine/tiled_loader.py`
- [ ] Update OverworldScene to support .tmx files
- [ ] Convert existing CSV map to .tmx format
- [ ] Add collision layer support
- [ ] Add object layer support for NPC spawn points
- [ ] Update tests to cover .tmx loading
- [ ] Document map creation workflow in CLAUDE.md

**Files to modify:**
- `requirements.txt`
- `src/engine/overworld_scene.py`
- `src/overworld.py` (TileMap class)
- New: `src/engine/tiled_loader.py`
- `tests/test_overworld.py`

**Acceptance Criteria:**
- Load .tmx files exported from Tiled editor
- Support multiple tile layers
- Collision detection works with Tiled collision layer
- NPCs can be placed via object layer
- Existing save files remain compatible

---

#### Task 1.2: Multiple Maps and Map Transitions
**Complexity:** Medium | **Estimated Scope:** 4-6 files | **Dependencies:** Task 1.1 (nice to have)

**Objective:** Support multiple map areas with transitions between them

**Subtasks:**
- [ ] Design map transition system (warp tiles, door triggers)
- [ ] Create MapManager class to handle multiple maps
- [ ] Implement map loading/unloading
- [ ] Add transition tiles to TileMap
- [ ] Create transition animations (fade out/in)
- [ ] Update save system to persist current map
- [ ] Create 2-3 additional map areas
- [ ] Add door/warp interactions
- [ ] Test party persistence across map transitions
- [ ] Update documentation

**Files to modify:**
- `src/engine/overworld_scene.py`
- `src/overworld.py`
- `src/engine/save.py`
- New: `src/engine/map_manager.py`
- `tests/test_overworld.py`
- `tests/test_save.py`

**Acceptance Criteria:**
- Player can transition between at least 3 maps
- Map state is saved/loaded correctly
- Party and inventory persist across transitions
- Smooth transition animations
- No performance issues during map switches

---

#### Task 1.3: Audio System Foundation
**Complexity:** Medium-High | **Estimated Scope:** 5-7 files | **Dependencies:** None

**Objective:** Implement sound effects and background music system

**Subtasks:**
- [ ] Create AudioManager class with pygame.mixer
- [ ] Implement music playback with looping
- [ ] Implement sound effect playback
- [ ] Add volume controls
- [ ] Create music tracks for:
  - Title screen
  - Overworld
  - Battle
  - Victory
- [ ] Add sound effects for:
  - Menu navigation
  - Attack/damage
  - Capture success/fail
  - Level up (future)
  - Item use
- [ ] Integrate audio with scenes
- [ ] Add mute toggle (M key)
- [ ] Update save system to persist audio settings
- [ ] Add unit tests for AudioManager
- [ ] Document audio asset pipeline

**Files to modify:**
- New: `src/engine/audio_manager.py`
- `src/engine/game.py`
- `src/engine/title_scene.py`
- `src/engine/overworld_scene.py`
- `src/engine/battle_scene.py`
- `src/engine/save.py`
- `src/constants.py`
- New: `tests/test_audio.py`
- `Makefile`

**Acceptance Criteria:**
- Background music plays and loops in all scenes
- Sound effects trigger on appropriate actions
- Audio can be muted/unmuted
- No audio lag or stuttering
- Audio settings persist in save file
- Asset pipeline documented

---

### Priority 2: UI/UX Polish

#### Task 2.1: Battle Animation System
**Complexity:** High | **Estimated Scope:** 3-5 files | **Dependencies:** None

**Objective:** Add visual feedback and animations to battle actions

**Subtasks:**
- [ ] Design animation system architecture
- [ ] Create Animation class for sprite effects
- [ ] Implement attack animations:
  - Attacker sprite movement/shake
  - Damage flash effect
  - HP bar smooth transition
- [ ] Add capture animation:
  - Package throw arc
  - Shake animation
  - Success/failure feedback
- [ ] Add status effect animations (faint, low HP warning)
- [ ] Implement text animations (damage numbers, messages)
- [ ] Add battle intro/outro transitions
- [ ] Create particle effect system (optional)
- [ ] Ensure animations don't slow down battle flow
- [ ] Add tests for animation timing
- [ ] Document animation system

**Files to modify:**
- `src/engine/battle_scene.py`
- New: `src/engine/animation.py`
- New: `src/engine/particles.py` (optional)
- `tests/test_battle.py`

**Acceptance Criteria:**
- Smooth HP bar transitions
- Attack animations provide clear visual feedback
- Capture sequence is engaging
- No animation bugs or freezes
- Battle flow remains responsive
- 60 FPS maintained

---

#### Task 2.2: Battle UI Improvements
**Complexity:** Medium | **Estimated Scope:** 2-3 files | **Dependencies:** None

**Objective:** Polish battle interface with better visuals and information display

**Subtasks:**
- [ ] Redesign battle menu layout
- [ ] Add mascot sprites to battle UI (not just colored rectangles)
- [ ] Show type icons/indicators
- [ ] Display move type and power in selection
- [ ] Add HP bar with numeric display
- [ ] Show status conditions visually
- [ ] Improve message box text wrapping
- [ ] Add battle log/history
- [ ] Polish colors and alignment
- [ ] Add mascot portraits (if assets available)
- [ ] Update battle screenshot in docs

**Files to modify:**
- `src/engine/battle_scene.py`
- `src/constants.py` (colors, UI constants)
- `docs/screenshots/battle.png`

**Acceptance Criteria:**
- Battle UI is visually clear and informative
- All information is easily readable
- Layout works at 240x160 resolution
- Type effectiveness is visually indicated
- Screenshot documentation is updated

---

#### Task 2.3: Title and Credits Polish
**Complexity:** Low-Medium | **Estimated Scope:** 3-4 files | **Dependencies:** Task 1.3 (audio)

**Objective:** Enhance title screen and implement credits scene

**Subtasks:**
- [ ] Design title screen layout with logo
- [ ] Add animated elements (mascot sprites, sparkles)
- [ ] Implement menu options (New Game, Continue, Options)
- [ ] Add "Press Start" animation
- [ ] Create proper CreditsScene implementation
- [ ] List all mascots and their types
- [ ] Credit open-source projects used
- [ ] Add scrolling credits animation
- [ ] Integrate title/credits music
- [ ] Add transition from credits back to title
- [ ] Create title screen asset/logo

**Files to modify:**
- `src/engine/title_scene.py`
- `src/engine/credits_scene.py`
- `src/engine/game.py`
- New: `assets/sprites/logo.png`
- `docs/screenshots/title.png`

**Acceptance Criteria:**
- Polished title screen with logo
- Menu system works correctly
- Credits scene is implemented and attractive
- Smooth transitions between scenes
- Music integration complete

---

#### Task 2.4: Overworld UI Enhancements
**Complexity:** Low-Medium | **Estimated Scope:** 2-3 files | **Dependencies:** None

**Objective:** Add HUD and interface improvements to overworld

**Subtasks:**
- [ ] Design minimal HUD layout
- [ ] Add party status display (HP bars, active mascot)
- [ ] Show inventory item counts
- [ ] Add minimap (optional)
- [ ] Implement pause menu (ESC key)
- [ ] Add on-screen control hints
- [ ] Improve NPC interaction indicator
- [ ] Add location/area name display
- [ ] Polish dialogue box appearance
- [ ] Add save/load confirmation messages

**Files to modify:**
- `src/engine/overworld_scene.py`
- `src/overworld.py`
- New: `src/engine/hud.py`

**Acceptance Criteria:**
- HUD provides useful information without clutter
- Party status is always visible
- Pause menu works correctly
- All UI elements respect Game Boy aesthetic
- Controls are intuitive

---

### Priority 3: Content Expansion

#### Task 3.1: Expand Mascot Roster
**Complexity:** Low-Medium | **Estimated Scope:** 2-3 files | **Dependencies:** None

**Objective:** Add more mascots with unique moves and stats

**Subtasks:**
- [ ] Research and list 20+ open-source mascots
- [ ] Design mascot stats (HP, ATK, DEF, SPD)
- [ ] Assign elemental types
- [ ] Create 3-4 signature moves per mascot
- [ ] Add mascot data to YAML/JSON
- [ ] Create or commission mascot sprites (8x8 overworld, 32x32 battle)
- [ ] Add encounter table configuration
- [ ] Update tests with new mascots
- [ ] Document mascot roster

**Files to modify:**
- New: `assets/mascots.yaml`
- `src/engine/battle_scene.py`
- `src/engine/overworld_scene.py`
- `tests/test_battle.py`
- New: `docs/MASCOTS.md`

**Acceptance Criteria:**
- At least 20 mascots defined
- Each has 3-4 unique moves
- Stats are balanced
- All mascots have sprites
- Documentation is complete

---

#### Task 3.2: Move and Type System Expansion
**Complexity:** Medium | **Estimated Scope:** 3-4 files | **Dependencies:** Task 3.1

**Objective:** Expand move pool and refine type effectiveness

**Subtasks:**
- [ ] Design additional elemental types (Database, Network, Security, etc.)
- [ ] Create 40+ unique moves
- [ ] Implement status effects (poison, paralysis, sleep, etc.)
- [ ] Add stat-modifying moves (buff/debuff)
- [ ] Implement multi-hit moves
- [ ] Add priority system for move order
- [ ] Create type effectiveness chart
- [ ] Balance move power and accuracy
- [ ] Update battle logic for new mechanics
- [ ] Add comprehensive tests
- [ ] Document type chart and moves

**Files to modify:**
- `src/engine/battle_scene.py`
- New: `src/engine/status_effects.py`
- `src/constants.py`
- `tests/test_battle.py`
- New: `docs/TYPE_CHART.md`
- New: `docs/MOVES.md`

**Acceptance Criteria:**
- At least 6 elemental types
- 40+ unique moves
- Status effects work correctly
- Type chart is balanced
- All mechanics are tested
- Documentation is comprehensive

---

#### Task 3.3: Item System Expansion
**Complexity:** Low-Medium | **Estimated Scope:** 3-4 files | **Dependencies:** None

**Objective:** Add more items and item interactions

**Subtasks:**
- [ ] Design additional item types:
  - Evolution stones
  - Status healers
  - Battle items (X Attack, X Defense)
  - Held items (future feature)
- [ ] Implement item shop system
- [ ] Add item descriptions
- [ ] Create item pickup system in overworld
- [ ] Add item sprites/icons
- [ ] Update inventory UI to show descriptions
- [ ] Implement item effects in battle
- [ ] Add item management menu
- [ ] Create tests for new items
- [ ] Document item list

**Files to modify:**
- `src/engine/inventory.py`
- `src/engine/battle_scene.py`
- `src/engine/overworld_scene.py`
- New: `src/engine/shop_scene.py`
- `tests/test_inventory.py`
- New: `docs/ITEMS.md`

**Acceptance Criteria:**
- At least 15 different items
- Shop system works correctly
- Items can be found in overworld
- All item effects function properly
- Documentation is complete

---

### Priority 4: Milestone 2 - Maintainer Gyms

#### Task 4.1: Gym System Architecture
**Complexity:** High | **Estimated Scope:** 6-8 files | **Dependencies:** Task 1.2, 3.1, 3.2

**Objective:** Create framework for gym challenges

**Subtasks:**
- [ ] Design gym progression system
- [ ] Create GymLeader class
- [ ] Implement gym badge system
- [ ] Add gym challenge mechanics
- [ ] Create gym entrance/interior maps
- [ ] Implement gym puzzles (optional)
- [ ] Add gym leader AI (stronger than wild mascots)
- [ ] Create victory rewards system
- [ ] Update save system for gym progress
- [ ] Add 8 gym locations to world map
- [ ] Create tests for gym mechanics
- [ ] Document gym system

**Files to modify:**
- New: `src/engine/gym.py`
- New: `src/engine/gym_leader.py`
- `src/engine/overworld_scene.py`
- `src/engine/battle_scene.py`
- `src/engine/save.py`
- `tests/test_gym.py`
- Multiple new map files

**Acceptance Criteria:**
- 8 gym locations on map
- Gym leaders have unique teams
- Badge system works correctly
- Gym progress is saved
- AI is challenging but fair
- Documentation is complete

---

#### Task 4.2: AI System for Trainers
**Complexity:** High | **Estimated Scope:** 3-4 files | **Dependencies:** Task 3.2

**Objective:** Implement intelligent opponent behavior

**Subtasks:**
- [ ] Design AI difficulty levels
- [ ] Create AIController class
- [ ] Implement basic AI (random moves)
- [ ] Implement intermediate AI (type advantage awareness)
- [ ] Implement advanced AI (strategy, switching, prediction)
- [ ] Add personality types for variety
- [ ] Create AI for gym leaders
- [ ] Add AI for final boss
- [ ] Balance AI difficulty
- [ ] Add comprehensive tests
- [ ] Document AI system

**Files to modify:**
- New: `src/engine/ai.py`
- `src/engine/battle_scene.py`
- `src/engine/gym_leader.py`
- `tests/test_ai.py`

**Acceptance Criteria:**
- AI makes sensible decisions
- Difficulty scales appropriately
- Gym leaders feel unique
- AI doesn't cheat or feel unfair
- Well-tested and documented

---

#### Task 4.3: Achievement System
**Complexity:** Medium | **Estimated Scope:** 4-5 files | **Dependencies:** Task 4.1

**Objective:** Track player accomplishments

**Subtasks:**
- [ ] Design achievement list (50+ achievements)
- [ ] Create Achievement class
- [ ] Implement achievement tracking
- [ ] Add achievement unlock notifications
- [ ] Create achievements menu
- [ ] Track statistics (battles won, mascots captured, etc.)
- [ ] Add hidden/secret achievements
- [ ] Implement achievement rewards (optional)
- [ ] Update save system for achievements
- [ ] Add tests
- [ ] Document achievements

**Files to modify:**
- New: `src/engine/achievements.py`
- `src/engine/battle_scene.py`
- `src/engine/overworld_scene.py`
- `src/engine/save.py`
- New: `src/engine/achievements_scene.py`
- `tests/test_achievements.py`

**Acceptance Criteria:**
- 50+ achievements defined
- Unlock notifications work
- Achievements menu is accessible
- Progress is saved correctly
- All achievements are obtainable
- Documentation is complete

---

#### Task 4.4: Save Slot System
**Complexity:** Low-Medium | **Estimated Scope:** 3-4 files | **Dependencies:** None

**Objective:** Support multiple save files

**Subtasks:**
- [ ] Design save slot UI
- [ ] Update save system to support multiple slots
- [ ] Add save slot selection menu
- [ ] Implement save file metadata (playtime, badges, etc.)
- [ ] Add delete save confirmation
- [ ] Show save previews
- [ ] Update title screen to show save slots
- [ ] Migrate existing save format if needed
- [ ] Add tests for multi-slot saves
- [ ] Document save slot system

**Files to modify:**
- `src/engine/save.py`
- `src/engine/title_scene.py`
- New: `src/engine/save_slot_scene.py`
- `src/constants.py`
- `tests/test_save.py`

**Acceptance Criteria:**
- 3 save slots available
- Slot selection works correctly
- Save metadata is displayed
- No data corruption between slots
- Migration from single save works
- Documentation is complete

---

### Priority 5: Polish and Release (Milestone 3)

#### Task 5.1: Performance Optimization
**Complexity:** Medium-High | **Estimated Scope:** All files | **Dependencies:** All major features

**Objective:** Ensure smooth 60 FPS performance

**Subtasks:**
- [ ] Profile performance bottlenecks
- [ ] Optimize sprite rendering
- [ ] Implement sprite caching
- [ ] Optimize collision detection
- [ ] Reduce memory usage
- [ ] Optimize map loading
- [ ] Add loading screens if needed
- [ ] Test on low-end hardware
- [ ] Fix any memory leaks
- [ ] Add performance benchmarks

**Files to modify:**
- All engine files potentially

**Acceptance Criteria:**
- Consistent 60 FPS on target hardware
- No memory leaks
- Fast load times
- Smooth transitions

---

#### Task 5.2: Localization Framework
**Complexity:** High | **Estimated Scope:** 10+ files | **Dependencies:** All content complete

**Objective:** Support multiple languages

**Subtasks:**
- [ ] Design localization system
- [ ] Extract all strings to translation files
- [ ] Create translation file format (JSON/YAML)
- [ ] Implement string loading system
- [ ] Add language selection menu
- [ ] Support dynamic text replacement
- [ ] Handle text length variations
- [ ] Add at least 2 translations (e.g., Spanish, French)
- [ ] Test with all languages
- [ ] Document translation process

**Files to modify:**
- All files with user-facing strings
- New: `src/engine/localization.py`
- New: `assets/translations/`

**Acceptance Criteria:**
- All strings are translatable
- Language switching works
- UI adapts to text length
- At least 3 languages supported
- Translation guide documented

---

#### Task 5.3: Map Editor Tool
**Complexity:** High | **Estimated Scope:** New tool | **Dependencies:** Task 1.1

**Objective:** Create tool for community map creation

**Subtasks:**
- [ ] Evaluate existing tools (Tiled integration)
- [ ] Create custom map editor if needed
- [ ] Add tile palette
- [ ] Implement collision layer editing
- [ ] Add NPC placement tool
- [ ] Support item/trigger placement
- [ ] Add map validation
- [ ] Create map export function
- [ ] Write comprehensive editor guide
- [ ] Create tutorial maps

**Files to modify:**
- New: `tools/map_editor.py` (if custom)
- Documentation

**Acceptance Criteria:**
- Community can create maps
- Editor is intuitive
- Maps validate correctly
- Comprehensive documentation
- Tutorial available

---

#### Task 5.4: Steam/Itch.io Release Prep
**Complexity:** Medium | **Estimated Scope:** Build system | **Dependencies:** All features complete

**Objective:** Package game for distribution

**Subtasks:**
- [ ] Create standalone executable (PyInstaller/Nuitka)
- [ ] Test on Windows, macOS, Linux
- [ ] Create installer/package
- [ ] Design store page assets
- [ ] Write store description
- [ ] Create trailer video
- [ ] Set up Steam/itch.io pages
- [ ] Implement analytics (optional)
- [ ] Add crash reporting
- [ ] Create release checklist
- [ ] Plan marketing strategy

**Files to modify:**
- New: `build.py`
- New: `installer/`
- New: `docs/RELEASE.md`

**Acceptance Criteria:**
- Game runs on all platforms
- Professional store presence
- Release process documented
- Analytics working
- Marketing materials ready

---

## Quick Reference: Agent-Ready Tasks

### Can Start Immediately (No Dependencies)
- Task 1.3: Audio System Foundation
- Task 2.1: Battle Animation System
- Task 2.2: Battle UI Improvements
- Task 2.4: Overworld UI Enhancements
- Task 3.1: Expand Mascot Roster
- Task 3.3: Item System Expansion
- Task 4.4: Save Slot System

### Small Tasks (< 1 day, good for new agents)
- Add battle damage numbers animation
- Create mascot sprite templates
- Design type effectiveness icons
- Write item descriptions
- Create achievement list
- Design gym badge sprites
- Write gym leader dialogue
- Create battle sound effects list
- Design pause menu UI
- Add control reminders to title screen

### Research Tasks (Exploration, No Code Changes)
- Research Tiled .tmx format and pytmx library
- Survey open-source mascots for roster
- Research pygame.mixer audio capabilities
- Investigate animation techniques in Pygame
- Study Pokemon battle AI patterns
- Research localization best practices
- Evaluate map editor options
- Research PyInstaller vs Nuitka for builds

---

## Testing Requirements

Every task must include:
- Unit tests for new functionality
- Integration tests if multiple systems interact
- Manual testing checklist
- Regression test to ensure existing features work
- Performance testing for heavy operations

---

## Documentation Requirements

Every task must update:
- CLAUDE.md if it changes development workflow
- README.md if it changes user-facing features
- Relevant design docs
- Code comments for complex logic
- Docstrings for public APIs

---

## Definition of Done

A task is complete when:
- [ ] Code is written and follows project style (Black, Ruff)
- [ ] All tests pass (unit + integration)
- [ ] No regressions in existing functionality
- [ ] Documentation is updated
- [ ] Code is reviewed (if working with team)
- [ ] Changes are committed with clear message
- [ ] Task is marked complete in tracking system

---

## Notes for Agent Coordination

### Communication Protocol
- Agents should report progress daily
- Blockers should be escalated immediately
- Dependencies should be clearly stated
- Code conflicts should be resolved quickly

### Code Standards
- Follow existing patterns in codebase
- Use type hints (Python 3.12+)
- Write docstrings for public functions
- Keep functions small and focused
- Test edge cases thoroughly

### Git Workflow
- Create feature branch for each task
- Commit frequently with clear messages
- Push to remote regularly
- Create PR when task is complete
- Request review before merging

---

**Last Updated:** 2026-01-20
**Next Review:** After Milestone 1 completion
