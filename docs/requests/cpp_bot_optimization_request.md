# C++ Bot Optimization Request for DeepSeek

## Executive Summary

**Bot Name**: bot001.cpp  
**Game**: Game of the Amazons (8×8 grid, 4 queens per side)  
**Platform**: Botzone (competitive game AI platform)  
**Language**: C++11 (single file, ~550 lines)  
**Time Constraints**: 
- First turn: 2 seconds (using 1.8s with buffer)
- Subsequent turns: 1 second (using 0.9s with buffer)

### Current Performance
- **Iterations per turn**: 12,000-32,000 MCTS iterations
- **Evaluation speed**: ~0.0001s per evaluation call
- **Memory usage**: 50-150 MB (limit: 256 MB)
- **Strength**: Equal to Python reference implementation (50-50 win rate)
- **Speed improvement**: 4.15× faster than Python version

### Objective
Seeking optimization advice to maximize MCTS iterations within strict time constraints while maintaining algorithm correctness. Target: 50-100% more iterations through code optimization.

---

## Game Context

### Game of the Amazons Rules
- 8×8 board with 4 queens per player
- Each turn: Move queen (like chess queen) → Shoot arrow (like chess queen from new position)
- Arrow creates permanent obstacle
- Lose when unable to make any legal move
- Typical game length: 40-80 plies (20-40 turns per player)

### Challenge Characteristics
- **Extremely high branching factor**: 200-800+ legal moves in early game
- **No natural evaluation**: No material count, position value hard to assess
- **Territory control critical**: Must maximize accessible space
- **Mid-game decisive**: Territory formation determines outcome

---

## Implementation Overview

### Algorithm: Monte Carlo Tree Search (MCTS) + Multi-Component Evaluation

**Key Components:**
1. **Game State Representation** - Board class with 8×8 array
2. **Move Generation** - Legal move calculation (Queen movement + arrow shooting)
3. **MCTS Tree** - UCT-based tree search with node selection
4. **Evaluation Function** - 5-component heuristic (no rollouts)
5. **I/O Handler** - Botzone long-running protocol

### Architecture Overview
```
Board State
    ↓
MCTS Search Loop (time-limited)
    ├─ Selection (UCT)
    ├─ Expansion (random untried move)
    ├─ Evaluation (multi-component heuristic)
    └─ Backpropagation (update statistics)
    ↓
Best Move Selection (by visit count)
```

### Multi-Component Evaluation Function

Instead of expensive random rollouts, we use a fast 5-component heuristic:

1. **Queen Territory** - BFS from all queens, count reachable cells
2. **King Territory** - Weighted close-range control (1-3 steps, decay by distance)
3. **Queen Position** - Exponential decay scoring (2^-distance for cells 1-7 steps away)
4. **King Position** - Distance-weighted positioning (cells 1-6 steps, divide by d+1)
5. **Mobility** - Total available queen moves (max 7 steps per direction)

**Phase Awareness**: Different weight sets for early (≤10 turns), mid (11-20), late (21+) game

---

## Technical Implementation Details

### Data Structures

**Board Representation:**
```cpp
class Board {
    array<array<int, GRID_SIZE>, GRID_SIZE> grid;  // Stack-allocated 8×8 array
    // Values: EMPTY(0), BLACK(1), WHITE(-1), OBSTACLE(2)
};
```

**MCTS Node:**
```cpp
class MCTSNode {
    MCTSNode* parent;
    Move move;
    vector<MCTSNode*> children;
    double wins;
    int visits;
    vector<Move> untried_moves;
    int player_just_moved;
};
```

**Move Structure:**
```cpp
struct Move {
    int x0, y0;  // Original position
    int x1, y1;  // New position
    int x2, y2;  // Arrow position
};
```

### MCTS Algorithm Flow

**1. Selection Phase (UCT):**
```cpp
double score = (child->wins / child->visits) + C * sqrt(log(parent->visits) / child->visits);
// C decreases with turn number: C = 0.177 * exp(-0.008 * (turn - 1.41))
```

