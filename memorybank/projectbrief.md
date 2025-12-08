# Project Brief: Amazing Amazons

## Overview
Amazing Amazons is a project focused on developing high-intelligence AI bots for playing the Game of Amazons. This is a new version of a previous AmazingAmazons project, aimed at creating competitive bots that can run on the Botzone platform.

## Core Objectives
1. **Develop intelligent AI bots** capable of playing the Game of Amazons at a high level
2. **Design for Botzone platform** - all bots must be compatible with Botzone's execution environment and interaction protocols
3. **Optimize for long-running mode** - utilize Botzone's long-running bot feature to minimize cold-start overhead
4. **Iterative improvement** - build upon previous work, starting with the best existing bot (bot001)

## Game: Amazons
- **Board**: 8x8 grid
- **Pieces**: Each player (Black/White) has 4 amazons
- **Movement**: Amazons move like chess queens (8 directions, any distance)
- **Turn structure**: 
  1. Select and move one amazon to empty square
  2. From new position, shoot an arrow (also moves like queen) to place an obstacle
  3. Obstacles permanently block movement
- **Win condition**: Opponent cannot make any legal move
- **First move**: Black (upper side of board) moves first

## Platform Constraints

### Botzone Time Limits
**Python Long-Running Bots:**
- First turn: 12 seconds
- Subsequent turns: 4 seconds

**C++ Long-Running Bots:**
- First turn: 2 seconds  
- Subsequent turns: 1 second

### Other Limits
- Memory: 256 MB (unless specified otherwise)
- Single CPU core (multi-threading doesn't improve performance)

## Current State
- One working bot imported from previous project: `bots/bot001.py`
- Bot001 is currently the best-performing bot
- Core game logic implemented in `core/game.py`
- Additional AI utilities in `core/ai.py` (older MCTS implementation)
- Wiki documentation stored in `wiki/` folder for reference

## Success Criteria
- Bots perform competitively on Botzone platform
- Consistent adherence to time and memory constraints
- Progressive improvement in bot intelligence through iterations
- Clean, maintainable codebase with proper documentation
