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
│   ├── bot000.cpp    # MCTS bot (identical to bot003)
│   ├── bot000        # Compiled MCTS bot binary
│   ├── bot001.py     # Python MCTS bot (Multi-Component)
│   ├── bot001.cpp    # C++ port (4x faster, production-ready)
│   ├── bot001_cpp    # Compiled C++ binary
│   ├── bot002.cpp    # Optimized C++ bot (bitboards, faster)
│   ├── bot002_cpp    # Compiled optimized binary
│   ├── bot003.cpp    # MCTS bot (identical to bot000)
│   ├── bot003        # Compiled MCTS bot binary
│   ├── bot016.cpp    # Incremental best move selection (timing fix)
│   └── bot016        # Compiled bot016 binary
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
    ├── bots/                    # Bot-related documentation
    │   ├── implementations/     # Bot implementation guides
    │   └── reports/             # Bot performance reports
    ├── interfaces/              # Bot integration documentation for GUI developers
    │   ├── bot_integration_interface.md      # Protocol specification
    │   ├── bot_selection_guide.md            # Bot catalog and selection
    │   ├── integration_examples.md           # Code patterns and examples
    │   └── improvement_suggestions.md        # Integration improvement suggestions
    ├── manuals/                # User guides
    │   └── tournament_system_manual.md   # Tournament system user guide
    ├── references/             # External references
    │   ├── deepseek/          # DeepSeek consultation documents
    │   └── gemini/            # Gemini consultation documents
    └── requests/              # Optimization and bug fix requests
        ├── cpp_bot_optimization_request.md       # Optimization request
        ├── illegal_movement_bug_solution_request.md  # Illegal move bug request
        ├── re_bug_solution_request.md           # Runtime error bug request
        └── tle_bug_solution_request.md          # TLE bug request
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

✅ **Complete**: Bot001 C++ port, testing infrastructure, bot002 optimized version, tournament validation, comprehensive bot interface documentation, and five new optimization bots (004-008)  
⚠️ **Blocked**: Bot002 has persistent TLE (Time Limit Exceeded) issue, awaiting expert consultation  
📅 **In Progress**: Systematic testing of optimization techniques via competition automation

**Recent Updates** (September 1, 2026):
- **Created bot016.cpp with incremental best move selection** ✅
  - **Base**: bot015.cpp
  - **Purpose**: Fix timing measurement inaccuracy by moving best move selection into each MCTS iteration
  - **Problem Addressed**: External time measurement (Botzone/tournament) includes time to select best move at the end, but bot015's internal timing didn't include this
  - **Key Implementation**:
    1. **Incremental best child tracking**: Added `best_child` and `max_visits` members to MCTS class
    2. **Update during backpropagation**: During each iteration, track which root child has highest visits
    3. **Immediate best move availability**: When time runs out, best move is already known (no post-loop scanning)
    4. **Optimized check**: Only updates when `node->parent == root` (direct children only)
  - **Performance Impact**: ~25% slower due to extra checks in backpropagation loop
  - **Botzone Testing**: Solution works on Botzone (timing now matches external measurement)
  - **Local Tournament Issue**: Tournament system shows bot016 slower than bot015 (954ms vs 529ms avg) - may be tournament system bug
  - **Compilation**: `g++ -std=c++17 -O2 -o bots/bot016 bots/bot016.cpp`
  - **Status**: Working on Botzone, timing accuracy improved

- **Fixed tournament system issues** ✅
  - **Issue 1 - Keep-running signal buffering**: Fixed `LongLiveBot` reading stale `>>>BOTZONE_REQUEST_KEEP_RUNNING<<<` signals from previous turns as the move
  - **Issue 2 - Missing memory stats for traditional bots**: Added `get_child_max_memory()` using `resource.getrusage(RUSAGE_CHILDREN)` for post-process memory tracking
  - **Test Results**: Games now complete properly with memory stats for both bot types
  - **Files modified**: `scripts/tournament/bot_runner.py`, `scripts/tournament/resource_monitor.py`

**Previous Updates** (January 9, 2026):
- **Created bot015.cpp - Comprehensive time measurement** ✅
  - **Base**: bot014.cpp
  - **Purpose**: Implement precise time tracking that accounts for ALL process overhead
  - **Problem Addressed**: Previous implementations only monitored search loop time, missing overhead from input reading, board restoration, MCTS construction, and parameter setup
  - **Key Implementation**:
    - **Timing inside search()**: Pass `program_start_time`, `original_time_limit`, and `safety_margin` to search method
    - **Comprehensive overhead tracking**: Calculate elapsed time at beginning of search() from program start
    - **Adjusted time limit**: Compute `adjusted_limit = original_limit - elapsed_time - safety_margin` before MCTS loop
    - **Optimized safety margin**: 0.02s (down from 0.10s) for better time utilization
    - **Failsafe**: Minimum 0.05s search time prevents edge cases
  - **Compilation**: `g++ -std=c++17 -O2 -o bots/bot015 bots/bot015.cpp`
  - **Status**: Compiled successfully, ready for Botzone testing to verify improved time management
  - **Advantage**: Timing now precisely matches Botzone's monitoring of entire process

