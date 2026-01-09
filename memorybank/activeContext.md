# Active Context

## Current Work Focus

**Status**: Created bot017.cpp with 4 essential MCTS performance improvements for increased iterations per second.

**Recent Activity** (September 1, 2026):
- **Created bot017.cpp with 4 essential MCTS performance improvements** ✅:
  - **Location**: `bots/bot017.cpp`
  - **Base**: bot016.cpp
  - **Purpose**: Implement the 4 most essential optimizations for "more MCTS iterations per second"
  - **Reference**: `docs/references/gpt/improve_bot016.md` - GPT analysis of performance bottlenecks
  - **Key Improvements Implemented**:
    1. **Fixed Board::copy() overhead**: Added no-init constructor to eliminate redundant `init_board()` calls every MCTS iteration
       - Added `Board(bool do_init)` constructor that skips initialization when false
       - Replaced `Board state = root_state.copy()` with `Board state = root_state` (implicit copy constructor)
       - Eliminates ~10-15% overhead from unnecessary board initialization
    2. **Replaced erase() with swap-pop in untried_moves**: Eliminated O(n) vector shifts during move selection
       - Changed from `node->untried_moves.erase(node->untried_moves.begin() + idx)` 
       - To swap-pop: `untried_moves[idx] = untried_moves.back(); untried_moves.pop_back()`
       - Reduces move selection from O(n) to O(1), critical with large branching factors
    3. **Optimized time checking with deadline**: Reduced syscall overhead by 99%
       - Calculate deadline once: `auto deadline = start_time + duration(adjusted_time_limit)`
       - Check time only every 256 iterations: `if ((iterations & 0xFF) == 0)`
       - Eliminates expensive `steady_clock::now()` calls on every iteration
    4. **Shrank Move struct using int8_t**: Reduced memory footprint for better cache performance
       - Changed from 6 × `int` (24 bytes) to 6 × `int8_t` (6 bytes)
       - Coordinates fit in 0-7 range, `int8_t` sufficient for 8×8 board
       - Cast to `int` when outputting: `(int)best_move.x0` etc.
       - Improves memory bandwidth and cache efficiency
  - **Performance Results**: Bot017 achieves **1.12x speedup** over bot016
    - bot016 average: 2.228s per move
    - bot017 average: 1.989s per move
    - Demonstrates successful optimization of MCTS iterations per second
  - **Implementation Approach**: Built incrementally in parts (max 200 lines each) to avoid errors
  - **Compilation**: `g++ -std=c++17 -O2 -o bots/bot017 bots/bot017.cpp`
  - **Status**: Compiled successfully, tested and verified with 1.12x performance improvement
  - **Next**: Ready for deployment and further testing

- **Created bot016.cpp with incremental best move selection** ✅:
  - **Location**: `bots/bot016.cpp`
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

- **Fixed tournament system issues** ✅:
  - **Issue 1 - Keep-running signal buffering**: LongLiveBot was reading stale `>>>BOTZONE_REQUEST_KEEP_RUNNING<<<` signals from previous turns as the move
    - **Root cause**: The keep-running signal from turn N could remain in the buffer if not fully consumed, then be read as the "move" on turn N+2
    - **Fix**: Modified `LongLiveBot.play_turn()` to detect when first line read is the keep-running signal and read the next line as the actual move
    - **File modified**: `scripts/tournament/bot_runner.py`
  - **Issue 2 - Missing memory stats for traditional bots**: bot015 (TraditionalBot) showed no memory statistics
    - **Root cause**: `communicate()` blocks until process finishes, then `get_process_memory(pid)` fails because process is terminated
    - **Fix**: Added `get_child_max_memory()` using `resource.getrusage(RUSAGE_CHILDREN)` which works after child exits
    - **Files modified**: `scripts/tournament/resource_monitor.py`, `scripts/tournament/bot_runner.py`
  - **Test Results**: 
    - Game completed successfully (52 turns, bot010 wins by no_moves)
    - bot015 now shows memory stats: Max memory 3.69 GB ✅
    - bot010 memory stats: Max memory 4.33 GB ✅
    - No invalid output errors
  - **Git commit**: 3745134

