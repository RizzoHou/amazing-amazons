# System Patterns

## Architecture Overview

The project follows a modular architecture with clear separation of concerns:

```
amazing-amazons/
├── core/              # Shared game logic and utilities
│   ├── game.py       # Board representation and move generation
│   └── ai.py         # Generic MCTS implementation
├── bots/             # Bot implementations
│   ├── bot001.py     # Python MCTS bot (Multi-Component)
│   ├── bot001.cpp    # C++ port (4x faster, production-ready)
│   ├── bot001_cpp    # Compiled C++ binary
│   ├── bot002.cpp    # Optimized C++ bot (bitboards, faster)
│   └── bot002_cpp    # Compiled optimized binary
├── scripts/          # Testing and utility scripts
│   ├── test_bot_simple.py      # Quick functionality tests
│   ├── botzone_simulator.py   # I/O protocol simulator
│   └── tournament.py           # Bot comparison framework
├── docs/             # Implementation documentation
│   └── bot_implementation/
│       ├── bot001_implementation.md      # Python bot docs
│       └── bot001_cpp_implementation.md  # C++ bot docs
├── memorybank/       # Project documentation
├── wiki/             # Botzone platform documentation
├── logs/             # Tournament logs and match output
└── results/          # Tournament results (JSON)
```

## Key Technical Decisions

### 1. Long-Running Mode Architecture
**Decision**: Implement bots using Botzone's long-running mode
**Rationale**: 
- Eliminates cold-start overhead
- Preserves MCTS tree between turns for better search efficiency
- Critical for Python bots which have higher startup costs

**Implementation**:
- First turn: Complete I/O cycle, output `>>>BOTZONE_REQUEST_KEEP_RUNNING<<<`
- Subsequent turns: Process runs continuously, reads single request line per turn
- State maintained: Board object, MCTS root node with tree

### 2. Board Representation
**Decision**: NumPy array-based board with integer encoding
**Rationale**: Fast array operations, memory efficient, easy to copy

**Encoding**:
```python
EMPTY = 0
BLACK = 1
WHITE = -1
OBSTACLE = 2
```

**Board Class** (`core/game.py`):
- 8x8 NumPy array
- Initial piece positions hardcoded
- Move generation via direction vectors
- Efficient `copy()` for search tree nodes

### 3. Move Representation
**Decision**: 6-tuple format `(x0, y0, x1, y1, x2, y2)`
- `(x0, y0)`: Starting position of amazon
- `(x1, y1)`: Ending position of amazon
- `(x2, y2)`: Arrow obstacle position

**Rationale**: Matches Botzone I/O format exactly, no translation needed

### 4. AI Strategy: Multi-Component MCTS
**Decision**: MCTS with sophisticated multi-component evaluation function

**Components**:
1. **Multi-Component Evaluation** (`MCTS` class in bot001.py):
   - **Queen Territory**: BFS-based territory control
   - **King Territory**: Weighted close-range control
   - **Queen Position**: Exponential decay scoring (2^-d)
   - **King Position**: Distance-weighted positioning
   - **Mobility**: Available moves count
   - **Phase Weights**: Dynamic weights for early/mid/late game
   - **Sigmoid Normalization**: Score normalized to [0, 1] probability

2. **MCTS Search**:
   - **Selection**: UCT with dynamic exploration constant (changes by turn)
   - **Expansion**: Add one child per iteration when untried moves exist
   - **Evaluation**: Multi-component heuristic (no random rollout)
   - **Backpropagation**: Update node statistics up the tree

**Key Insight**: Multi-component evaluation inspired by strong opponent bots, balancing territory, positioning, and mobility

## Design Patterns

### 1. Tree Search with State Copying
```python
# Selection phase
node = self.root
state = root_state.copy()  # Copy state for exploration

while node has fully explored children:
    node = node.uct_select_child()
    state.apply_move(node.move)  # Modify state along path
```

**Pattern**: Each MCTS iteration maintains its own state copy to avoid interference

### 2. Tree Reuse Between Turns
```python
def advance_root(self, move):
    """Shift MCTS tree root to reflect opponent's move"""
    for child in self.root.children:
        if child.move == move:
            self.root = child
            self.root.parent = None
            return
    self.root = None  # Tree miss, start fresh
```

**Pattern**: Preserves search tree when opponent makes expected move

### 3. Time-Bounded Iterative Deepening
```python
start_time = time.time()
while time.time() - start_time < self.time_limit:
    # Run one MCTS iteration
    iterations += 1
```

**Pattern**: Anytime algorithm - can return best move found so far when time expires

## Component Relationships

### Bot001 Architecture Flow
```
Input (stdin) → Parse Move History → Reconstruct Board State
                                            ↓
              Multi-Component Eval ← MCTS Search → Legal Move Generator
                    ↓                               ↑
            (Territory, Position,            Board.get_legal_moves()
             Mobility Analysis)
                    ↓
            MCTS Backpropagation
                    ↓
         Select Best Move → Output (stdout)
```

### Module Dependencies

**Python Version (bot001.py)**:
- Fully self-contained (includes Board class)
- Does NOT import from `core.game` - has its own implementation
- No external dependencies beyond NumPy and standard library

**C++ Version (bot001.cpp)**:
- Completely standalone, single-file implementation
- No external dependencies (uses only C++ standard library)
- Compilation: `g++ -O2 -std=c++11 -o bots/bot001_cpp bots/bot001.cpp`

**Testing Infrastructure**:
- `scripts/test_bot_simple.py`: Tests both Python and C++ bots
- `scripts/tournament.py`: Runs parallel matches, saves results to JSON
- No dependencies between test scripts and bot implementations