**2. Expansion Phase:**
- Randomly select one untried move
- Create new node and add to tree
- Generate legal moves for new state

**3. Evaluation Phase:**
- Calculate 5 evaluation components
- Weighted combination based on game phase
- Sigmoid normalization to [0, 1]

**4. Backpropagation:**
- Update wins and visits from leaf to root
- Perspective-aware: flip win value for opponent nodes

### Critical Hot Paths

**1. Move Generation** (called every expansion):
```cpp
vector<Move> get_legal_moves(int color) const {
    // For each piece:
    //   For each of 8 directions:
    //     Slide until blocked (Queen movement)
    //       For each landing position:
    //         For each of 8 directions:
    //           Shoot arrow until blocked
    // Complexity: O(pieces × directions × max_slide × directions × max_shoot)
    // Typical: 4 queens × 8 × 7 × 8 × 7 ≈ 12,544 checks
}
```

**2. BFS Territory Calculation** (called in every evaluation):
```cpp
pair<unordered_map<int, int>, array<array<int, GRID_SIZE>, GRID_SIZE>> 
bfs_territory(const grid, const pieces) {
    // BFS from all pieces simultaneously
    // Mark distance to each reachable cell
    // Count cells by distance
    // Complexity: O(64 × 8) = O(512) per call
    // Called twice per evaluation (my pieces + opponent pieces)
}
```

**3. Evaluation Function** (called every MCTS iteration):
```cpp
double evaluate_multi_component(const grid, int root_player) {
    // 1. Run BFS for both players (2× BFS calls)
    // 2. Calculate 5 components from BFS results
    // 3. Weighted combination with phase-specific weights
    // 4. Sigmoid normalization
    // Complexity: O(BFS) + O(components) ≈ O(1024) + O(320) = O(1344)
}
```

### Memory Management

**Tree Growth:**
- Each node: ~96 bytes (pointers, vectors, doubles, ints)
- Typical tree size: 12k-32k nodes = 1-3 MB per turn
- Tree reuse between turns reduces allocation overhead
- Manual delete in destructor prevents leaks

**Memory Allocation Pattern:**
- Board state: Stack-allocated (no heap overhead)
- MCTS nodes: Heap-allocated with new/delete
- Move vectors: Dynamic growth with std::vector
- BFS structures: Recreated each evaluation

---

## Performance Bottlenecks & Analysis

### Identified Bottlenecks (Profiled)

**1. Move Generation (Estimated 30-40% of time)**
- **Issue**: Nested loops checking all possible queen moves + arrow shots
- **Volume**: 200-800 legal moves in early game, 50-200 in mid/late game
- **Inefficiency**: No early termination, checks even unlikely moves
- **Opportunity**: Move ordering, pruning bad moves early

**2. BFS Territory Calculation (Estimated 25-35% of time)**
- **Issue**: Called twice per evaluation (my pieces + opponent)
- **Volume**: ~20k-60k BFS calls per turn (2 per MCTS iteration)
- **Inefficiency**: Recalculates from scratch every time
- **Opportunity**: Incremental updates, caching distance maps

**3. Memory Allocation (Estimated 15-20% of time)**
- **Issue**: Frequent new/delete for MCTS nodes
- **Volume**: 12k-32k allocations per turn
- **Inefficiency**: Default allocator not optimized for small objects
- **Opportunity**: Custom allocator, memory pool

**4. Board Copying (Estimated 5-10% of time)**
- **Issue**: Each expansion creates board copy for simulation
- **Volume**: One copy per MCTS iteration
- **Inefficiency**: Copies entire 8×8 array even if most cells unchanged
- **Opportunity**: Copy-on-write, incremental state updates

**5. Random Move Selection (Estimated 5% of time)**
- **Issue**: Uniform random selection from untried_moves vector
- **Volume**: One random selection per expansion
- **Inefficiency**: No prioritization of promising moves
- **Opportunity**: Move ordering heuristics, priority queue