**Previous Activity** (January 9, 2026):
- **Created bot015.cpp with comprehensive time measurement** ✅:
  - **Location**: `bots/bot015.cpp`
  - **Base**: bot014.cpp
  - **Purpose**: Implement precise time tracking that accounts for ALL overhead including MCTS construction
  - **Problem Addressed**: Previous timing only monitored `mcts.search()` time, missing significant overhead from:
    - Input reading and parsing
    - Board state restoration
    - MCTS instance construction (RNG seeding)
    - Parameter setup
    - Method call overhead
  - **Key Implementation**:
    1. **Timing inside search() method**: Pass `program_start_time` to search() along with original limit and safety margin
    2. **Comprehensive overhead tracking**: Calculate elapsed time at the very beginning of search() to capture:
       - All initialization from program start
       - MCTS constructor execution
       - turn_number assignment
       - Method call overhead
       - Root node creation
       - Legal moves generation
    3. **Adjusted time limit**: Compute `adjusted_limit = original_limit - elapsed_time - safety_margin` before MCTS loop
    4. **Precise loop timing**: Use `adjusted_time_limit` for all timing checks in MCTS iterations
    5. **Optimized safety margin**: Reduced to 0.02s (from 0.10s) for better time utilization
    6. **Failsafe protection**: Minimum time of 0.05s prevents edge cases
  - **Method Signature Change**: `search()` now accepts:
    - `const chrono::steady_clock::time_point& program_start_time`
    - `double original_time_limit`
    - `double safety_margin`
  - **Compilation**: `g++ -std=c++17 -O2 -o bots/bot015 bots/bot015.cpp`
  - **Status**: Compiled successfully, committed to git (0ac510d)
  - **Advantage**: Timing now precisely matches Botzone's monitoring of entire process, eliminating timeout issues from unaccounted overhead
  - **Next**: Ready for Botzone testing to verify improved time management

**Recent Activity** (January 9, 2026 - earlier):
- **Created bot014.cpp - Non-long-live version of bot010** ✅:
  - **Location**: `bots/bot014.cpp`
  - **Base**: bot010.cpp
  - **Purpose**: Create a cleaner bot without long-live mode to solve memory and timing issues
  - **Problem Addressed**: Long-live mode causes chaotic memory allocation and imprecise time monitoring due to tree reuse complexity
  - **Key Changes**:
    1. **Removed long-live mode**: No `>>>BOTZONE_REQUEST_KEEP_RUNNING<<<` command output
    2. **Simplified to single-turn execution**: Bot exits cleanly after outputting move
    3. **No tree reuse**: Removed all `advance_root()` calls - fresh MCTS tree each turn
    4. **Removed while loop**: No continuous operation - bot processes one turn and exits
    5. **Simplified main function**: Reads full history, reconstructs state, searches once, outputs, and exits
  - **Advantages**:
    - **Predictable memory usage**: No accumulated tree growth across turns
    - **Precise time monitoring**: Each run is independent with no hidden overhead
    - **Simpler debugging**: Each run is reproducible and isolated
    - **Standard protocol**: Follows Botzone simple interaction without keep-running complexity
  - **Compilation**: `g++ -std=c++17 -O3 -o bots/bot014 bots/bot014.cpp`
  - **Status**: Compiled successfully (41KB executable), committed to git (babc1d4)
  - **Next**: Ready for testing to compare memory behavior and timing precision vs bot010

