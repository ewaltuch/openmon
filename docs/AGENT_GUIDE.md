# Agent Delegation Guide

Quick reference for delegating tasks to Gemini Code Assistant and other AI agents.

---

## Quick Start

1. **Pick a task** from [backlog.md](./backlog.md) "Ready to Start" section
2. **Fill in details** from [ROADMAP.md](./ROADMAP.md)
3. **Assign to Gemini Code Assistant** with clear instructions
4. **Track progress** in [backlog.md](./backlog.md) Active Tasks table
5. **Review and integrate** locally when complete

---

## Document Structure

```
docs/
├── ROADMAP.md          # Detailed task descriptions, dependencies, acceptance criteria
├── backlog.md          # High-level milestones + active task tracking
├── TASK_TEMPLATE.md    # Template for task delegation (optional reference)
├── AGENT_GUIDE.md      # This file - how to work with agents
└── design.md           # Architecture overview
```

---

## Agent Types & Task Matching

When assigning to Gemini Code Assistant (or other AI coding agents), match tasks to strengths:

### Content-Heavy Tasks
**Good For Agents:**
- Writing dialogue and NPC interactions
- Creating mascot stats and descriptions
- Designing items and achievements
- Writing documentation

**Example Tasks:**
- Task 3.1: Expand Mascot Roster (content portions)
- Write gym leader dialogue
- Create achievement descriptions

### UI/UX Tasks
**Good For Agents:**
- Implementing UI layouts
- Creating visual elements
- Menu systems
- Polish and feedback

**Example Tasks:**
- Task 2.2: Battle UI Improvements
- Task 2.4: Overworld UI Enhancements
- Design pause menu

### Gameplay Mechanics
**Good For Agents:**
- Implementing game features
- Battle system enhancements
- Player progression systems

**Example Tasks:**
- Task 4.2: AI System for Trainers
- Task 3.2: Move and Type System Expansion
- Battle animations

### Systems & Architecture
**More Complex - Provide Extra Guidance:**
- Engine architecture
- Save/load systems
- Performance optimization

**Example Tasks:**
- Task 1.1: Tiled Map Integration
- Task 4.4: Save Slot System
- Task 5.1: Performance Optimization

### Audio Integration
**Good For Agents:**
- Sound effects integration
- Music system implementation

**Example Tasks:**
- Task 1.3: Audio System Foundation

---

## Task Selection Guide

### For First-Time Tasks (Start Here)
Start with "Quick Wins" - small, self-contained tasks:
- Add mute toggle
- Create save/load confirmation messages
- Add on-screen control hints
- Write NPC dialogue

### For Standard Tasks
Pick from "Priority 1" tasks:
- Task 1.3: Audio System
- Task 2.2: Battle UI Improvements
- Task 3.1: Expand Mascot Roster

### For Parallel Assignments
These can be worked on by different agent sessions simultaneously:
- Task 1.3 (Audio) + Task 2.2 (Battle UI) + Task 3.1 (Mascots)
- Task 2.4 (Overworld UI) + Task 3.3 (Items) + Task 4.4 (Save Slots)

---

## Task Delegation Checklist

Before delegating:
- [ ] Task has no blocking dependencies OR dependencies are clear
- [ ] Task description is detailed and unambiguous
- [ ] Acceptance criteria are measurable
- [ ] Files to modify are listed
- [ ] Examples/patterns from codebase are provided
- [ ] Test requirements are clear
- [ ] Context from existing code is included

---

## Quality Standards

### All Code Must
- [ ] Pass all existing tests (`pytest`)
- [ ] Include new tests for new functionality
- [ ] Follow project style (Black, Ruff - run `ruff check .`)
- [ ] Include docstrings for public functions
- [ ] Use type hints (Python 3.12+)
- [ ] Maintain 60 FPS performance
- [ ] Update relevant documentation

### All Tasks Must
- [ ] Have acceptance criteria met
- [ ] Include test coverage
- [ ] Update documentation
- [ ] Not break existing features
- [ ] Be verified by you before committing

---

## Working with Gemini Code Assistant

### Assignment Format