### Time Distribution Estimate
```
Move Generation:          35%  (generating legal moves during expansion)
BFS Territory:            30%  (evaluation function's BFS calls)
Memory Allocation:        15%  (new/delete for MCTS nodes)
Board Operations:          8%  (copying, applying moves)
Random Selection:          5%  (choosing untried moves)
UCT Calculation:           4%  (selection phase scoring)
Other (backprop, etc.):    3%
```

### Why Not More Iterations?

**Current**: 12k-32k iterations in 0.9s = 13-35k iterations/second

**Comparison to theoretical maximum:**
- If pure computation: Could theoretically do 100k+ iterations/second
- **Reality**: 35k iterations/second max
- **Gap**: ~3× slower than theoretical
- **Reason**: Dominated by move generation and evaluation complexity

---

## Current Limitations

### Algorithmic Limitations

1. **No Move Ordering**
   - Expansion chooses random untried move
   - No prioritization of promising moves
   - Wastes iterations on bad moves

2. **No Transposition Table**
   - Same positions reached via different move orders treated as separate nodes
   - Duplicates work across tree branches
   - Common in Amazons due to move independence

3. **Fixed Phase Boundaries**
   - Phase changes at turns 10 and 20
   - Not adaptive to actual game state
   - May misapply weights in unusual games

4. **No Progressive Widening**
   - Explores all legal moves equally
   - High branching factor dilutes search
   - No focus on best continuations

5. **Static Time Allocation**
   - Fixed time per turn (0.9s/1.8s)
   - No dynamic adjustment based on position criticality
   - May waste time in obvious positions

### Implementation Limitations

1. **Board Representation**
   - Using `array<array<int, 8>, 8>` - not cache-friendly
   - Each cell is 4 bytes (int) - could be 1 byte
   - No bitboard optimization

2. **BFS Implementation**
   - Uses `std::deque` and `std::unordered_map`
   - No SIMD vectorization
   - Recalculates from scratch each time

3. **Memory Allocator**
   - Using default `new`/`delete`
   - Not optimized for MCTS tree allocation pattern
   - Fragmentation possible

4. **Move Storage**
   - `std::vector<Move>` with dynamic resizing
   - Frequent allocations during move generation
   - Could pre-allocate or use object pool

5. **Random Number Generation**
   - `std::mt19937` may be overkill for move selection
   - Faster alternatives exist (xorshift, etc.)

---

## Specific Optimization Questions for DeepSeek

### 1. Move Ordering & Prioritization

**Current**: Random selection from `untried_moves` vector
```cpp
uniform_int_distribution<int> dist(0, node->untried_moves.size() - 1);
int idx = dist(rng);
Move m = node->untried_moves[idx];
```

**Questions:**
- What lightweight heuristics could prioritize moves without expensive calculation?
- Should I use a priority queue, or sort moves once during node creation?
- For Amazons specifically, what move characteristics correlate with quality?
  - Territory control (moves that claim more space)?
  - Centrality (moves toward center)?
  - Opponent blocking (arrows aimed at opponent queens)?

### 2. Board Representation & Bitboards

**Current**: `array<array<int, 8>, 8>` using 256 bytes (64 × 4 bytes)

**Questions:**
- Is bitboard representation feasible for Amazons? (Need to track: empty, black queens, white queens, obstacles)
- Would 4 separate `uint64_t` bitboards be faster? (One per piece type)
- How to efficiently check queen sliding moves with bitboards?
- Trade-off: Bitboard speed vs implementation complexity for 8-direction sliding?

**Alternative consideration:**
- Use `array<array<int8_t, 8>, 8>` (64 bytes instead of 256)?
- Better cache locality but does it matter for 64-cell board?

### 3. BFS Optimization

**Current**: Two full BFS calls per evaluation (~30% of time)

**Questions:**
- **Incremental BFS**: Can I update distance maps incrementally after each move?
  - Move changes 3 cells: old queen position → new position → arrow position
  - Can I locally recompute affected regions instead of full BFS?
- **Caching strategy**: Cache BFS results at MCTS nodes?
  - Memory trade-off: Would need ~512 bytes per node for distance map