- **Created bot014.cpp - Non-long-live version of bot010** ✅
  - **Base**: bot010.cpp
  - **Purpose**: Solve memory allocation chaos and imprecise time monitoring caused by long-live mode
  - **Key Changes**:
    - Removed long-live mode (no `>>>BOTZONE_REQUEST_KEEP_RUNNING<<<` output)
    - Single-turn execution (bot exits after outputting move)
    - No tree reuse (removed all `advance_root()` calls)
    - Simplified main function for single-turn processing
  - **Advantages**: Predictable memory usage, precise time monitoring, simpler debugging, standard Botzone protocol
  - **Compilation**: `g++ -std=c++17 -O3 -o bots/bot014 bots/bot014.cpp`
  - **Status**: Compiled successfully, ready for testing vs bot010

**Recent Updates** (January 8, 2026):
- **Created bot010.cpp with MCTS evaluation optimization** ✅
  - **Base**: bot009.cpp
  - **Improvement**: Eliminates heap allocations from evaluation function for 3-5x performance boost
  - **Implementation**: 
    - Static buffers (dist_my, dist_op arrays, FastQueue struct)
    - perform_fast_bfs() replaces bfs_territory() with fixed arrays
    - evaluate_optimized() replaces evaluate_multi_component() with single-pass scoring
    - Removed STL containers from critical path (<deque>, <unordered_map>, <tuple>)
  - **Compilation**: `g++ -std=c++11 -O3 -o bots/bot010 bots/bot010.cpp`
  - **Expected Performance**: 3-5x increase in MCTS iterations per second
  - **Status**: Compiled successfully, ready for performance testing

- **Created bot009.cpp by integrating opponent.cpp weights into bot003** ✅
  - **Improvement**: Uses sophisticated 28x6 weight array from opponent.cpp instead of EARLY/MID/LATE weights
  - **Implementation**: 
    - Replaced EARLY/MID/LATE weight arrays with opponent.cpp's ARGS array
    - Updated `get_phase_weights()` to use opponent.cpp's 28-turn weight progression
    - Uses only first 5 weights from each row (opponent.cpp has 6 components)
  - **Compilation**: `g++ -std=c++11 -O2 -o bots/bot009 bots/bot009.cpp`
  - **Testing**: Verified with basic test input, produces valid moves
  - **Status**: Fully functional and ready for testing against other bots

**Recent Updates** (December 26, 2025):
- **Created five new C++ bots with optimization techniques** ✅
  - **bot004.cpp**: Move ordering heuristics (sorts moves by centrality and arrow proximity)
  - **bot005.cpp**: Transposition table (caches evaluations using Zobrist hashing)
  - **bot006.cpp**: Progressive widening (limits child expansion based on node visits)
  - **bot007.cpp**: Bitboard representation (3x uint64_t for faster operations)
  - **bot008.cpp**: Adaptive time management (dynamic time allocation based on game phase)
  - **Status**: All bots created, compiled, and ready for systematic testing

- **Created competition automation system** ✅
  - **Script**: `scripts/run_competitions.py`
  - **Purpose**: Automate 10-game competitions between each new bot and bot003
  - **Features**: Sequential execution (respects memory constraints), detailed results collection, JSON output, markdown reports
  - **Output**: Results in `results/competitions/`, analysis reports in `docs/analysis/`
  - **Status**: System operational, initial tests completed

- **Initial competition results** ⚠️
  - **Test**: Ran 1-game competitions for each bot vs bot003
  - **Findings**: Some bots have TLE issues (bot004, bot008) and protocol issues (bot007)
  - **Analysis**: Reports generated in `docs/analysis/` directory
  - **Next**: Full 10-game competitions needed for statistical significance

**Previous Updates** (December 25, 2025):
- **Bot Interface Documentation Created**: Comprehensive documentation for GUI integration ✅
  - **Location**: `docs/interfaces/` directory
  - **Purpose**: Enable GUI developers to integrate Amazing Amazons AI bots into their applications
  - **Documents Created**: 4 comprehensive interface documents
  - **Status**: Documentation complete and ready for GUI developers

- **Tournament System Manual Created**: Comprehensive user guide for tournament testing infrastructure ✅
  - **Document**: `docs/manuals/tournament_system_manual.md`
  - **Contents**: Overview, installation, bot requirements, CLI commands, running matches/tournaments, testing bots, compiling bots, troubleshooting, architecture, best practices
  - **Status**: Manual complete and ready for users