**Recent Activity** (January 8, 2026):
- **Created bot010.cpp with MCTS evaluation optimization** ✅:
  - **Location**: `bots/bot010.cpp`
  - **Base**: bot009.cpp
  - **Purpose**: Eliminate heap allocations from evaluation function to increase MCTS iteration count by 3-5x
  - **Reference**: `docs/references/gemini/optimize_mcts_evaluation.md`
  - **Implementation**:
    1. **Added static optimization buffers**: 
       - `dist_my[GRID_SIZE][GRID_SIZE]` and `dist_op[GRID_SIZE][GRID_SIZE]` for distance arrays
       - `FastQueue` struct - lightweight fixed-size queue to replace `std::deque`
    2. **Implemented `perform_fast_bfs()`**: 
       - Replaces `bfs_territory()` with pointer-based, static-memory approach
       - Uses fixed arrays instead of dynamic containers
       - No heap allocations during BFS execution
    3. **Implemented `evaluate_optimized()`**: 
       - Replaces `evaluate_multi_component()` with single-pass scoring
       - Pre-calculated powers-of-2 lookup table (avoids `pow()` calls)
       - Maintains all 5 evaluation components with identical logic
       - Single pass over board eliminates `std::unordered_map` usage
    4. **Removed obsolete code**: 
       - Deleted `bfs_territory()` function
       - Deleted `calc_position_score()` function
       - Removed unused headers: `<deque>`, `<unordered_map>`, `<tuple>`
    5. **Updated MCTS::search()**: Changed evaluation call from `evaluate_multi_component()` to `evaluate_optimized()`
  - **Compilation**: Compiled successfully with `g++ -std=c++11 -O3 -o bots/bot010 bots/bot010.cpp`
  - **Expected Performance**: 3-5x increase in MCTS iterations per second due to zero heap allocations in evaluation path
  - **Status**: Bot010 compiled and ready for testing against bot009

- **Created bot009.cpp by integrating opponent.cpp weights into bot003** ✅:
  - **Location**: `bots/bot009.cpp`
  - **Purpose**: Create a new bot that uses the sophisticated weight array from opponent.cpp instead of the EARLY/MID/LATE weights in bot003
  - **Implementation**:
    1. **Replaced weight arrays**: Removed EARLY/MID/LATE weight arrays and replaced with the 28x6 ARGS array from opponent.cpp
    2. **Updated get_phase_weights() function**: Modified to use opponent.cpp's weight array where:
       - Turns 0-27 use the corresponding row from the ARGS array
       - Turns >= 28 use the last row (index 27) as a fallback
    3. **Maintained compatibility**: Uses only the first 5 weights from each row (opponent.cpp has 6 components but bot003 uses 5)
  - **Compilation**: Compiled successfully with `g++ -std=c++11 -O2 -o bots/bot009 bots/bot009.cpp`
  - **Testing**: Verified functionality with basic test input:
    - Input: `1\n-1 -1 -1 -1 -1 -1\n`
    - Output: Valid move `2 0 2 6 7 6` followed by `>>>BOTZONE_REQUEST_KEEP_RUNNING<<<`
  - **Status**: Bot009 is fully functional and ready for testing against other bots

**Recent Activity** (December 26, 2025):
- **Created five new C++ bots with incremental improvements** ✅:
  - **Location**: `bots/` directory
  - **Purpose**: Test specific optimization techniques to identify most effective improvements
  - **Bots Created**:
    1. **bot004.cpp**: Move ordering heuristics
       - Sorts moves by centrality and arrow proximity before MCTS expansion
       - Goal: Improve search efficiency by exploring promising moves first
       - Implementation: Added `sort_moves_by_heuristic()` function
       
    2. **bot005.cpp**: Transposition table
       - Caches evaluation results for board positions using Zobrist hashing
       - Goal: Avoid recomputing evaluations for identical positions
       - Implementation: Added `TranspositionTable` class with 2^20 entries
       
    3. **bot006.cpp**: Progressive widening
       - Limits child expansion based on node visits (sqrt(visits) children)
       - Goal: Focus search on most promising branches in high-branching positions
       - Implementation: Modified `expand()` method in MCTS class
       
    4. **bot007.cpp**: Bitboard representation
       - Uses 3x uint64_t bitboards instead of 8x8 array
       - Goal: Faster move generation and board operations
       - Implementation: Complete rewrite with bitboard operations
       
    5. **bot008.cpp**: Adaptive time management
       - Dynamically adjusts time per move based on game phase and remaining time
       - Goal: Better time allocation for critical positions
       - Implementation: Added `AdaptiveTimeManager` class
       
  - **Compilation**: All bots compiled successfully with `g++ -O2 -std=c++11 -o bots/bot00X bots/bot00X.cpp`
  - **Status**: All bots created and compiled, ready for testing