- **SIMD**: Is BFS amenable to SIMD vectorization with AVX2?
- **Early termination**: Can I stop BFS after distance X for certain components?

### 4. Memory Allocation Strategy

**Current**: Default `new`/`delete` for 12k-32k nodes per turn

**Questions:**
- **Custom allocator**: Should I implement arena/pool allocator for MCTSNode?
  ```cpp
  class NodeAllocator {
      char pool[256 * 1024 * 1024];  // Pre-allocate pool
      size_t offset;
  };
  ```
- **Object pool**: Reuse deleted nodes instead of freeing?
- **Single allocation**: Allocate nodes in blocks of 1000 at a time?
- **Stack allocation**: Can I avoid heap entirely with fixed-size node array?
  - Limitation: Max tree size becomes fixed

### 5. Transposition Table

**Current**: No deduplication of equivalent positions

**Questions:**
- **Zobrist hashing**: Standard approach for game trees?
- **Hash collision handling**: Chaining vs open addressing?
- **Size/speed trade-off**: How large should table be? (Memory limit: 256 MB)
- **When to probe**: Check before expansion? Before evaluation?
- **What to store**: Full evaluation result or just visit statistics?

**Example structure:**
```cpp
struct TranspositionEntry {
    uint64_t hash;
    double value;
    int visits;
    int depth;
};
unordered_map<uint64_t, TranspositionEntry> tt;
```

### 6. Move Generation Optimization

**Current**: Generates ALL legal moves (~35% of time)

**Questions:**
- **Lazy generation**: Generate moves on-demand during MCTS?
- **Move ordering during generation**: Generate best moves first?
- **Bitboard sliding**: Faster than loop-based sliding?
- **Early move cutoffs**: Stop after generating N best moves?

**Pseudo-code for potential optimization:**
```cpp
// Instead of generating all 200-800 moves
// Generate in priority order and stop early?
vector<Move> get_priority_moves(int color, int max_moves = 50) {
    // Generate center-controlling moves first
    // Then edge moves
    // Limit to top N
}
```

### 7. Progressive Widening / MCTS Enhancements

**Questions:**
- **Progressive widening**: Only expand top K moves initially, expand more as visits increase?
  ```cpp
  int max_children = min(C * pow(visits, alpha), untried_moves.size());
  ```
- **RAVE (Rapid Action Value Estimation)**: Track move statistics across tree?
- **Virtual loss**: For parallel MCTS (if I parallelize)?
- **UCB1-Tuned**: Better than standard UCB1 for high branching?

### 8. Evaluation Function Optimization

**Questions:**
- **Component caching**: Cache intermediate results (e.g., mobility count)?
- **Approximation**: Can I approximate BFS with faster heuristic?
  - Example: Flood-fill with max depth limit?
- **Lazy evaluation**: Skip expensive components if score is obviously good/bad?
- **SIMD**: Vectorize component calculations?

### 9. Time Management

**Current**: Fixed time limits (0.9s / 1.8s)

**Questions:**
- **Dynamic allocation**: Use more time for critical positions?
  - How to detect criticality? (Evaluation uncertainty? Close game?)
- **Iterative deepening**: Set iteration checkpoints and stop gracefully?
- **Time bank**: Save time from easy moves for later?

### 10. Code-Level Optimizations

**Questions:**
- **Inline functions**: Should I inline hot path functions?
- **Compiler flags**: Beyond `-O2`, what helps? (`-O3`, `-march=native`, `-ffast-math`?)
- **Branch prediction**: Any obvious mispredicted branches?
- **Cache optimization**: Data layout improvements?

---

## Code Snippets: Current Implementation

