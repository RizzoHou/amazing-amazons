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
├── bots/             # Individual bot implementations
│   └── bot001.py     # Current best bot (Multi-Component MCTS)
├── models/           # Reserved for future neural network weights
├── memorybank/       # Project documentation (Cline memory system)
├── wiki/             # Botzone platform documentation
├── scripts/          # Testing and utility scripts (to be developed)
├── logs/             # Match logs
├── reports/          # Analysis reports
├── results/          # Performance metrics
└── docs/             # Implementation documentation
    └── bot_implementation/
        └── bot001_implementation.md  # Comprehensive bot001 documentation
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

✅ **Complete**: Project initialization, memory bank documentation, and development workflows  
🔄 **In Progress**: Bot verification and testing infrastructure  
📅 **Planned**: Botzone submission and performance optimization

**Recent Updates** (January 8, 2025):
- Created comprehensive bot001 implementation documentation (700+ lines)
- Established standardized development workflows (task completion, README updates)
- Reorganized development rules for better maintainability

See [`memorybank/progress.md`](memorybank/progress.md) for detailed status.

## Bot Architecture

### Bot001: Multi-Component MCTS

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
- First turn time limit: 12 seconds (using 5.8s conservatively)
- Subsequent turns: 4 seconds (using 3.8s with buffer)
- Typical MCTS iterations: 1000-5000 per turn
- Evaluation speed: < 0.001s per position

## Usage

### Running Locally

Test bot with sample input:
```bash
echo "1
-1 -1 -1 -1 -1 -1" | python bots/bot001.py
```

### Submitting to Botzone

1. Prepare bot file (bot001.py is single-file, ready to submit)
2. No external files needed (fully self-contained)
3. Submit bot on Botzone with these settings:
   - ✅ Use Simplified Interaction
   - ✅ Use Long-Running Mode
4. Test and monitor performance

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

- [`docs/bot_implementation/bot001_implementation.md`](docs/bot_implementation/bot001_implementation.md) - Comprehensive bot001 documentation covering all modules, algorithms, and design decisions

## References

- [Botzone Platform](https://www.botzone.org.cn/)
- [Amazons Game Rules (Wiki)](wiki/Amazons%20-%20Botzone%20Wiki.pdf)
- [Bot Development Guide (Wiki)](wiki/Bot%20-%20Botzone%20Wiki.pdf)

## Next Steps

1. ✅ Initialize project structure and documentation
2. ✅ Create comprehensive implementation documentation
3. ✅ Establish development workflows
4. 🔄 Verify bot001 functionality with all dependencies
5. 📅 Create testing infrastructure
6. 📅 Submit to Botzone and establish baseline performance
7. 📅 Optimize and iterate

## License

[To be determined]

## Contributing

This is currently a personal project. Testing and feedback welcome!

---

**Note**: This project is in active development. Bot001 is imported from a previous project and represents the current best implementation using multi-component heuristic evaluation inspired by strong opponent bots. Future versions may explore neural network evaluation, opening books, and other advanced techniques.