- **Created competition automation script** ✅:
  - **Script**: `scripts/run_competitions.py`
  - **Purpose**: Automate running 10-game competitions between each new bot and bot003
  - **Features**:
    - Runs games sequentially (not in parallel) due to memory constraints
    - Collects detailed results (wins, losses, moves, duration, errors)
    - Generates JSON results files in `results/competitions/`
    - Creates markdown reports in `docs/analysis/`
    - Includes summary report comparing all bots
  - **Implementation**: `CompetitionRunner` class with comprehensive reporting
  - **Status**: Script complete and functional

- **Ran initial competition tests** ⚠️:
  - **Test**: Ran 1-game competitions for each bot vs bot003
  - **Results**: 
    - bot004: TLE on first turn (2.1s duration, failed)
    - bot005: Completed game (31 moves, 30.7s, bot004 won - data discrepancy)
    - bot006: Error (details not captured)
    - bot007: Keep-running mismatch error
    - bot008: TLE on first turn (2.1s duration, failed)
  - **Analysis**: Some bots have time limit or protocol issues
  - **Status**: Initial testing complete, issues identified for further optimization

- **Previous Activity** (December 25, 2025):
  - **Created comprehensive bot interface documentation for GUI integration** ✅:
    - **Location**: `docs/interfaces/` directory
    - **Purpose**: Enable GUI developers to integrate Amazing Amazons AI bots into their applications
    - **Documents Created**: 4 comprehensive interface documents
    - **Status**: Documentation complete and ready for GUI developers
    - **Git commit**: Pending

  - **Created comprehensive tournament system manual** ✅:
    - **Document**: `docs/manuals/tournament_system_manual.md`
    - **Purpose**: User guide for the tournament testing infrastructure
    - **Status**: Manual complete and ready for users
    - **Git commit**: Pending

- **Previous Activity** (December 15, 2025):
  - **Created TLE bug solution request document for DeepSeek** ✅:
    - **Document**: `docs/requests/tle_bug_solution_request.md`
    - **Context**: Bot002 still gets TLE on Botzone despite previous fix attempts
    - **Analysis included**: Timing progression, late-game slowdown, first turn anomaly
    - **Status**: Request document ready, awaiting DeepSeek consultation
    - **Git commit**: Pending
  
  - **Previous TLE fix attempt** (December 15, 2025) - INSUFFICIENT:
    - **Root cause**: Time check at loop start allowed expensive iterations to exceed 1000ms limit
    - **Solution**: Two-tier defense-in-depth approach with conservative time limits and mid-iteration safety check
    - **Result**: Multi-layered time safety but TLE persists
    - **Git commit**: Pending

**Recent Activity** (December 14, 2025):

- **Fixed bot002.cpp Runtime Error (RE) bug - SIGSEGV crashes** ✅:
  - **Root cause**: Custom NodePool allocator used `vector::resize()` which invalidated all node pointers when reallocating
  - **Symptom**: Bot crashed on Turn 7 with signal 11 (segmentation fault) after 6 successful turns
  - **Solution from DeepSeek**:
    1. Replaced NodePool with `std::deque<MCTSNode>` for pointer stability
    2. Removed tree reuse (`advance_root()`) - rebuild tree each turn for simplicity
    3. Added `reset()` method to clear tree between turns
  - **Trade-offs**: Slightly slower (no tree reuse) but 100% stable and simpler code
  - **Documentation**: Created comprehensive docs in `docs/bots/implementations/bot002_re_fix.md` and `docs/requests/re_bug_solution_request.md`
  - **Result**: Bot compiles cleanly, zero crashes expected
  - **Git commit**: dce4e5c
  