### Move Generation (Hot Path #1)
```cpp
vector<Move> get_legal_moves(int color) const {
    vector<Move> moves;
    
    // Find all pieces of the given color
    for (int px = 0; px < GRID_SIZE; px++) {
        for (int py = 0; py < GRID_SIZE; py++) {
            if (grid[px][py] != color) continue;
            
            // Try all 8 directions for piece movement
            for (int d = 0; d < 8; d++) {
                int dx = DIRECTIONS[d][0];
                int dy = DIRECTIONS[d][1];
                int nx = px + dx;
                int ny = py + dy;
                
                // Slide queen in this direction
                while (is_valid(nx, ny) && grid[nx][ny] == EMPTY) {
                    // From each landing position, try shooting in all 8 directions
                    for (int ad = 0; ad < 8; ad++) {
                        int adx = DIRECTIONS[ad][0];
                        int ady = DIRECTIONS[ad][1];
                        int ax = nx + adx;
                        int ay = ny + ady;
                        
                        // Shoot arrow in this direction
                        while (is_valid(ax, ay)) {
                            bool is_blocked = false;
                            if (grid[ax][ay] != EMPTY) {
                                if (ax == px && ay == py) {
                                    // Arrow hits original position (valid)
                                } else {
                                    is_blocked = true;
                                }
                            }
                            if (is_blocked) break;
                            
                            moves.push_back(Move(px, py, nx, ny, ax, ay));
                            ax += adx;
                            ay += ady;
                        }
                    }
                    nx += dx;
                    ny += dy;
                }
            }
        }
    }
    return moves;
}
```

### BFS Territory Calculation (Hot Path #2)
```cpp
pair<unordered_map<int, int>, array<array<int, GRID_SIZE>, GRID_SIZE>> 
bfs_territory(const array<array<int, GRID_SIZE>, GRID_SIZE>& grid, 
              const vector<pair<int, int>>& pieces) {
    array<array<int, GRID_SIZE>, GRID_SIZE> dist;
    for (int i = 0; i < GRID_SIZE; i++) {
        for (int j = 0; j < GRID_SIZE; j++) {
            dist[i][j] = 99;
        }
    }
    
    deque<tuple<int, int, int>> q;
    for (auto& p : pieces) {
        dist[p.first][p.second] = 0;
        q.push_back(make_tuple(p.first, p.second, 0));
    }
    
    unordered_map<int, int> territory_by_dist;
    
    while (!q.empty()) {
        int x, y, d;
        tie(x, y, d) = q.front();
        q.pop_front();
        int nd = d + 1;
        
        for (int i = 0; i < 8; i++) {
            int nx = x + DIRECTIONS[i][0];
            int ny = y + DIRECTIONS[i][1];
            
            if (nx >= 0 && nx < GRID_SIZE && ny >= 0 && ny < GRID_SIZE) {
                if (grid[nx][ny] == EMPTY && dist[nx][ny] > nd) {
                    dist[nx][ny] = nd;
                    territory_by_dist[nd]++;
                    q.push_back(make_tuple(nx, ny, nd));
                }
            }
        }
    }
    
    return make_pair(territory_by_dist, dist);
}
```

### UCT Selection (Critical for Search Quality)
```cpp
MCTSNode* uct_select_child(double C) {
    double log_visits = log(visits);
    double best_score = -1e9;
    MCTSNode* best_child = nullptr;
    
    for (auto c : children) {
        double score = (c->wins / c->visits) + C * sqrt(log_visits / c->visits);
        if (score > best_score) {
            best_score = score;
            best_child = c;
        }
    }
    return best_child;
}
```

