# Task Delegation Template

Use this template when assigning tasks to agents or team members.

---

## Task: [Task ID and Name]

**Example:** Task 1.3: Audio System Foundation

---

### Overview
**Complexity:** [Low | Medium | High]
**Estimated Scope:** [Number of files to create/modify]
**Priority:** [High | Medium | Low]
**Dependencies:** [List task IDs or "None"]

**Brief Description:**
[1-2 sentence summary of what this task accomplishes]

---

### Objective
[Detailed description of the goal and why it's important]

---

### Context
**Related Documentation:**
- [Link to relevant docs]
- [Link to design specs]

**Existing Code to Review:**
- `path/to/file1.py` - [What to look for]
- `path/to/file2.py` - [What to look for]

**Similar Patterns in Codebase:**
[Point to existing code that uses similar patterns]

---

### Requirements

#### Functional Requirements
- [ ] [Requirement 1]
- [ ] [Requirement 2]
- [ ] [Requirement 3]

#### Technical Requirements
- [ ] Follow existing code style (Black, Ruff)
- [ ] Add type hints
- [ ] Write docstrings
- [ ] Maintain 60 FPS performance
- [ ] Keep Game Boy aesthetic (4-color palette, 240x160)

---

### Detailed Subtasks

#### Phase 1: Research & Planning
- [ ] [Subtask 1]
- [ ] [Subtask 2]

#### Phase 2: Implementation
- [ ] [Subtask 3]
- [ ] [Subtask 4]

#### Phase 3: Testing & Documentation
- [ ] [Subtask 5]
- [ ] [Subtask 6]

---

### Files to Create/Modify

**New Files:**
- `src/path/to/new_file.py` - [Purpose]
- `tests/test_new_feature.py` - [Test coverage]

**Files to Modify:**
- `src/existing/file.py` - [What changes are needed]
- `src/constants.py` - [Add new constants]

**Files to Read (Context):**
- `src/related/file.py` - [Understand existing patterns]

---

### Testing Checklist

#### Unit Tests
- [ ] Test [specific functionality]
- [ ] Test edge case: [describe case]
- [ ] Test error handling: [describe scenario]

#### Integration Tests
- [ ] Test integration with [system A]
- [ ] Test interaction with [system B]

#### Manual Testing
- [ ] Start game and [test scenario]
- [ ] Verify [expected behavior]
- [ ] Check performance (60 FPS maintained)

#### Regression Testing
- [ ] Existing feature X still works
- [ ] Save/load still works
- [ ] No new bugs in [related area]

---

### Acceptance Criteria

- [ ] [Criterion 1: Specific, measurable outcome]
- [ ] [Criterion 2: Specific, measurable outcome]
- [ ] [Criterion 3: Specific, measurable outcome]
- [ ] All tests pass (`pytest`)
- [ ] Code follows style guide (`ruff check .`)
- [ ] Documentation is updated
- [ ] No performance regressions

---

### Documentation Updates Required

- [ ] Update `README.md` if user-facing features changed
- [ ] Update `CLAUDE.md` if development workflow changed
- [ ] Update `docs/design.md` if architecture changed
- [ ] Add/update docstrings in modified files
- [ ] Update this task in `docs/backlog.md` when complete

---

### Resources

**Helpful Links:**
- [Link to pygame.mixer docs]
- [Link to relevant tutorial]
- [Link to example code]

**Questions to Ask:**
- [Question about requirements]
- [Question about design choice]

---

### Implementation Notes

**Recommended Approach:**
[Suggest a high-level approach or strategy]

**Things to Watch Out For:**
- [Potential pitfall 1]
- [Potential pitfall 2]

**Optional Enhancements:**
- [Nice-to-have feature 1]
- [Nice-to-have feature 2]

---

### Progress Tracking

**Status:** Not Started
**Assigned To:** [Agent/Person name]
**Start Date:** [YYYY-MM-DD]
**Target Completion:** [YYYY-MM-DD]
**Actual Completion:** [YYYY-MM-DD]

**Blockers:**
- [List any blockers as they arise]

**Updates:**
- [YYYY-MM-DD]: [Progress update]
- [YYYY-MM-DD]: [Progress update]

---

### Review Checklist

Before marking as complete:
- [ ] Code review completed
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Changes committed with clear message
- [ ] PR created (if applicable)
- [ ] Demo prepared (if applicable)
- [ ] Backlog updated

---

## Example: Completed Task Brief

### Task 1.3: Audio System Foundation

**Status:** ✅ Complete
**Completed By:** Agent-Audio-01
**Completion Date:** 2026-01-25

**Summary:**
Implemented full audio system using pygame.mixer with background music for all scenes and 8 sound effects. Added mute toggle (M key) and volume controls. Audio settings persist in save file.

**Key Changes:**
- Created `src/engine/audio_manager.py` (AudioManager class)
- Integrated audio into all scenes
- Added 3 music tracks (title, overworld, battle)
- Added 8 sound effects
- Updated save system to persist audio settings

**Lessons Learned:**
- pygame.mixer initialization needs to happen early in game loop
- Audio files should be pre-loaded to avoid lag
- Volume controls need separate channels for music vs SFX

**Follow-up Tasks:**
- Consider adding more battle music variations
- Add audio settings menu (separate from quick mute toggle)
