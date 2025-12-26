# Implementation Plan

Create a series of new C++ bots (bot004-bot008) based on bot003 with incremental improvements, each implementing one specific enhancement. Run 10 competitions between each new bot and bot003, analyze results, and update documentation.

## Overview

This implementation plan outlines the creation of five new C++ bots (bot004 through bot008) derived from bot003.cpp, each implementing a distinct algorithmic improvement identified in the bot003 report. The goal is to test incremental enhancements to the Multi-Component MCTS algorithm while maintaining stability and Botzone protocol compliance. Each bot will implement one specific improvement feature, allowing isolated testing of its effectiveness. After implementation, each new bot will compete in 10 games against bot003 to evaluate performance improvements. Results will be analyzed and documented in docs/analysis/, and memory bank documentation will be updated to reflect the new bot versions and findings.

## Types

Single sentence describing the type system changes.

The bot implementations will maintain the existing type system from bot003 with minor extensions for new features. Key types include:
- `Move` struct: 6 integer coordinates (x0, y0, x1, y1, x2, y2) for piece movement and arrow placement
- `Board` class: 8x8 array representation with EMPTY(0), BLACK(1), WHITE(-1), OBSTACLE(2) encoding
- `MCTSNode` class: Tree node with parent pointer, move, children vector, win statistics (double wins, int visits), untried moves vector, and player tracking
- `MCTS` class: Main AI controller with time management, search algorithm, and evaluation functions
- New types for specific bots:
  - `TranspositionTable` (bot005): Hash map with Zobrist keys for position caching
  - `MoveOrderingHeuristic` (bot004): Comparator for prioritizing central and aggressive moves
  - `TimeManager` (bot008): Adaptive time allocation based on position complexity
  - `BitBoard` (bot007): uint64_t representation for efficient move generation (alternative to array<array<int,8>,8>)

## Files

Single sentence describing file modifications.

Detailed breakdown:
- New files to be created:
  - `bots/bot004.cpp`: Implements move ordering heuristics - sorts untried moves by center proximity and mobility impact before expansion
  - `bots/bot005.cpp`: Implements transposition table - Zobrist hashing with 64-bit keys, cache for evaluation results
  - `bots/bot006.cpp`: Implements progressive widening - limits expansion to top 5 moves initially, gradually expands based on visits
  - `bots/bot007.cpp`: Implements bitboard representation - 3x uint64_t for pieces/obstacles, bitwise move generation
  - `bots/bot008.cpp`: Implements adaptive time management - allocates more time to critical positions, implements time banking
  - `scripts/run_competitions.py`: New script to automate 10-game competitions between each new bot and bot003
  - `docs/analysis/bot004_vs_bot003_results.md`: Results analysis for bot004 vs bot003 (10 games)
  - `docs/analysis/bot005_vs_bot003_results.md`: Results analysis for bot005 vs bot003 (10 games)
  - `docs/analysis/bot006_vs_bot003_results.md`: Results analysis for bot006 vs bot003 (10 games)
  - `docs/analysis/bot007_vs_bot003_results.md`: Results analysis for bot007 vs bot003 (10 games)
  - `docs/analysis/bot008_vs_bot003_results.md`: Results analysis for bot008 vs bot003 (10 games)
  - `docs/analysis/summary_report.md`: Comparative analysis of all improvements with win rates, performance metrics, and recommendations

- Existing files to be modified:
  - `scripts/tournament/cli.py`: Extend to support batch competition mode for automated testing
  - `memorybank/activeContext.md`: Update with new bot implementations and competition results
  - `memorybank/progress.md`: Update project status with new bot versions and findings
  - `memorybank/techContext.md`: Document new algorithmic features and implementation details
  - `README.md`: Add section about new bot versions and their features

- Files to be deleted or moved: None

- Configuration file updates: None required

## Functions

Single sentence describing function modifications.

Detailed breakdown:
- New functions in bot004.cpp:
  - `order_moves(vector<Move>& moves)`: Sorts moves by center proximity (distance from board center) and mobility impact
  - `calculate_move_priority(const Move& m)`: Returns heuristic score for move ordering

- New functions in bot005.cpp:
  - `zobrist_hash(const Board& board)`: Computes 64-bit hash using precomputed random numbers for each board state
  - `TranspositionTable::lookup(uint64_t hash)`: Returns cached evaluation if exists
  - `TranspositionTable::store(uint64_t hash, double eval)`: Caches evaluation result

- New functions in bot006.cpp:
  - `progressive_widen(MCTSNode* node, int visits)`: Returns subset of untried moves based on node visit count
  - `get_top_moves(const vector<Move>& moves, int count)`: Selects top N moves by simple heuristic

