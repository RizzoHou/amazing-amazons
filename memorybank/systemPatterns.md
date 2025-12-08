# System Patterns

## Architecture Overview

The project follows a modular architecture with clear separation of concerns:

```
amazing-amazons/
├── core/              # Shared game logic and utilities
│   ├── game.py       # Board representation and move generation
│   └── ai.py         # Generic MCTS implementation
├── bots/             # Individual bot implementations
│   └── bot001.py     # Current best bot (Neural MCTS)
├── models/           # Neural network weights (referenced but not in repo)
├── memorybank/       # Project documentation
├── wiki/             # Botzone platform documentation
└── scripts/          # Testing and utility scripts
```

## Key Technical Decisions

### 1. Long-Running Mode Architecture
**Decision**: Implement bots using Botzone's long-running mode
**Rationale**: 
- Eliminates cold-start overhead for neural network initialization
- Preserves MCTS tree between turns for better search efficiency
- Critical for Python bots which have higher startup costs

**Implementation**:
- First turn: Complete I/O cycle, output `>>>BOTZONE_REQUEST_KEEP_RUNNING<<<`
- Subsequent turns: Process runs continuously, reads single request line per turn
- State maintained: Board object, MCTS root node with tree, neural network

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
- `bot001.py` is fully self-contained (includes Board class)
- Does NOT import from `core.game` - has its own implementation
- `core/ai.py` and `core/game.py` are standalone (not used by bot001)
- No external dependencies beyond NumPy and standard library

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
- **Neural network load failure**: Exit with error to stderr
- **Unexpected input**: Bot may hang or crash (needs improvement)

## Testing Strategy (Implied)

- `scripts/` directory exists for testing utilities
- `logs/` directory for match logs
- `reports/` and `results/` for performance analysis
- Testing against previous bot versions is expected workflow
