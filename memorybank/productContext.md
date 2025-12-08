# Product Context

## Why This Project Exists

This project exists to develop competitive AI bots for the Game of Amazons that can compete on the Botzone platform. The Game of Amazons is a complex two-player zero-sum game with complete information, featured in international computer game competitions (ICGA) and national Chinese college computer game contests.

## Problems It Solves

1. **Computational Challenge**: Amazons has an enormous branching factor (hundreds of legal moves per position), making it computationally expensive to search deeply
2. **Strategic Complexity**: The game requires both tactical (immediate move quality) and strategic thinking (territory control, mobility)
3. **Time Constraints**: Bots must make high-quality decisions within strict time limits (1-12 seconds)
4. **Platform Integration**: Bots must correctly interface with Botzone's interaction protocols and long-running mode

## How It Works

### User Experience (Bot Competition Flow)

1. **Submission**: User submits bot code to Botzone platform
2. **Matching**: Botzone pairs the bot against other bots or human players
3. **Execution**: 
   - Bot receives game state via stdin (simplified or JSON format)
   - Bot processes the state and computes best move
   - Bot outputs move via stdout
   - For long-running bots, process stays alive between turns
4. **Evaluation**: Performance tracked through ELO ratings and match results

### AI Strategy

The current best bot (bot001) uses:
- **Multi-Component Evaluation**: Five strategic components (territory, position, mobility) combined with phase-aware weights to evaluate board positions
- **Monte Carlo Tree Search (MCTS)**: Explores game tree by balancing exploration vs exploitation with dynamic UCB constant
- **Long-Running Optimization**: Maintains MCTS tree between turns to reuse computation

## Target Outcomes

1. **High Win Rate**: Bots should consistently win against random/weak opponents and compete well against strong opponents
2. **Efficient Computation**: Maximize search depth and evaluation quality within time constraints
3. **Robustness**: Handle edge cases, endgame scenarios, and unusual positions correctly
4. **Progressive Improvement**: Each new bot version should measurably improve upon previous versions

## User Journey

### Development Workflow
1. Develop/improve bot locally
2. Test against previous versions
3. Submit to Botzone
4. Analyze match logs and performance
5. Identify weaknesses
6. Iterate on improvements

### Key Pain Points Addressed
- **Cold Start Overhead**: Long-running mode keeps MCTS tree intact between turns
- **Time Management**: Careful time budgeting ensures moves complete within limits
- **Position Evaluation**: Multi-component heuristic provides fast evaluation without rollout overhead
- **Search Efficiency**: MCTS with dynamic UCB focuses computation on promising branches

## Interaction Model

### With Botzone Platform
- **Input**: Receives game history (all previous moves) via stdin
- **Processing**: Internally reconstructs board state and computes next move
- **Output**: Emits move coordinates followed by keep-running signal
- **State Persistence**: Maintains internal state (board, MCTS tree) between turns

### Between Bot Versions
- Bots are versioned (bot001, bot002, etc.)
- Previous versions archived for testing/comparison
- Core game logic available in `core/` module (though bot001 is self-contained)
- Each bot can have different evaluation strategies and MCTS parameters