**Previous Updates** (December 15, 2025):
- **Bot002 TLE Request Document Created**: Comprehensive bug solution request for DeepSeek ✅
  - **Problem**: Bot002 still experiences TLE despite previous fixes (0.7s/1.4s limits + mid-iteration check)
  - **Symptom**: Bot reaches 951ms → 1000ms TLE in late-game despite 700ms limit + 150ms safety buffer
  - **Analysis**: ~300-450ms unaccounted time, late-game 3-5x slowdown, first turn anomaly
  - **Document**: `docs/requests/tle_bug_solution_request.md` with comprehensive timing analysis
  - **Questions**: 8 diagnostic questions for DeepSeek covering timing, overhead, and optimization
  - **Status**: Request document ready, will be provided with source code and logs to DeepSeek

**Previous Updates** (December 14, 2025):
- **Bot002 Runtime Error (RE) Fix**: Fixed SIGSEGV segmentation fault crashes ✅
  - **Root Cause**: Custom NodePool allocator used `vector::resize()` which invalidated all node pointers when reallocating memory
  - **Symptom**: Bot crashed on Turn 7 with signal 11 after 6 successful turns
  - **Solution** (from DeepSeek):
    1. Replaced NodePool with `std::deque<MCTSNode>` for pointer stability
    2. Removed tree reuse (`advance_root()`) - rebuild tree each turn
    3. Added `reset()` method to clear tree between turns
  - **Trade-offs**: Slightly slower (no tree reuse) but 100% stable with simpler code
  - **Documentation**: `docs/bots/implementations/bot002_re_fix.md` and `docs/requests/re_bug_solution_request.md`
  - Git commit: dce4e5c
  
- **Bot002 Critical Bug Fixes**: Fixed TWO major bugs causing illegal moves on Botzone ✅
  - **Bug 1 - MCTS Selection Phase**: Wrong player color used (`1 - node->player_just_moved` instead of correct `node->player_just_moved`)
    - Impact: Corrupted simulation state, MCTS tree diverged from actual board
  - **Bug 2 - Replay Loop**: Applied both request and response lines from Botzone
    - Impact: Each move applied twice with alternating colors, corrupting bitboard via XOR operations
    - Fix: Only process odd-indexed lines (actual responses), skip even-indexed duplicates
  - Added defensive assertion in DEBUG mode for early error detection
  - Updated .clinerules with sequential testing requirement
  - Comprehensive documentation: `docs/bots/implementations/bot002_illegal_move_fix.md`
  - Git commit: a6ea4d3
  
- **Status**: Bot002 fully fixed (both illegal moves and crashes), stable, and ready for Botzone deployment
- **Task Completion Workflow Enhanced**: Improved workflow to enforce mandatory sequential execution
  - Problem: Steps were being skipped, memory bank files not reviewed before updates
  - Solution: Complete rewrite of `.clinerules/workflows/task_completion.md`
  - Added mandatory 4-step sequence: (1) Review ALL memory bank files → (2) Update files one by one → (3) Update README → (4) Clear git status
  - Multiple safeguards: Warning messages, checkpoints, "STOP HERE" instructions, completion checklist
  - Result: Workflow now prevents skipping steps and ensures thorough updates
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

### Available Bots

The project includes several bot implementations with varying levels of sophistication:

#### Bot000: MCTS Bot (Identical to Bot003)
- **Language**: C++
- **Algorithm**: Multi-Component MCTS (similar to Bot001)
- **Features**: Phase-aware weighting, dynamic UCB constant, long-running mode
- **Performance**: Similar to Bot001 C++ version
- **Purpose**: Baseline MCTS implementation for testing and comparison

#### Bot001: Multi-Component MCTS (Primary Bot)
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

#### Bot002: Optimized Bitboard MCTS
- **Language**: C++
- **Algorithm**: MCTS with bitboard representation and optimized BFS
- **Features**: Bitboard move generation, Xorshift64 PRNG, node pool allocator
- **Performance**: Very fast (1.128s per move average)
- **Status**: Stable but has TLE (Time Limit Exceeded) issue in late game
- **Current Focus**: TLE bug resolution with DeepSeek consultation

#### Bot003: MCTS Bot (Identical to Bot000)
- **Language**: C++
- **Algorithm**: Multi-Component MCTS (similar to Bot001)
- **Features**: Phase-aware weighting, dynamic UCB constant, long-running mode
- **Performance**: Similar to Bot001 C++ version
- **Purpose**: Baseline bot for testing optimization techniques

#### Bot004: Move Ordering Heuristics
- **Language**: C++
- **Algorithm**: Multi-Component MCTS with move ordering
- **Features**: Sorts moves by centrality and arrow proximity before MCTS expansion
- **Goal**: Improve search efficiency by exploring promising moves first
- **Status**: Created and compiled, initial testing shows TLE issues