When assigning a task, provide complete context in one message:

```markdown
Task: [Task ID and Name from ROADMAP.md]

Objective:
[Clear description of what needs to be accomplished]

Context:
- Review src/path/to/related/file.py to understand existing patterns
- This feature should follow the Game Boy aesthetic (4-color palette, 240x160 resolution)
- Reference similar code in src/path/to/example.py

Requirements:
- [Specific requirement 1]
- [Specific requirement 2]
- Must maintain 60 FPS performance

Files to Create/Modify:
- src/new/file.py - [Purpose]
- src/existing/file.py - [What to change]
- tests/test_feature.py - [Test coverage needed]

Acceptance Criteria:
- [Measurable outcome 1]
- [Measurable outcome 2]
- All tests pass
- Documentation updated

Testing:
- Run pytest after implementation
- Manual test: [specific scenario]
- Verify no regressions in [related feature]

See docs/ROADMAP.md Task X.X for full details.
```

### Example Task Assignment

```markdown
Task 2.2: Battle UI Improvements

Objective:
Polish the battle interface with better layout, move information display, and visual clarity.

Context:
- Current implementation: src/engine/battle_scene.py lines 200-400
- Follow existing Game Boy aesthetic (4 colors from src/constants.py)
- Reference docs/screenshots/battle.png for current state
- Menu system pattern in src/engine/title_scene.py shows how we handle menus

Requirements:
- Show move type icon next to move name in selection menu
- Display move power value
- Make HP bars more prominent with numeric display
- Add type effectiveness indicator (e.g., "Super effective!")
- Ensure everything fits in 240x160 resolution
- Maintain 60 FPS performance

Files to Modify:
- src/engine/battle_scene.py - Main UI implementation
- src/constants.py - Add any new UI constants (colors, positions)
- tests/test_battle.py - Update tests if UI changes affect them

Acceptance Criteria:
- Move selection shows type icon and power
- HP display is clear and prominent
- Type effectiveness is visually indicated during attacks
- All existing battle functionality still works
- Tests pass
- Manual testing shows improved clarity

Testing:
- Run: pytest tests/test_battle.py
- Manual test: Start battle, use different move types, verify UI displays correctly
- Test with multiple mascots to ensure consistency
- Verify save/load still works after battle

Implementation Notes:
- Use pygame.draw for shapes and pygame.font for text
- Keep UI elements aligned to 8-pixel grid where possible
- Reference TYPE_EFFECTIVENESS dict in battle_scene.py for type checking

See docs/ROADMAP.md Task 2.2 for full details.
```

---

## Agent Workflow

### 1. Task Assignment
- Provide complete task description to Gemini
- Include all context from ROADMAP.md
- Specify exact files and patterns to follow

### 2. Implementation
- Agent works on the feature
- Agent should run tests periodically
- Agent reports progress/blockers

### 3. Completion Report
Agent should provide:
- Summary of changes made
- Which files were modified/created
- Test results
- Any issues encountered
- Manual testing confirmation

### 4. Your Review
- Review code changes locally
- Run `pytest` yourself
- Run `python -m src.engine.game` to test manually
- Check style with `ruff check .`
- Verify against acceptance criteria

### 5. Integration
- If approved: commit changes with clear message
- If needs revision: provide specific feedback
- Update docs/backlog.md to mark complete

---

## Common Scenarios

### Scenario 1: Agent Finds a Bug
**Agent:** "While implementing X, I found a bug in Y. Should I fix it?"

**Your Response:**
- "Yes, fix it as part of this task" - if small and related
- "No, document it for later" - if unrelated or large
- Ask for details if unclear

### Scenario 2: Design Decision Needed
**Agent:** "Should I implement this as A or B?"

**Your Response:**
- Provide clear direction with reasoning
- Reference existing patterns in codebase
- Consider maintainability and consistency
- Make a definitive choice

### Scenario 3: Task is Blocked
**Agent:** "Can't proceed because X isn't implemented yet"

**Your Response:**
- Implement X yourself first, then reassign
- OR assign X to agent as prerequisite
- OR adjust task scope to work around