`core/ai.py` and `core/game.py` remain standalone (not used by bot001 implementations)

## Critical Implementation Paths

### 1. Move Generation Algorithm
**Location**: `core/game.py::Board.get_legal_moves()`

**Critical Logic**:
```python
for each piece of my color:
    for each direction (8 total):
        for each distance (until blocked):
            candidate_position = piece + direction * distance
            
            for each arrow_direction (8 total):
                for each arrow_distance (until blocked):
                    arrow_position = candidate_position + arrow_direction * arrow_distance
                    
                    # CRITICAL: Old piece position becomes empty, valid arrow target
                    if arrow_position == original_piece_position:
                        valid_move
                    elif arrow_position occupied:
                        break
                    else:
                        yield move
```

**Complexity**: O(64 × 8 × 8 × 8 × 8) = O(262,144) worst case, but early termination reduces this significantly

### 2. Long-Running I/O Protocol
**Location**: `bot001.py::main()`

**First Turn**:
1. Read `turn_id` (single integer)
2. Read `2*turn_id - 1` lines (move history)
3. Parse and apply all moves to board
4. Run MCTS with extended time limit
5. Output move + keep-running signal

**Subsequent Turns**:
1. Read lines until 6-integer move found (skip turn_id lines)
2. Apply opponent move
3. Run MCTS with standard time limit
4. Output move + keep-running signal
5. Flush stdout
6. Continue loop (don't exit)

### 3. MCTS Tree Node Structure
**Location**: `bot001.py::MCTSNode`

**Node State**:
- `parent`: Reference to parent node
- `move`: Move that led to this node
- `children`: List of child nodes
- `wins`: Accumulated value (continuous, not just win count)
- `visits`: Number of times node visited
- `untried_moves`: Moves not yet expanded
- `player_just_moved`: Who made the move to reach this node

**Dynamic UCT Selection**:
```python
# UCB constant changes with turn number
C = 0.177 * exp(-0.008 * (turn - 1.41))
score = (wins / visits) + C * sqrt(log(parent.visits) / visits)
```

**Key Feature**: Exploration constant decreases as game progresses

## Performance Considerations

1. **NumPy Operations**: Board operations use NumPy for speed
2. **No Deep Copying Unless Needed**: MCTS creates shallow copies efficiently
3. **Move List Pre-allocation**: Moves stored in Python lists (acceptable overhead)
4. **Time Management**: Reserve small buffer (0.2s) to ensure completion before timeout

## Error Handling

- **No valid moves**: Output `-1 -1 -1 -1 -1 -1` and exit
- **Unexpected input**: Bot may hang or crash (needs improvement)
- **Minimal error handling**: Bot001 has basic exception catching but could be more robust

## Testing Strategy

### Implemented Testing Infrastructure (December 10, 2025)

**1. Functionality Tests** (`scripts/test_bot_simple.py`):
- Quick verification of both Python and C++ bots
- Tests I/O protocol compliance
- Validates long-running mode
- Verifies move format correctness

**2. Protocol Simulation** (`scripts/botzone_simulator.py`):
- Simulates Botzone long-running protocol
- Tests multiple turn sequences
- Useful for debugging I/O issues

**3. Tournament System** (`scripts/tournament.py`):
- Runs complete games between two bots
- Supports parallel execution (default: 10 concurrent games)
- Tracks statistics: wins, times, game lengths
- Saves detailed results to JSON
- Command-line interface with customizable parameters

**Tournament Results**:
- 50 games Python vs C++: 25-25 split (equal strength confirmed)
- Performance: C++ 4.15x faster (0.925s vs 3.843s per move)
- Average game length: 27.8 turns
- Zero errors or crashes

### Testing Workflow

1. **Unit Testing**: `python3 scripts/test_bot_simple.py`
2. **Tournament Testing**: `python3 scripts/tournament.py --games N --parallel P`
3. **Results Analysis**: Review JSON files in `results/` directory
4. **Log Review**: Check `logs/` for detailed game sequences

## Performance Comparison: Python vs C++

### Implementation Characteristics

| Aspect | Python (bot001.py) | C++ (bot001.cpp) |
|--------|-------------------|------------------|
| **Language** | Python 3 | C++11 |
| **Lines of Code** | ~350 | ~550 |
| **Dependencies** | NumPy | None |
| **Compilation** | Interpreted | `g++ -O2 -std=c++11` |
| **Board Repr** | NumPy array | `std::array<std::array<int, 8>, 8>` |
| **Move List** | Python list | `std::vector<Move>` |
| **BFS Queue** | collections.deque | `std::deque` |
| **Territory Map** | defaultdict | `std::unordered_map` |

### Performance Metrics

| Metric | Python | C++ | Improvement |
|--------|--------|-----|-------------|
| **Avg Time/Move** | 3.843s | 0.925s | 4.15x |
| **Time Limits** | 5.8s / 3.8s | 1.8s / 0.9s | - |
| **Iterations** | 3k-8k | 12k-32k | ~4x |
| **Memory** | ~100 MB | ~80 MB | 1.25x |
| **Strength** | Baseline | Equal | 1.0x |

### C++ Optimizations

1. **Stack Allocation**: Arrays on stack instead of heap
2. **Pass by Reference**: Avoid unnecessary copying
3. **Precise Timing**: `std::chrono::steady_clock` for high precision
4. **Fast I/O**: `ios::sync_with_stdio(false)` for speed
5. **Manual Memory Management**: No GC overhead for tree nodes
