# Amazing Amazons

A project for developing high-intelligence AI bots for the Game of Amazons, designed to compete on the [Botzone platform](https://www.botzone.org.cn/).

## Overview

This is a new version of the previous AmazingAmazons project, focused on creating competitive AI bots using advanced techniques like Monte Carlo Tree Search (MCTS) and sophisticated evaluation functions. The project currently features bot001, a multi-component MCTS implementation that utilizes Botzone's long-running mode for optimal performance.

### The Game: Amazons

- **Board**: 8×8 grid
- **Pieces**: Each player (Black/White) has 4 amazons
- **Movement**: Amazons move like chess queens (8 directions, any distance)
- **Turn Structure**: 
  1. Move one amazon to an empty square
  2. Shoot an arrow from the new position to place an obstacle
- **Win Condition**: Opponent cannot make any legal move
- **First Move**: Black moves first

## Project Structure

```
amazing-amazons/
├── core/              # Shared game logic and utilities
│   ├── game.py       # Board representation and move generation
│   └── ai.py         # Generic MCTS implementation (legacy)
├── bots/             # Bot implementations
│   ├── bot001.py     # Python MCTS bot (Multi-Component)
│   ├── bot001.cpp    # C++ port (4x faster, production-ready)
│   ├── bot001_cpp    # Compiled C++ binary
│   ├── bot002.cpp    # Optimized C++ bot (bitboards, faster)
│   └── bot002_cpp    # Compiled optimized binary
├── scripts/          # Testing and utility scripts
│   ├── test_bot_simple.py      # Quick bot functionality tests
│   ├── botzone_simulator.py   # I/O protocol simulator
│   └── tournament.py           # Bot comparison framework
├── memorybank/       # Project documentation (Cline memory system)
├── wiki/             # Botzone platform documentation
├── logs/             # Match logs and tournament output
├── reports/          # Analysis reports
├── results/          # Tournament results (JSON)
└── docs/             # Implementation documentation
    ├── bot_implementation/
    │   ├── bot001_implementation.md      # Python bot documentation
    │   └── bot001_cpp_implementation.md  # C++ bot documentation
    └── requests/
        └── cpp_bot_optimization_request.md  # Optimization request for expert consultation
```

## Setup

### Requirements

- Python 3.6+
- NumPy

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd amazing-amazons
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install numpy
```

## Current Status

✅ **Complete**: Bot001 C++ port, testing infrastructure, bot002 optimized version, and tournament validation  
🔄 **Ready**: Bot002 for Botzone submission (crash-free and stable)  
📅 **Planned**: Advanced features (opening book, endgame solver)

**Recent Updates** (December 14, 2025):
- **Task Completion Workflow Enhanced**: Improved workflow to enforce mandatory sequential execution
  - Problem: Steps were being skipped, memory bank files not reviewed before updates
  - Solution: Complete rewrite of `.clinerules/workflows/task_completion.md`
  - Added mandatory 4-step sequence: (1) Review ALL memory bank files → (2) Update files one by one → (3) Update README → (4) Clear git status
  - Multiple safeguards: Warning messages, checkpoints, "STOP HERE" instructions, completion checklist
  - Result: Workflow now prevents skipping steps and ensures thorough updates
- **Bot002 Bug Fix**: Fixed illegal move issue reported from Botzone
  - Root cause: Color tracking error during game history replay caused board desynchronization
  - Fix: Corrected to always start with BLACK for first actual move, alternate only on actual moves
  - Verification: 3 tournament games in non-parallel mode - zero illegal moves, all games ended naturally
  - Git commit: 53cca24
  - Status: Production-ready for Botzone deployment
- **Bot002 Tournament Testing**: 20 games vs bot001 - **ZERO CRASHES**
  - Fixed critical crash bugs (move replay logic, input validation, defensive checks)
  - Results: Bot001 won 16 games (80%), Bot002 won 4 games (20%)
  - Bot002 faster (1.128s/move) but strategically weaker than bot001 (1.776s/move)
  - Average game length: 25.9 turns

**Previous Updates** (December 13, 2025):
- **Created bot002.cpp**: Optimized version with bitboard representation
  - Bitboard move generation (3x uint64_t vs 8x8 array)
  - Fast BFS with fixed arrays and on-the-fly accumulation
  - Xorshift64 PRNG, node pool allocator
  - Move ordering heuristic (root only)
- **Fixed critical Botzone crash issues**:
  - Removed expensive move ordering from inner loops (was called on every node!)
  - Conservative time limits: 1.6s/0.8s (vs 2s/1s limits)
  - Reduced memory overhead, fixed pool reset bug
- Compiled with aggressive flags: -O3 -march=native -flto

**Previous Updates** (November 12, 2025):
- Created comprehensive optimization request document for expert consultation
- Documented current performance bottlenecks (move generation 35%, BFS 30%, memory 15%)
- Prepared 10 specific optimization questions with code snippets
- Target: 50-100% more MCTS iterations through optimization

**Previous Updates** (December 10, 2025):
- Created C++ port of bot001 (4x faster, production-ready)
- Built comprehensive testing infrastructure (3 test scripts)
- Ran 50-game tournament: Python vs C++ (equal strength confirmed)
- Performance: C++ averages 0.925s vs Python's 3.843s per move
- Documentation: Complete implementation guide for C++ version

**Previous Updates** (January 8, 2025):
- Created comprehensive bot001 implementation documentation (700+ lines)
- Established standardized development workflows
- Reorganized development rules for better maintainability

See [`memorybank/progress.md`](memorybank/progress.md) for detailed status.

## Bot Architecture

### Bot001: Multi-Component MCTS (Python & C++)

Available in both Python (`bot001.py`) and C++ (`bot001.cpp`) with identical algorithms.

**Components**:
- **Multi-Component Evaluation**: Five strategic factors combined
  - **Queen Territory**: BFS-based territory control
  - **King Territory**: Weighted close-range control  
  - **Queen Position**: Exponential decay scoring (2^-d)
  - **King Position**: Distance-weighted positioning
  - **Mobility**: Available moves count
- **Phase-Aware Weighting**: Different weights for early/mid/late game
  - Early game (turns 1-10): Emphasizes positioning
  - Mid game (turns 11-20): Balanced approach
  - Late game (turns 21+): Focus on territory and mobility
- **Dynamic UCB Constant**: Exploration decreases as game progresses
  - Formula: `C = 0.177 * exp(-0.008 * (turn - 1.41))`
- **MCTS Search**: Monte Carlo Tree Search with dynamic UCT selection
  - No random rollouts (uses multi-component evaluation)
  - Tree reuse between turns via long-running mode
- **Long-Running Mode**: Maintains state across turns for efficiency

**Performance**:

Python version:
- First turn: 12s limit (using 5.8s conservatively)
- Subsequent turns: 4s limit (using 3.8s with buffer)
- Average: 3.8s per move
- MCTS iterations: 3,000-8,000 per turn

C++ version (4x faster):
- First turn: 2s limit (using 1.8s conservatively)
- Subsequent turns: 1s limit (using 0.9s with buffer)
- Average: 0.9s per move
- MCTS iterations: 12,000-32,000 per turn
- No external dependencies

## Usage

### Running Locally

**Test Python bot:**
```bash
echo "1
-1 -1 -1 -1 -1 -1" | python bots/bot001.py
```

**Test C++ bot:**
```bash
echo "1
-1 -1 -1 -1 -1 -1" | ./bots/bot001_cpp
```

**Run functionality tests:**
```bash
python3 scripts/test_bot_simple.py
```

**Run tournament (Python vs C++):**
```bash
python3 scripts/tournament.py --games 50 --parallel 10
```

### Submitting to Botzone

**Recommended: C++ version** (4x faster, no dependencies)

1. Submit `bot001.cpp` as source file
2. Select language: C++
3. Compilation: `g++ -O2 -std=c++11 -o bot bot001.cpp`
4. Enable settings:
   - ✅ Use Simplified Interaction
   - ✅ Use Long-Running Mode
5. Test and monitor performance

**Alternative: Python version**

1. Submit `bot001.py` as source file
2. Select language: Python 3
3. Dependencies: NumPy (usually pre-installed)
4. Enable same settings as above

## Development Workflow

1. **Make changes** to bot code or add new features
2. **Test locally** using scripts in `scripts/` directory
3. **Update documentation** in `memorybank/` if significant changes
4. **Commit changes** with descriptive messages
5. **Submit to Botzone** for real-world testing
6. **Analyze results** and iterate

## Platform Constraints

### Time Limits (Botzone)
- **Python Long-Running Bots**:
  - First turn: 12 seconds
  - Subsequent turns: 4 seconds
- **C++ Long-Running Bots**:
  - First turn: 2 seconds
  - Subsequent turns: 1 second

### Resource Limits
- Memory: 256 MB (default)
- CPU: Single core (multi-threading not beneficial)

## Documentation

### Memory Bank
Comprehensive project documentation is maintained in the `memorybank/` directory:

- [`projectbrief.md`](memorybank/projectbrief.md) - Project overview and objectives
- [`productContext.md`](memorybank/productContext.md) - Purpose and user experience
- [`systemPatterns.md`](memorybank/systemPatterns.md) - Architecture and design decisions
- [`techContext.md`](memorybank/techContext.md) - Technologies and constraints
- [`activeContext.md`](memorybank/activeContext.md) - Current state and next steps
- [`progress.md`](memorybank/progress.md) - Development progress and milestones

### Bot Implementation
Detailed technical documentation for bot implementations:

- [`docs/bot_implementation/bot001_implementation.md`](docs/bot_implementation/bot001_implementation.md) - Comprehensive Python bot documentation covering all modules, algorithms, and design decisions
- [`docs/bot_implementation/bot001_cpp_implementation.md`](docs/bot_implementation/bot001_cpp_implementation.md) - C++ implementation guide with compilation, testing, and tournament results

## References

- [Botzone Platform](https://www.botzone.org.cn/)
- [Amazons Game Rules (Wiki)](wiki/Amazons%20-%20Botzone%20Wiki.pdf)
- [Bot Development Guide (Wiki)](wiki/Bot%20-%20Botzone%20Wiki.pdf)

## Next Steps

1. ✅ Initialize project structure and documentation
2. ✅ Create comprehensive implementation documentation
3. ✅ Establish development workflows
4. ✅ Verify bot001 functionality with all dependencies
5. ✅ Create testing infrastructure (3 test scripts)
6. ✅ Create C++ port for better performance
7. ✅ Run comprehensive tournament (50 games)
8. 🔄 Submit C++ bot to Botzone and establish baseline ELO
9. 📅 Optimize based on match analysis
10. 📅 Explore advanced features (opening book, endgame solver)

## License

[To be determined]

## Contributing

This is currently a personal project. Testing and feedback welcome!

---

**Note**: This project is in active development. Bot001 is imported from a previous project and represents the current best implementation using multi-component heuristic evaluation inspired by strong opponent bots. Future versions may explore neural network evaluation, opening books, and other advanced techniques.
