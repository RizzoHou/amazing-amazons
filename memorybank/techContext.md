# Technical Context

## Technologies Used

### Core Language & Runtime
- **Python 3**: Primary language for bot development
  - Version: Python 3.6+ (Botzone supports multiple versions)
  - Used for bot001.py and all current bots

### Libraries & Dependencies

#### NumPy
- **Purpose**: Fast array operations for board representation and evaluation computations
- **Usage**: 
  - Board state stored as NumPy arrays
  - BFS territory calculations with efficient array operations
  - Distance map computations for position scoring

#### Standard Library
- `sys`: I/O operations (stdin/stdout)
- `time`: Time tracking for MCTS iterations
- `math`: Mathematical operations (log, sqrt for UCT, exponential for sigmoid)
- `random`: Random selection during MCTS expansion
- `collections`: deque for BFS territory calculation

### Evaluation System
- **Custom Multi-Component Heuristic**: No machine learning dependency
- **Rationale**: 
  - Fast evaluation without neural network overhead
  - Inspired by strong opponent bots (specifically opponent03)
  - Dynamic phase-based weighting for different game stages
  - Combines multiple strategic factors (territory, position, mobility)

## Development Setup

### Project Structure
```
amazing-amazons/
├── core/                  # Shared modules
│   ├── __init__.py       # Makes core a package
│   ├── game.py           # Board logic
│   └── ai.py             # Generic MCTS (legacy)
├── bots/                 # Bot implementations
│   └── bot001.py         # Current best bot
├── docs/                 # Implementation documentation
│   └── bot_implementation/ # Bot implementation details
├── memorybank/           # Project documentation
├── wiki/                 # Botzone docs (PDF)
├── scripts/              # Testing utilities
├── logs/                 # Match logs
├── reports/              # Analysis reports
├── results/              # Performance metrics
└── .gitignore           # Git configuration
```

### Environment Requirements

**Local Development**:
- Python 3.6+
- NumPy library
- Text editor / IDE (VSCode)

**Botzone Platform**:
- Ubuntu 16.04 x86-64
- Single CPU core
- 256 MB memory (default)
- Python 3.6+ with NumPy, SciPy, TensorFlow (CPU), PyTorch available

### Running Bots Locally

**Testing Format**:
```bash
# Activate virtual environment if used
source venv/bin/activate

# Run bot with simulated input
echo "1
-1 -1 -1 -1 -1 -1" | python bots/bot001.py
```

**Interactive Testing**:
- Use scripts in `scripts/` directory
- Create test harnesses that simulate Botzone I/O
- Compare bot outputs against expected moves

## Technical Constraints

### Platform Constraints (Botzone)

**Time Limits**:
- Python long-running bots:
  - First turn: 12 seconds
  - Subsequent turns: 4 seconds
- C++ long-running bots (for reference):
  - First turn: 2 seconds
  - Subsequent turns: 1 second

**Memory Limits**:
- Default: 256 MB RAM
- Single CPU core (no multi-threading benefit)

**I/O Constraints**:
- Simplified interaction: Line-based stdin/stdout
- JSON interaction: Also supported but not used
- Long-running mode: Must flush stdout after each turn

### Performance Constraints

**Evaluation Function**:
- BFS-based territory calculation (optimized with NumPy)
- Must complete in < 0.001 seconds per evaluation
- Five components: queen/king territory, queen/king position, mobility

**MCTS Search**:
- Must maximize iterations within time budget
- Typical range: 1000-5000 iterations per turn (depends on position)
- Must handle tree growth without memory overflow

**Move Generation**:
- Typical early game: 200-800 legal moves
- Must generate moves efficiently (< 0.1 seconds)

## Language-Specific Patterns

### Python Optimizations

1. **NumPy Vectorization**:
```python
# Fast: NumPy boolean indexing
pieces = np.argwhere(self.grid == color)

# Slow: Python nested loops
for x in range(8):
    for y in range(8):
        if grid[x][y] == color:
            pieces.append((x, y))
```

2. **List Comprehension Over Loops**:
```python
# Faster
moves = [move for move in self.generate_moves()]

# Slower
moves = []
for move in self.generate_moves():
    moves.append(move)
```

3. **Pre-allocated Arrays**:
```python
# Pre-allocate for batch norm
x = np.zeros(192, dtype=np.float32)
```

### Import Pattern

**Bot Modules**:
```python
# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.game import Board, BLACK, WHITE, GRID_SIZE
```

**Rationale**: Bots in subdirectories need to import from `core/`

## Tool Usage Patterns

### Version Control (Git)

**Expected Workflow**:
1. Commit after major features/changes
2. Tag bot versions (e.g., `bot001`, `bot002`)
3. Keep neural network weights out of repo (too large)
4. Use `.gitignore` for logs, results, temporary files

### Testing & Evaluation

**Directories**:
- `scripts/`: Testing harnesses and utilities
- `logs/`: Match logs from Botzone or local tests
- `reports/`: Analysis of bot performance
- `results/`: Aggregate statistics

**Process**:
1. Local testing against previous versions
2. Submit to Botzone
3. Download match logs
4. Analyze performance
5. Identify weaknesses
6. Iterate

### Documentation

**Memory Bank System**:
- All project context in `memorybank/`
- Update after significant changes
- Core files: projectbrief, productContext, systemPatterns, techContext, activeContext, progress

**Code Comments**:
- Minimal inline comments in bot001.py
- Docstrings for major functions
- Comments for non-obvious logic (e.g., arrow shooting from moved piece position)

## Dependencies Management

### Required Dependencies
```python
# Standard library (always available)
import sys, time, math, random, os

# Third-party (available on Botzone)
import numpy as np
```

### Optional Dependencies (Not Used)
- TensorFlow, PyTorch: Available on Botzone but not used (custom inference)
- JSON libraries: Available but using simplified I/O
- SciPy: Available but not needed

### Evaluation Weights
- **Phase-Based Weights**: Hardcoded in bot001.py
- **Three Phases**: Early (turns 1-10), Mid (11-20), Late (21+)
- **Components**: [Queen Territory, King Territory, Queen Position, King Position, Mobility]
- **Example**: EARLY_WEIGHTS = [0.08, 0.06, 0.60, 0.68, 0.02]

## Build & Deployment

### For Botzone Submission

**Single-File Deployment**:
1. Bot code is self-contained in one file (bot001.py)
2. No external files needed (no weights to upload)
3. No build step required
4. Mark "Use Simplified Interaction" checkbox
5. Mark "Use Long-Running Mode" checkbox

**Multi-File Deployment** (if needed in future):
- Python: Bundle as zip with `__main__.py` entry point
- C++: Use amalgamation tool to merge into single file

## Performance Profiling

**Time Budget Allocation** (4-second turn):
- Board reconstruction: 0.01 seconds
- MCTS search: 3.8 seconds (95% of time)
- Output: 0.01 seconds
- Buffer: 0.18 seconds (safety margin)

**Bottlenecks**:
1. Move generation in early game (many legal moves)
2. BFS territory calculation in evaluation
3. MCTS node creation overhead
4. Board copying for simulation

**Optimization Opportunities**:
- Cache territory calculations
- Move ordering/pruning
- Transposition table
- Parallel MCTS (not beneficial on single core)
- Incremental evaluation updates