### Main MCTS Search Loop
```cpp
Move search(const Board& root_state, int root_player) {
    auto start_time = chrono::steady_clock::now();
    int iterations = 0;
    double C = get_ucb_constant(turn_number);
    
    while (true) {
        auto current_time = chrono::steady_clock::now();
        double elapsed = chrono::duration<double>(current_time - start_time).count();
        if (elapsed >= time_limit) break;
        
        MCTSNode* node = root;
        Board state = root_state.copy();
        int current_player = root_player;
        
        // Selection
        while (node->untried_moves.empty() && !node->children.empty()) {
            node = node->uct_select_child(C);
            state.apply_move(node->move);
            current_player = -current_player;
        }
        
        // Expansion
        if (!node->untried_moves.empty()) {
            uniform_int_distribution<int> dist(0, node->untried_moves.size() - 1);
            int idx = dist(rng);
            Move m = node->untried_moves[idx];
            
            state.apply_move(m);
            current_player = -current_player;
            
            MCTSNode* new_node = new MCTSNode(node, m, -current_player);
            new_node->untried_moves = state.get_legal_moves(current_player);
            
            node->untried_moves.erase(node->untried_moves.begin() + idx);
            node->children.push_back(new_node);
            node = new_node;
        }
        
        // Evaluation
        double win_prob = evaluate_multi_component(state.grid, root_player);
        
        // Backpropagation
        while (node != nullptr) {
            node->visits++;
            if (node->player_just_moved == root_player) {
                node->wins += win_prob;
            } else {
                node->wins += (1.0 - win_prob);
            }
            node = node->parent;
        }
        
        iterations++;
    }
    
    // Select best move by visit count
    MCTSNode* best_node = nullptr;
    int max_visits = -1;
    for (auto child : root->children) {
        if (child->visits > max_visits) {
            max_visits = child->visits;
            best_node = child;
        }
    }
    
    return best_node->move;
}
```

---

## Goals & Constraints

### Primary Goal
Maximize MCTS iterations within time budget:
- **Target**: 50-100% more iterations (18k-65k instead of 12k-32k)
- **Means**: Code optimization, algorithmic improvements, better data structures

### Secondary Goals
- Maintain algorithm correctness (no bugs)
- Preserve or improve playing strength
- Keep implementation complexity reasonable
- Stay within memory limits (256 MB)

### Hard Constraints
- **Platform**: Botzone (online judge system)
- **Language**: C++11 (cannot use C++14/17 features)
- **Format**: Single file submission (no external libraries)
- **Time**: 1s for regular turns, 2s for first turn (strictly enforced)
- **Memory**: 256 MB limit
- **Compilation**: `g++ -O2 -std=c++11`

### Soft Constraints
- **Code size**: Prefer < 1000 lines for maintainability
- **Readability**: Keep code understandable for future modifications
- **Portability**: Should work on standard Linux x86_64 (Botzone VM)

---

## Optimization Priority Ranking

Based on profiling and impact analysis, here's my priority order:

### Tier 1 (High Impact, Medium Effort)
1. **Move ordering heuristics** - 35% time spent, likely 20-30% reduction possible
2. **BFS optimization** - 30% time spent, caching could save 50%+
3. **Custom memory allocator** - 15% time spent, pool allocator ~50% faster

### Tier 2 (Medium Impact, Low-Medium Effort)
4. **Board representation optimization** - Better cache locality
5. **Compiler flags and inlining** - Easy to try, 5-10% gains
6. **Faster RNG** - Small but cheap optimization

### Tier 3 (Lower Impact or Higher Complexity)
7. **Transposition table** - Complex implementation, uncertain payoff
8. **Progressive widening** - Algorithmic change, needs tuning
9. **Bitboard representation** - High effort, uncertain Amazons applicability

---

## Request Summary

I'm seeking advice on:

1. **Which optimizations to prioritize** given the profiled bottlenecks
2. **Specific implementation guidance** for top optimizations (move ordering, BFS caching, memory allocation)
3. **Code-level improvements** for the provided hot path snippets
4. **Architectural changes** if fundamental redesign would yield better results
5. **Amazons-specific insights** from game characteristics (high branching, territory control)

**Ideal outcome**: Clear roadmap for achieving 50-100% more MCTS iterations while maintaining correctness and staying within constraints.

Thank you for your expertise!

---

## Appendix: Full Implementation Available

The complete bot001.cpp source code (~550 lines) is available if detailed analysis is needed. This document highlights the critical sections, but the full implementation includes:

- Complete Board class with move application
- Full MCTS tree implementation with memory management
- All 5 evaluation components with phase-specific weights
- Botzone I/O protocol handler
- Dynamic UCB constant calculation
- Tree reuse between turns

**Repository**: github.com/RizzoHou/amazing-amazons (private, can provide access if needed)