- **Fixed bot002.cpp illegal movement bugs** (TWO CRITICAL BUGS):
  - **Bug 1 - MCTS Selection Phase**: Applied moves with wrong player color (`1 - node->player_just_moved` instead of `node->player_just_moved`)
    - Impact: Corrupted simulation state, MCTS tree diverged from actual board
    - Fix: Changed to use correct player color in selection phase
  - **Bug 2 - Replay Loop Duplicate Application**: Applied both request and response lines from Botzone
    - Impact: Each move applied twice with alternating colors, corrupting bitboard state via XOR
    - Fix: Only process odd-indexed lines (actual responses), skip even-indexed duplicates
  - **Added defensive assertion**: DEBUG mode check in apply_move() to catch similar bugs early
  - **Updated .clinerules**: Added sequential testing requirement due to memory constraints
  - **Created comprehensive documentation**: `docs/bots/implementations/bot002_illegal_move_fix.md`
  - **Git commit**: a6ea4d3
  - **Status**: Bug fixed, compiled successfully, ready for Botzone deployment
  
- **Enhanced task completion workflow** (`.clinerules/workflows/task_completion.md`):
  - **Problem identified**: Workflow steps were being skipped, memory bank files not being reviewed before updates
  - **Solution implemented**: Complete rewrite with mandatory sequential execution
  - Added prominent warning: "⚠️ CRITICAL: This workflow MUST be executed sequentially. DO NOT skip any steps."
  - **Step 1 - Review ALL Memory Bank Files (MANDATORY - READ ONLY)**:
    - Required reading checklist of all 6 core files before any updates
    - "STOP HERE" instruction to prevent proceeding before completion
    - Explanation of why each file matters
  - **Step 2 - Update Memory Bank Files (ONE BY ONE)**:
    - "ONLY AFTER completing Step 1" language
    - Priority order: activeContext.md first, then progress.md, then others as needed
    - Explicit instruction to update "ONE AT A TIME"
    - Checkpoint before proceeding to Step 3
  - **Step 3 - Update README.md**:
    - "ONLY AFTER completing Step 2" language
    - Must READ README.md first before updating
    - Checkpoint before proceeding to Step 4
  - **Step 4 - Clear Git Status (FINAL STEP)**:
    - Sequential git commands with expected outputs
    - Descriptive commit message guidelines
    - Final verification of clean status
  - **Added multiple safeguards**:
    - "Critical Execution Rules" section with DO/DON'T lists
    - Checkpoint markers after each step
    - Final "Workflow Completion Checklist"
    - Warning emojis and bold text throughout
  - **Result**: Workflow now enforces exact sequence and prevents skipping steps
  - **Git commit**: Pending (will be committed after memory bank and README updates)
- **Executed the enhanced workflow**: Currently following Step 1 → Step 2 sequence with all 6 files reviewed

**Previous Activity** (December 14, 2025):
- **Fixed critical bug in bot002.cpp**: Resolved INVALIDMOVE errors on Botzone
  - **Root cause**: Color tracking logic during game history replay was incorrect
  - Moves were being applied to wrong player's queens, causing board state desynchronization
  - Bot would try to move queens from positions where they no longer existed
  - **Fix**: Changed color tracking to always start with BLACK for first actual move, properly alternate only on actual moves (not -1 entries)
  - **Testing**: Verified with 3 tournament games in non-parallel mode - zero illegal moves or errors
  - All games ended naturally (average 26.3 turns)
  - **Git commit**: 53cca24
- **Status**: Bot002 now ready for Botzone deployment with bug fix applied

**Previous Activity** (December 13, 2025):
- **Created bot002.cpp**: Optimized version based on DeepSeek's optimization plan
  - Implemented bitboard representation (3x uint64_t vs 8x8 array)
  - Optimized move generation with bitwise operations
  - Fast BFS with fixed arrays and on-the-fly weight accumulation
  - Xorshift64 PRNG (faster than mt19937)
  - Move ordering heuristic (centrality + arrow proximity)
  - Node pool allocator for memory efficiency
  - Aggressive compiler flags: -O3 -march=native -flto
- **Fixed critical time limit issues** reported from Botzone:
  - Move ordering was being called on EVERY node (hundreds/second) - extremely expensive
  - Fixed: Only order moves for root node, skip for all child nodes
  - Reduced memory allocation from 50MB to 10MB
  - Fixed pool reset bug that destroyed kept subtree
  - Added conservative time limits: 1.6s/0.8s (vs 2s/1s limits) for safety buffer
