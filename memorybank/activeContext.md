# Active Context

## Current Work Focus

**Status**: Development workflow infrastructure completed.

**Recent Activity** (January 8, 2025): 
- Created task completion workflow in `.clinerules/workflows/`
- Created comprehensive implementation documentation for bot001.py
- Added incremental file creation rule to .clinerules
- Polished language in basic_requirements.md for clarity
- Documented all bot001 components in detail


## Recent Changes

### Workflow Creation (January 8, 2025)
1. **Task Completion Workflow** (`.clinerules/workflows/task_completion.md`):
   - Created standardized workflow for post-task completion
   - Two-step process: Update memory bank → Clear git status
   - Detailed guidance on which memory bank files to update and why
   - Clear git workflow with commit message best practices
   - Execution notes for proper implementation

### Documentation Enhancement (January 8, 2025)
1. **Bot001 Implementation Documentation** (`docs/bot_implementation/bot001_implementation.md`):
   - Created comprehensive 700+ line documentation covering all implementation details
   - Built incrementally section by section (following new .clinerules guideline)
   - Documented 5 modules: Game Constants, Board, MCTS Tree, Evaluation, Search Algorithm, I/O
   - Included algorithm complexity analysis, design rationale, and optimization opportunities
   - Added performance tuning section with known limitations and future improvements