- New functions in bot007.cpp:
  - `BitBoard::from_array(const array<array<int,8>,8>& grid)`: Converts array representation to bitboard
  - `BitBoard::generate_moves(int color)`: Bitwise move generation using shift operations
  - `BitBoard::to_array()`: Converts back to array representation for compatibility

- New functions in bot008.cpp:
  - `TimeManager::allocate_time(int turn, double remaining, int complexity)`: Dynamic time allocation
  - `calculate_position_complexity(const Board& board)`: Estimates branching factor and game phase
  - `TimeManager::update_bank(double used, double allocated)`: Implements time banking

- Modified functions in all bots:
  - `MCTS::search()`: Modified to incorporate each bot's specific enhancement
  - `MCTSNode` constructor: May include additional data structures for specific features

- Removed functions: None

## Classes

Single sentence describing class modifications.

Detailed breakdown:
- New classes:
  - `TranspositionTable` (bot005): Manages hash table for position caching with LRU eviction policy
  - `MoveOrderingHeuristic` (bot004): Encapsulates move prioritization logic with configurable weights
  - `TimeManager` (bot008): Handles adaptive time allocation with complexity estimation and banking
  - `BitBoard` (bot007): Alternative board representation with efficient bitwise operations

- Modified classes:
  - `MCTS` (all bots): Extended with bot-specific enhancement hooks
  - `MCTSNode` (bot005, bot006): May include additional fields for transposition keys or progressive widening state

- Removed classes: None

## Dependencies

Single sentence describing dependency modifications.

Details of new packages, version changes, and integration requirements:
- No external dependencies required - all bots use pure C++11 standard library
- Compilation requirements: g++ with -std=c++11 flag, -O3 optimization recommended
- Tournament system: Python 3 with existing tournament scripts (no new dependencies)
- Memory requirements: Each bot should stay within 256MB Botzone limit
- Time requirements: Must respect Botzone time limits (1s per turn, 2s first turn)

## Testing

Single sentence describing testing approach.

Test file requirements, existing test modifications, and validation strategies:
- Unit tests: Each bot will be compiled and tested for basic functionality using existing test framework
- Protocol compliance: Verify Botzone long-running mode protocol implementation matches bot003
- Self-play tests: Each new bot will play 3 self-play games to ensure no crashes or illegal moves
- Competition tests: 10 games against bot003 for each new bot using tournament system
- Performance metrics: Track iterations per second, memory usage, win rates
- Validation: Compare results against bot003 baseline, statistical significance analysis
- Edge cases: Test endgame positions, no-legal-moves scenarios, time limit handling

## Implementation Order

Single sentence describing the implementation sequence.

Numbered steps showing the logical order of changes to minimize conflicts and ensure successful integration:

1. **Create bot004 (Move Ordering Heuristics)**
   - Copy bot003.cpp to bot004.cpp
   - Implement `order_moves()` function with center proximity heuristic
   - Integrate into MCTS expansion phase
   - Test compilation and basic functionality
   - Run 3 self-play games for stability

2. **Create bot005 (Transposition Table)**
   - Copy bot003.cpp to bot005.cpp
   - Implement Zobrist hashing with precomputed random numbers
   - Create `TranspositionTable` class with LRU cache
   - Integrate into evaluation caching
   - Test memory usage and hash collisions

3. **Create bot006 (Progressive Widening)**
   - Copy bot003.cpp to bot006.cpp
   - Implement progressive widening logic in expansion phase
   - Add visit-based move selection threshold
   - Test with various widening parameters

4. **Create bot007 (Bitboard Representation)**
   - Copy bot003.cpp to bot007.cpp
   - Implement `BitBoard` class with conversion methods
   - Replace array-based move generation with bitwise operations
   - Ensure compatibility with existing evaluation functions
   - Performance benchmark against array representation

5. **Create bot008 (Adaptive Time Management)**
   - Copy bot003.cpp to bot008.cpp
   - Implement `TimeManager` class with complexity estimation
   - Add time banking and dynamic allocation
   - Test time usage across different positions

6. **Create competition automation script**
   - Develop `scripts/run_competitions.py` to automate 10-game matches
   - Implement result logging and statistics collection
   - Add error handling and progress reporting

7. **Run competitions**
   - For each bot (004-008), run 10 games against bot003
   - Record win/loss/draw results, move counts, errors
   - Capture performance metrics (iterations, time usage)

8. **Analyze results**
   - Create individual result files in `docs/analysis/`
   - Generate summary report with comparative analysis
   - Calculate win rates, statistical significance
   - Identify most effective improvements

9. **Update documentation**
   - Update memory bank files (activeContext.md, progress.md, techContext.md)
   - Update README.md with new bot information
   - Document findings and recommendations

10. **Final validation**
    - Verify all bots compile without errors
    - Ensure tournament system works with all new bots
    - Confirm memory bank is up-to-date
    - Prepare final implementation report