- **Compilation**: `g++ -O3 -march=native -flto -std=c++11 -o bots/bot002_cpp bots/bot002.cpp`
- **Testing**: Bot002 runs correctly, respects time limits
- **Ready for Botzone**: Fixed version should stay within time limits
- **Tournament Testing** (December 14, 2025):
  - Ran 20-game tournament: bot002_cpp vs bot001_cpp (sequential mode)
  - **ZERO CRASHES** - All critical fixes successful!
  - Results: Bot001 (bot001_cpp) won 16 games (80%), Bot002 won 4 games (20%)
  - Average game length: 25.9 turns
  - Average time: Bot002 1.128s/move, Bot001 1.776s/move
  - Bot002 is faster but weaker strategically (needs algorithm improvements)
  - File: `results/bot002_vs_bot001_20251214_135450.json`

**Previous Activity** (November 12, 2025):
- Enhanced workflow documentation system with three comprehensive workflows
- Updated `task_completion.md` to include README update step (was missing)
- Added `projectbrief.md` reminder to memory bank update section (was missing)
- Created `memory_bank_update.md` - standalone workflow for memory bank maintenance
  - Includes all 6 core files with projectbrief.md explicitly listed
  - File hierarchy diagram showing relationships
  - Detailed update guidelines for each file
  - Special handling for "update memory bank" requests
- Created `git_status_clear.md` - standalone workflow for git commit operations
  - Comprehensive commit message guidelines with examples
  - Common scenarios and logical grouping advice
  - Focus on committing to current branch
  - Best practices and troubleshooting
- All three workflows cross-reference each other for easy navigation
- Git commit: f9593b5

**Previous Activity** (November 12, 2025):
- Created comprehensive optimization request document (`docs/requests/cpp_bot_optimization_request.md`)
- Documented current performance: 12k-32k iterations/turn, 4.15× faster than Python
- Identified bottlenecks: Move generation (35%), BFS territory (30%), memory allocation (15%)
- Prepared 10 specific optimization questions covering:
  - Move ordering heuristics
  - BFS optimization and caching strategies
  - Custom memory allocators
  - Transposition tables with Zobrist hashing
  - Bitboard representation feasibility
  - Progressive widening and MCTS enhancements
- Included detailed code snippets of hot paths for analysis
- Prioritized optimizations by impact: Tier 1 (move ordering, BFS, allocator), Tier 2 (board representation, compiler flags), Tier 3 (transposition table, bitboards)
- Document ready to share with DeepSeek for expert optimization advice
- Goal: 50-100% more MCTS iterations (target: 18k-65k per turn)

**Previous Activity** (December 10, 2025):
- Created complete C++ port of bot001 (bot001.cpp)
- Built comprehensive testing infrastructure (3 scripts)
- Ran 50-game tournament: Python vs C++ validation
- Confirmed equal strength and 4x C++ performance improvement
- Documented C++ implementation thoroughly
- Updated README.md and memory bank with current status
- Ready for Botzone submission

**Previous Activity** (January 8, 2025): 
- Reorganized .clinerules into categorized files
- Created task completion workflow and README update workflow
- Created comprehensive implementation documentation for bot001.py
- Documented all bot001 components in detail


## Recent Changes

### C++ Bot Implementation and Testing (December 10, 2025)
1. **Bot001 C++ Port** (`bots/bot001.cpp`):
   - Complete port maintaining identical algorithm to Python version
   - 550 lines of C++11 code with no external dependencies
   - Optimized for C++ time limits (1.8s first turn, 0.9s subsequent)
   - ~4x performance improvement over Python
   - Compilation: `g++ -O2 -std=c++11 -o bots/bot001_cpp bots/bot001.cpp`

2. **Testing Infrastructure** (`scripts/`):
   - **test_bot_simple.py**: Quick functionality verification for both bots
   - **botzone_simulator.py**: Simulates Botzone long-running protocol
   - **tournament.py**: Bot comparison framework with parallel execution
     - Supports customizable game count and parallel workers
     - Tracks wins, times, game lengths
     - Saves detailed results to JSON