### Scenario 4: Scope Questions
**Agent:** "Should I also add feature Z?"

**Your Response:**
- "Yes, if it's small and makes sense"
- "No, let's keep focused on task scope"
- "Good idea - let's make it a separate task"

---

## Review Checklist

Before committing agent's work:
- [ ] All tests pass (`pytest`)
- [ ] Code style is correct (`ruff check .`)
- [ ] Manual testing shows feature works
- [ ] No regressions in existing features
- [ ] Documentation is updated (README, CLAUDE.md if needed)
- [ ] Changes match acceptance criteria
- [ ] Code follows project patterns
- [ ] Performance is maintained (60 FPS)

---

## Integration Process

### When Agent Reports Completion

1. **Ask for change summary**
   - "What files did you change?"
   - "What's the high-level approach?"

2. **Review the code**
   - Read through changes
   - Check for obvious issues
   - Verify follows project patterns

3. **Run tests**
   ```bash
   pytest                          # All tests
   pytest tests/test_battle.py     # Specific test
   pytest -v                       # Verbose
   ```

4. **Manual testing**
   ```bash
   python -m src.engine.game
   ```
   - Test the new feature
   - Check related features still work
   - Verify save/load compatibility

5. **Style check**
   ```bash
   ruff check .
   black --check .
   ```

6. **Commit if approved**
   ```bash
   git add src/engine/battle_scene.py src/constants.py
   git commit -m "Task 2.2: Improve battle UI with type indicators and HP display

   - Added move type icons to battle menu
   - Show move power values
   - Enhanced HP display with numeric values
   - Added type effectiveness indicators

   All tests passing, manual testing successful."

   git push
   ```

7. **Update tracking**
   - Mark task complete in docs/backlog.md
   - Update active task table
   - Add completion date

---

## Progress Tracking

### Update backlog.md Regularly
- Move completed items to "Complete" section
- Update milestone percentages
- Adjust priorities based on learnings
- Add newly discovered tasks

### After Each Task
- [ ] Update Active Tasks table
- [ ] Move from backlog to complete
- [ ] Note completion date
- [ ] Celebrate the win!

---

## Tips for Effective Delegation

### Do
✅ Provide complete context upfront
✅ Include examples from existing code
✅ Be specific about acceptance criteria
✅ Allow questions and clarifications
✅ Review work thoroughly
✅ Give constructive feedback
✅ Acknowledge good work

### Don't
❌ Assign tasks with vague requirements
❌ Change requirements mid-task
❌ Skip code review
❌ Forget to test manually
❌ Forget to update tracking docs
❌ Commit without verification

---

## Troubleshooting

### Agent is struggling with task
- Provide more context from existing code
- Break task into smaller pieces
- Pair with agent (guide step-by-step)
- Consider if task is too complex

### Tests are failing
- Ask agent to debug and fix
- Check if it's a test issue vs implementation issue
- Provide guidance on test failures

### Code doesn't match project style
- Point to specific style issues
- Reference good examples in codebase
- Run Black/Ruff and share output
- Request revisions

### Feature works but has issues
- Provide specific, actionable feedback
- Explain why change is needed
- Reference project standards
- Be clear about must-haves vs nice-to-haves

---

## Success Metrics

Track to measure delegation effectiveness:
- **Completion rate** - % of assigned tasks completed successfully
- **First-time pass rate** - % passing review without major revisions
- **Integration time** - How long from completion to commit
- **Quality** - Are tests comprehensive? Code maintainable?

---

## Quick Reference Commands

```bash
# Test the game
python -m src.engine.game

# Run all tests
pytest

# Run specific test file
pytest tests/test_battle.py

# Verbose test output
pytest -v

# Check code style
ruff check .
black --check .

# Fix style automatically
ruff check --fix .
black .

# Build assets
make assets

# View git status
git status

# Review changes
git diff

# Commit changes
git add [files]
git commit -m "Task X.X: Description"
git push
```

---

**Remember:** Clear communication + thorough review = successful delegation

Gemini Code Assistant is a powerful tool when given clear instructions and context.