#### Bot005: Transposition Table
- **Language**: C++
- **Algorithm**: Multi-Component MCTS with transposition table
- **Features**: Caches evaluation results using Zobrist hashing (2^20 entries)
- **Goal**: Avoid recomputing evaluations for identical positions
- **Status**: Created and compiled, ready for testing

#### Bot006: Progressive Widening
- **Language**: C++
- **Algorithm**: Multi-Component MCTS with progressive widening
- **Features**: Limits child expansion based on node visits (sqrt(visits) children)
- **Goal**: Focus search on most promising branches in high-branching positions
- **Status**: Created and compiled, ready for testing

#### Bot007: Bitboard Representation
- **Language**: C++
- **Algorithm**: Multi-Component MCTS with bitboard representation
- **Features**: Uses 3x uint64_t bitboards instead of 8x8 array
- **Goal**: Faster move generation and board operations
- **Status**: Created and compiled, initial testing shows protocol issues

#### Bot008: Adaptive Time Management
- **Language**: C++
- **Algorithm**: Multi-Component MCTS with adaptive time management
- **Features**: Dynamically adjusts time per move based on game phase and remaining time
- **Goal**: Better time allocation for critical positions
- **Status**: Created and compiled, initial testing shows TLE issues

#### Bot009: Opponent.cpp Weight Integration
- **Language**: C++
- **Algorithm**: Multi-Component MCTS with opponent.cpp's sophisticated weight array
- **Features**: Uses 28x6 weight array from opponent.cpp instead of EARLY/MID/LATE weights
  - Turns 0-27: Use corresponding row from ARGS array
  - Turns ≥28: Use last row (index 27) as fallback
  - Uses only first 5 weights from each row (opponent.cpp has 6 components)
- **Goal**: Leverage opponent.cpp's optimized weight tuning for better evaluation
- **Status**: Created, compiled, and verified with basic testing

#### Bot016: Incremental Best Move Selection
- **Language**: C++
- **Algorithm**: Multi-Component MCTS with incremental best move tracking
- **Base**: bot015.cpp
- **Features**: 
  - **Incremental best child tracking**: Tracks best move during each MCTS iteration
  - **Timing accuracy**: Fixes measurement discrepancy between internal and external timing
  - **Optimized check**: Only updates when `node->parent == root` (direct children only)
- **Goal**: Make internal time measurement match external (Botzone/tournament) timing
- **Performance**: ~25% slower than bot015 due to extra checks in backpropagation loop
- **Botzone Testing**: Works on Botzone with improved timing accuracy
- **Local Tournament Issue**: Shows slower performance (954ms vs 529ms avg) - may be tournament system bug
- **Status**: Working on Botzone, timing accuracy improved

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

- [`docs/bots/implementations/bot001_implementation.md`](docs/bots/implementations/bot001_implementation.md) - Comprehensive Python bot documentation covering all modules, algorithms, and design decisions
- [`docs/bots/implementations/bot001_cpp_implementation.md`](docs/bots/implementations/bot001_cpp_implementation.md) - C++ implementation guide with compilation, testing, and tournament results

### Bot Interface Documentation
Comprehensive documentation for GUI developers to integrate Amazing Amazons AI bots:

- [`docs/interfaces/bot_integration_interface.md`](docs/interfaces/bot_integration_interface.md) - Detailed Botzone protocol specification and integration patterns
- [`docs/interfaces/bot_selection_guide.md`](docs/interfaces/bot_selection_guide.md) - Bot catalog with characteristics and selection criteria
- [`docs/interfaces/integration_examples.md`](docs/interfaces/integration_examples.md) - Implementation examples in Python, C++, JavaScript
- [`docs/interfaces/improvement_suggestions.md`](docs/interfaces/improvement_suggestions.md) - Recommendations for enhanced integration

### Tournament System
User guide for the tournament testing infrastructure:

- [`docs/manuals/tournament_system_manual.md`](docs/manuals/tournament_system_manual.md) - Comprehensive guide covering CLI commands, running matches/tournaments, testing bots, compiling bots, troubleshooting, and best practices

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
9. ✅ Create five optimization bots (004-008) and competition automation system
10. 📅 Run full 10-game competitions for each optimization bot vs bot003
11. 📅 Analyze results to identify most effective optimization techniques
12. 📅 Explore advanced features (opening book, endgame solver)

## License

[To be determined]

## Contributing

This is currently a personal project. Testing and feedback welcome!

---

**Note**: This project is in active development. Bot001 is imported from a previous project and represents the current best implementation using multi-component heuristic evaluation inspired by strong opponent bots. Future versions may explore neural network evaluation, opening books, and other advanced techniques.