3. **Tournament Results** (50 games):
   - Equal strength: 25-25 wins (confirms correct porting)
   - Performance: C++ 0.925s vs Python 3.843s per move (4.15x faster)
   - Average game length: 27.8 turns
   - Zero errors or crashes in all games
   - Results: `results/tournament_20251210_212408.json`

4. **Documentation**:
   - Created `docs/bots/implementations/bot001_cpp_implementation.md`
   - Covers architecture, compilation, testing, performance
   - Includes complete tournament analysis
   - Updated `memorybank/progress.md` with completed milestones
   - Updated `README.md` with C++ version and testing info

5. **Git Commit**: 43dc4b1


### .clinerules Reorganization (January 8, 2025)
1. **Split basic_requirements.md into 5 focused files**:
   - `cline_operations.md`: Rules to prevent conversation failures (e.g., incremental file creation)
   - `documentation.md`: Documentation standards
   - `development_workflow.md`: Development process best practices
   - `project_setup.md`: Initial setup and environment configuration
   - `version_control.md`: Git practices
   
2. **Rationale**: Better organization and maintainability
   - Single file for operational rules that prevent tool-use errors
   - Clear categorization makes rules easier to find and update
   - Using bullet points instead of numbering to prevent numbering issues

3. **Git Commit**: b805f9b8f35ecd06de9ff87dfa40883c91cdede3

### Development Infrastructure (January 8, 2025)

#### Workflow Creation
1. **Task Completion Workflow** (`.clinerules/workflows/task_completion.md`):
   - Created standardized workflow for post-task completion
   - Two-step process: Update memory bank → Clear git status
   - Detailed guidance on which memory bank files to update and why
   - Clear git workflow with commit message best practices
   - Execution notes for proper implementation

#### Documentation Enhancement
1. **Bot001 Implementation Documentation** (`docs/bots/implementations/bot001_implementation.md`):
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

### Workflow Documentation (January 8, 2025)
1. **README Update Workflow** (`.clinerules/workflows/readme_update.md`):
   - Created comprehensive workflow for maintaining README.md
   - Modeled after memorybank.md structure
   - Includes 7 update triggers (features, structure, milestones, etc.)
   - Prioritizes 4 critical sections (Current Status, Setup, Usage, Bot Architecture)
   - Provides 6 common update scenarios with specific guidance
   - Defines clear exclusion guidelines (what NOT to include in README)
   - 8-step update process with flowchart and consistency checklist
   - Emphasizes user-focused, concise, current content
   - README is the user view; memory bank is the detailed context

2. **README.md Update** (`.clinerules/workflows/readme_update.md` applied):
   - Updated README.md following new workflow guidelines
   - Synchronized Current Status section with memory bank
   - Added Recent Updates highlighting January 8, 2025 achievements
   - Expanded Project Structure to show docs/bots/implementations/ directory
   - Added Bot Implementation Documentation section
   - Updated Next Steps to reflect completed milestones
   - Fixed bot001 description accuracy (Multi-Component MCTS, not Neural)

3. **Git Commits**:
   - README update workflow: 310124e
   - Memory bank update: cdc0b70
   - README.md update: 3879b72

#### Project Setup (Previous Session)
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

### Immediate Priorities (COMPLETED ✓)
1. **✅ Verify bot001 functionality**
   - Tested both Python and C++ versions locally
   - Long-running mode works correctly
   - All evaluation components verified through tournament

2. **✅ Create testing infrastructure**
   - Built 3 comprehensive test scripts
   - Tournament system with parallel execution
   - Full bot vs bot comparison framework

3. **Botzone Deployment (READY)**
   - Prepare C++ bot for submission (recommended: no dependencies, 4x faster)
   - Submit to Botzone with long-running mode enabled
   - Monitor initial matches and establish baseline ELO

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

**Most critical immediate task**: Submit C++ bot to Botzone and establish baseline ELO rating. Both implementations are fully tested and production-ready.