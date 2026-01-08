# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a competitive AI bot development project for the Game of Amazons, designed to run on the Botzone platform. The project focuses on creating high-performance bots using Monte Carlo Tree Search (MCTS) with various optimization techniques.

**Key Technologies**: Python 3.6+, C++11, NumPy
**Platform**: Botzone (Ubuntu 16.04 x86-64)
**Game**: Amazons (8×8 board, 4 amazons per player, queen movement + arrow shooting)

## Development Commands

### Bot Compilation
C++ bots are compiled manually with:
```bash
g++ -O3 -std=c++11 -o bots/botXXX bots/botXXX.cpp
```

The tournament system provides a helper function:
```bash
python -c "from scripts.tournament.utils import compile_bot; compile_bot('bot003')"
```

### Testing Commands
**Quick functionality test** (first move as BLACK):
```bash
echo "1
-1 -1 -1 -1 -1 -1" | python bots/bot001.py
# or for C++ bots:
echo "1
-1 -1 -1 -1 -1 -1" | ./bots/bot001_cpp
```

**Run simple bot tests**:
```bash
python scripts/test_bot_simple.py
```

**Run Botzone protocol simulation**:
```bash
python scripts/botzone_simulator.py
```

### Tournament System
The tournament framework (`scripts/tournament/`) provides comprehensive testing:

**Single match**:
```bash
python -c "from scripts.tournament.cli import run_match; run_match('bot001', 'bot003')"
```

**Competition automation** (10-game series):
```bash
python scripts/run_competitions.py
```

**Check legal moves** (debugging tool):
```bash
python scripts/check_legal_moves.py
```

**Debug board visualization**:
```bash
python scripts/debug_board.py
```

## Architecture Overview

### Directory Structure
- `core/` - Shared game logic (board representation, move generation)
- `bots/` - Bot implementations (Python and C++ versions)
- `scripts/` - Testing and utility scripts
- `docs/` - Comprehensive documentation
- `memorybank/` - Project context and technical decisions (Cline system)
- `results/` - Tournament results (JSON format)
- `logs/` - Match logs and output

### Bot Architecture
The primary algorithm is **Multi-Component MCTS** with these key features:

1. **Multi-Component Evaluation**: Five strategic factors combined:
   - Queen Territory (BFS-based territory control)
   - King Territory (weighted close-range control)
   - Queen Position (exponential decay scoring)
   - King Position (distance-weighted positioning)
   - Mobility (available moves count)

2. **Phase-Aware Weighting**: Different strategies for early/mid/late game phases

3. **Dynamic UCB Constant**: Exploration decreases as game progresses

4. **Long-Running Mode**: Maintains MCTS tree state between turns for efficiency

### Bot Implementations
- `bot001.py` / `bot001.cpp` - Primary MCTS implementation (Python and C++ versions)
- `bot002.cpp` - Optimized version with bitboard representation (has TLE issues)
- `bot003.cpp` - Baseline MCTS bot for comparison
- `bot004-bot008.cpp` - Optimization bots with different techniques
- `opponent.cpp` - Latest implementation with AVX2 SIMD optimizations

## Platform Constraints (Botzone)

### Time Limits
- **Python long-running bots**: 12s (first turn), 4s (subsequent turns)
- **C++ long-running bots**: 2s (first turn), 1s (subsequent turns)

### Resource Limits
- Memory: 256 MB default
- CPU: Single core (no multi-threading benefit)

### I/O Protocol
- Simplified interaction: Line-based stdin/stdout
- Long-running mode: Must flush stdout after each turn
- Move format: 6 integers `x0 y0 x1 y1 x2 y2`

## Development Workflow

### Cline Memory Bank System
The project uses a Cline memory bank (`memorybank/`) for context:
- `projectbrief.md` - Project overview and objectives
- `systemPatterns.md` - Architecture and design decisions
- `techContext.md` - Technologies and constraints
- `activeContext.md` - Current state and next steps
- `progress.md` - Development progress and milestones

### Development Rules (`.clinerules/`)
- `development_workflow.md` - Development processes
- `task_completion.md` - Mandatory sequential workflow for task completion
- `memory_bank_update.md` - How to update memory bank files
- `readme_update.md` - README update procedures

### Key Development Patterns
1. **Always test sequentially** - Run tests in order: simple test → protocol simulation → tournament
2. **Update memory bank first** - Review and update memory bank files before making changes
3. **Check Botzone compatibility** - Ensure bots work within platform constraints
4. **Use tournament framework** - For comprehensive testing and performance comparison

## Common Tasks

### Creating a New Bot
1. Copy an existing bot (e.g., `bot003.cpp`) as a starting point
2. Implement optimization technique
3. Compile: `g++ -O3 -std=c++11 -o bots/botXXX bots/botXXX.cpp`
4. Test with simple test script
5. Run competition against baseline (`bot003`)
6. Analyze results in `results/competitions/`

### Debugging TLE (Time Limit Exceeded) Issues
1. Check time limits in bot code (conservative buffers required)
2. Use tournament system to measure actual execution times
3. Profile with `scripts/check_legal_moves.py` for move generation issues
4. Review Botzone logs for specific timing patterns

### Testing Botzone Compatibility
1. Use `botzone_simulator.py` to simulate platform I/O
2. Verify long-running mode works correctly
3. Check memory usage stays under 256 MB
4. Ensure move format matches Botzone expectations

## Important Notes

- **No automated build system** - Bots are compiled manually
- **NumPy dependency** - Required for Python bots, not for C++ bots
- **Tree reuse** - MCTS trees are preserved between turns in long-running mode
- **Bitboard representation** - Used in optimized bots for faster operations
- **AVX2 optimizations** - Latest addition in `opponent.cpp` for SIMD parallelism

## Getting Started
1. Read `README.md` for comprehensive project overview
2. Check `memorybank/` for current project context
3. Use tournament framework for testing: `scripts/tournament/`
4. Follow Cline workflows in `.clinerules/` for development tasks