2. **.clinerules Enhancement**:
   - Added Rule #8: "Incremental File Creation" to basic_requirements.md
   - Polished all requirement descriptions for clarity and actionability
   - Fixed numbering inconsistency (duplicate item #9)
   - Improved language: more specific instructions, clearer purpose statements, better titles

3. **Git Commit**: 
   - Committed documentation and .clinerules updates
   - Latest commit: 7e0b13e8f35ecd06de9ff87dfa40883c91cdede3

### Project Setup (Previous Session)
1. **Memory Bank Creation**: Established comprehensive documentation system
   - Created all core memory bank files
   - Documented game rules, architecture, and technical details
   - Captured critical platform constraints (time limits)

2. **Code Import**: 
   - Brought bot001.py (best previous bot) into new project
   - Bot uses Multi-Component MCTS (no neural network)
   - Sophisticated evaluation with 5 components
   - Long-running mode implementation

3. **Documentation**:
   - Wiki docs stored in `wiki/` folder
   - Botzone platform interaction protocols documented
   - Time limit information added (user-provided critical details)

## Next Steps

### Immediate Priorities
1. **Verify bot001 functionality**
   - Test bot locally with sample input
   - Ensure long-running mode works correctly
   - Verify all evaluation components work

2. **Create testing infrastructure**
   - Build test harness in `scripts/` directory
   - Implement bot vs bot testing capability
   - Create match replay functionality

3. **Baseline performance**
   - Test bot001 against random player
   - Submit to Botzone for initial rating
   - Analyze early match logs

### Medium-Term Goals
1. **Bot improvement research**
   - Study match logs to identify weaknesses
   - Research advanced evaluation functions
   - Investigate opening book strategies

2. **Development tools**
   - Position visualization
   - MCTS tree inspection
   - Performance profiling scripts

3. **New bot versions**
   - Experiment with different neural architectures
   - Try different MCTS parameters
   - Implement move ordering heuristics

## Active Decisions and Considerations

### Platform Time Limits (CRITICAL)
**User-provided information**:
- Python long-running: First turn = 12s, subsequent = 4s
- C++ long-running: First turn = 2s, subsequent = 1s

**Current bot001 settings**:
- `TIME_LIMIT = 3.8` (safe buffer under 4s)
- `FIRST_TURN_TIME_LIMIT = 5.8` (conservative, could use more)

**Decision needed**: Should we increase first turn limit closer to 12s for better opening moves?

### Evaluation Function Complexity
**Observation**: Bot001 uses sophisticated multi-component evaluation
**Components**:
1. Queen territory (BFS-based)
2. King territory (weighted close-range)
3. Queen position (exponential decay)
4. King position (distance-weighted)
5. Mobility (available moves)

**Consideration**: These weights are inspired by opponent03 - need to verify optimality through testing

### Testing Strategy
**Preferred approach**:
1. Unit tests for move generation
2. Integration tests for I/O protocol
3. Performance tests against previous versions
4. Botzone submission for real-world validation

### Code Organization
**Current structure is good**:
- `core/` for shared logic ✓ (not used by bot001 but available)
- `bots/` for individual implementations ✓
- Separate directories for logs, reports, results ✓

**Note**: Bot001 is self-contained and doesn't use core/game.py

**Potential additions**:
- `tests/` directory for unit tests
- `analysis/` directory for match analysis tools
- `tuning/` directory for parameter optimization

## Important Patterns and Preferences

### Development Workflow
1. Make changes locally
2. Test thoroughly before submission
3. Document changes in memory bank
4. Commit with git after major milestones
5. Update README.md with project status

### Code Style
- Clear, readable code over clever optimizations
- Comments for non-obvious logic
- Docstrings for public functions
- Type hints where helpful (not enforced yet)

### Documentation Discipline
- Update memory bank after significant changes
- Keep `activeContext.md` current with latest work
- Update `progress.md` with completed milestones
- Document learnings and insights

## Learnings and Project Insights

### Game Characteristics
- **Branching factor**: Extremely high in early game (200-800 moves)
- **Game length**: Typically 40-80 plies (20-40 turns per player)
- **Critical phase**: Mid-game territory formation
- **Endgame**: Often about mobility and avoiding getting trapped

### MCTS for Amazons
- **Challenge**: High branching factor limits search depth
- **Solution**: Multi-component evaluation eliminates rollout overhead
- **Dynamic UCB**: Exploration constant decreases with turn number
- **Phase weights**: Different strategic priorities for early/mid/late game
- **Tree reuse**: Significant benefit in long-running mode
- **Time management**: Critical to reserve safety buffer

### Botzone Platform
- **Long-running mode**: Essential for Python bots to compete
- **I/O protocol**: Simplified interaction is easier to implement
- **Debugging**: Requires careful log analysis
- **Testing**: Local testing crucial before submission

### Evaluation Function Design
- **Multi-component**: Five strategic factors combined
- **Phase-aware**: Weights change through early/mid/late game
- **BFS-based**: Territory control via breadth-first search
- **Exponential decay**: Position scoring favors closer territory
- **Sigmoid normalization**: Final score mapped to [0, 1] probability
- **Evaluation speed**: Must be < 0.001s per call for MCTS efficiency

## Known Issues and Gotchas

### Bot001 Potential Issues
1. **BFS overhead**: Territory calculation may be slow in early game
2. **I/O edge cases**: Minimal error handling for malformed input
3. **Time management**: No dynamic adjustment if running slow
4. **Memory**: No monitoring of tree size growth
5. **Weight tuning**: Phase weights from opponent03 may not be optimal

### Platform Quirks
1. **Long-running timing**: CPU usage during wait is counted toward next turn
2. **Stdout flush**: Critical to call `sys.stdout.flush()` after each output
3. **Signal handling**: Bot receives SIGSTOP/SIGCONT between turns
4. **File access**: Must use relative paths or Botzone storage path

### Development Environment
1. **Import paths**: Bots need `sys.path.insert()` to import from `core/`
2. **Testing I/O**: Need to simulate Botzone input format carefully
3. **Performance**: Local timing may differ from Botzone VM

## Questions and Uncertainties

1. **Weight origin**: Where did the phase weights come from? Are they from opponent03 testing?
2. **Previous project history**: What versions led to this implementation?
3. **Optimal parameters**: Is the dynamic UCB formula (0.177 * exp(-0.008 * turn)) tuned?
4. **Phase boundaries**: Are turns 10/20 the optimal phase transition points?
5. **Component weights**: Could machine learning optimize the 5-component weights better?
6. **Opening strategies**: Should we implement opening book or just rely on search?

## Context for Future Me

When resuming work on this project:
1. Check this file first for current status
2. Review `progress.md` for what's been completed
3. Address any critical issues listed above
4. Continue with "Next Steps" priorities
5. Update documentation after making changes

**Most critical immediate task**: Test bot001 locally to verify all evaluation components work correctly.
