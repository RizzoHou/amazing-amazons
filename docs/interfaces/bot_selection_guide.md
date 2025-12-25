# Bot Selection and Configuration Guide

## Overview

This guide helps GUI developers choose and configure the appropriate Amazing Amazons AI bot for their integration needs. It covers bot characteristics, performance profiles, configuration options, and selection criteria.

## Bot Catalog

### bot001.py - Multi-Component MCTS (Python)

**Algorithm**: Monte Carlo Tree Search with Multi-Component Evaluation
**Strength**: High (tournament-proven)
**Speed**: Medium (3.8s per move average)
**Memory**: ~100 MB
**Dependencies**: Python 3.6+, NumPy

**Characteristics:**
- Sophisticated 5-component evaluation function
- Phase-aware weights (early/mid/late game)
- Dynamic UCB exploration constant
- Tree reuse between turns
- Long-running mode optimized

**Best For:**
- High-quality AI opponents
- When Python environment is available
- Non-time-critical applications
- Research and analysis

### bot001.cpp - Multi-Component MCTS (C++)

**Algorithm**: Same as bot001.py, ported to C++
**Strength**: High (identical to Python version)
**Speed**: Fast (0.9s per move average, 4.15× faster)
**Memory**: ~80 MB
**Dependencies**: None (standalone binary)

**Characteristics:**
- Identical algorithm to Python version
- No external dependencies
- Optimized for C++ time limits
- Production-ready

**Best For:**
- Production GUI applications
- Performance-critical scenarios
- Cross-platform deployment
- When Python dependencies are undesirable

### bot002.cpp - Optimized Bitboard MCTS (C++)

**Algorithm**: Bitboard-based MCTS with optimizations
**Strength**: Medium-High (slightly weaker than bot001)
**Speed**: Very Fast (1.1s per move average)
**Memory**: ~50 MB
**Dependencies**: None (standalone binary)

**Characteristics:**
- Bitboard representation (3× uint64_t)
- Optimized move generation
- Fast BFS with fixed arrays
- Xorshift64 PRNG
- Move ordering heuristic

**Best For:**
- Maximum speed requirements
- Resource-constrained environments
- When slight strength reduction is acceptable
- Testing and rapid iteration

### bot000.cpp - MCTS Bot (Identical to bot003)

**Algorithm**: Multi-Component Monte Carlo Tree Search
**Strength**: Medium-High (similar to bot001)
**Speed**: Fast (similar to bot001.cpp)
**Memory**: ~80 MB
**Dependencies**: None

**Characteristics:**
- Multi-component evaluation function
- Phase-aware weights (early/mid/late game)
- Dynamic UCB exploration constant
- Tree reuse between turns
- Long-running mode optimized

**Best For:**
- High-quality AI opponents
- When bot001.cpp is not available
- Testing and comparison with bot003
- Alternative MCTS implementation

### bot003.cpp - MCTS Bot (Identical to bot000)

**Algorithm**: Multi-Component Monte Carlo Tree Search
**Strength**: Medium-High (similar to bot001)
**Speed**: Fast (similar to bot001.cpp)
**Memory**: ~80 MB
**Dependencies**: None

**Characteristics:**
- Multi-component evaluation function
- Phase-aware weights (early/mid/late game)
- Dynamic UCB exploration constant
- Tree reuse between turns
- Long-running mode optimized

**Best For:**
- High-quality AI opponents
- When bot001.cpp is not available
- Testing and comparison with bot000
- Alternative MCTS implementation

## Selection Criteria

### Based on Application Requirements

| Requirement | Recommended Bot | Rationale |
|-------------|----------------|-----------|
| Maximum Strength | bot001.cpp | Highest quality moves, tournament-proven |
| Maximum Speed | bot002.cpp | Fastest computation, bitboard optimized |
| Python Environment | bot001.py | Native Python, easier integration |
| Minimal Dependencies | bot001.cpp/bot002.cpp | No external libraries needed |
| Beginner Opponent | bot000.cpp | MCTS bot, easier than bot001 |
| Intermediate Opponent | bot003.cpp | MCTS bot, similar to bot000 |
| Research/Education | bot001.py | Transparent Python implementation |
| Production Deployment | bot001.cpp | Balance of strength and speed |

### Based on Hardware Constraints

**Low-end Systems (≤ 2GB RAM, slow CPU):**
- bot002.cpp (optimized memory usage)
- bot003.cpp (minimal resource requirements)

**Mid-range Systems (4-8GB RAM, modern CPU):**
- bot001.cpp (good balance)
- bot001.py (if Python available)

**High-end Systems (≥ 16GB RAM, fast CPU):**
- Any bot, consider bot001.cpp for best quality

### Based on Time Constraints

**Real-time (< 1s per move):**
- bot002.cpp (1.1s average)
- bot003.cpp (0.5s average)

**Near-real-time (1-3s per move):**
- bot001.cpp (0.9s average)

**Turn-based (3-10s per move):**
- bot001.py (3.8s average)
- bot001.cpp with increased time limit

## Configuration Options

### Time Limit Adjustment

All bots respect time limits internally. For GUI integration, you can:

1. **Set Environment Variables:**
```bash
# Python bot
TIME_LIMIT=2.0 python bots/bot001.py

# C++ bot (if supported)
TIME_LIMIT=1.5 ./bots/bot001_cpp
```

2. **Modify Source Code:**
- Python: Change `TIME_LIMIT` and `FIRST_TURN_TIME_LIMIT` constants
- C++: Change `TIME_LIMIT` and `FIRST_TURN_TIME_LIMIT` constants

3. **External Timeout:**
- Implement timeout at subprocess level
- Kill process if exceeds GUI time budget

### Difficulty Adjustment

**Method 1: Time Limit Scaling**
```python
# Easier: Less thinking time
easy_time = base_time * 0.5

# Harder: More thinking time  
hard_time = base_time * 2.0
```

**Method 2: Iteration Limit (Advanced)**
Modify bot source to limit MCTS iterations:
```python
# In bot001.py search() method
max_iterations = difficulty_level * 1000
while iterations < max_iterations and time_remaining:
    # MCTS iteration
```

**Method 3: Multiple Bot Strategy**
- Easy: bot000.cpp (MCTS bot, easier than bot001)
- Medium: bot003.cpp (MCTS bot, similar to bot000)
- Hard: bot002.cpp (optimized MCTS)
- Expert: bot001.cpp (full MCTS)

### Random Seed Control

For reproducible behavior:
```bash
# Set random seed
RANDOM_SEED=12345 ./bots/bot001_cpp

# Or modify in source code
random.seed(configured_seed)  # Python
srand(configured_seed);       # C++
```

## Performance Profiles

### Speed vs Strength Trade-off

```
Strength (Higher is better)
    ↑
    |       bot001.cpp
    |      /
    |     /
    |    /   bot002.cpp
    |   /   /
    |  /   /
    | /   /
    |/   bot003.cpp
    |   /
    |  /
    | /
    |/
    +----------------→ Speed (Faster is better)
     bot000.cpp
```

### Memory Usage Patterns

**Python Bots:**
- Initial: ~50 MB
- Peak: ~100 MB (MCTS tree growth)
- Stable: ~80 MB (after tree pruning)

**C++ Bots:**
- Initial: ~20 MB
- Peak: ~80 MB (bot001.cpp)
- Stable: ~50 MB (bot002.cpp)

### Time Distribution

**bot001.py per turn:**
- Board reconstruction: 0.01s (0.3%)
- MCTS search: 3.8s (99%)
- Output: 0.01s (0.3%)
- Buffer: 0.18s (safety margin)

**bot001.cpp per turn:**
- Board reconstruction: < 0.01s
- MCTS search: 0.9s (97%)
- Output: < 0.01s
- Buffer: 0.1s (safety margin)

## Integration Considerations

### Subprocess Management

**Process Pool Strategy:**
```python
# Maintain pool of bot processes
bot_pool = {
    'easy': BotProcess('bots/bot000_cpp'),
    'medium': BotProcess('bots/bot003_cpp'),
    'hard': BotProcess('bots/bot002_cpp'),
    'expert': BotProcess('bots/bot001_cpp')
}
```

**Lifecycle Management:**
- Start bot on first use
- Keep alive for session duration
- Restart on error or memory growth
- Clean shutdown on application exit

### State Synchronization

**Challenge:** Bots maintain internal game state
**Solution:** Provide complete move history each game

```python
def play_game_with_bot(bot, initial_state):
    moves = []
    state = initial_state
    
    while not game_over(state):
        # Send all previous moves for state reconstruction
        bot_move = bot.get_move(moves, state.current_player)
        
        # Validate move against actual state
        if is_legal_move(state, bot_move):
            apply_move(state, bot_move)
            moves.append(bot_move)
        else:
            # State desynchronization - restart bot
            bot.restart()
            # Replay all moves to resynchronize
            for move in moves:
                bot.send_move(move)
```

### Error Recovery Strategies

1. **Timeout Recovery:**
```python
try:
    move = bot.get_move_with_timeout(time_limit)
except TimeoutError:
    bot.restart()
    # Use fallback move or forfeit
```

2. **Protocol Error Recovery:**
```python
if not is_valid_protocol_response(response):
    log_error(f"Protocol error: {response}")
    bot.restart()
    # Retry with same input
```

3. **Crash Recovery:**
```python
if not bot.process.is_alive():
    log_error("Bot process crashed")
    bot = BotProcess(bot.path)  # Fresh instance
    # Replay game history if possible
```

## Testing and Validation

### Bot Compatibility Test

```python
def test_bot_compatibility(bot_path):
    """Verify bot follows protocol and produces legal moves"""
    
    test_cases = [
        ("First turn Black", "1\n-1 -1 -1 -1 -1 -1\n"),
        ("First turn White", "1\n2 0 3 1 4 2\n"),
        ("Subsequent turn", "3 1 4 2 5 3\n")
    ]
    
    for name, input_data in test_cases:
        result = run_bot_test(bot_path, input_data)
        if not result.valid:
            return False, f"{name} failed: {result.error}"
    
    return True, "All tests passed"
```

### Performance Benchmark

```python
def benchmark_bot(bot_path, num_games=10):
    """Measure bot performance characteristics"""
    
    metrics = {
        'avg_time_per_move': [],
        'memory_usage': [],
        'move_quality': [],  # vs reference bot
        'reliability': []    # success rate
    }
    
    for game in range(num_games):
        # Run game and collect metrics
        game_metrics = run_game_and_measure(bot_path)
        for key in metrics:
            metrics[key].append(game_metrics[key])
    
    return compute_statistics(metrics)
```

## Advanced Configuration

### Custom Evaluation Weights

For bot001.py/bot001.cpp, you can modify phase weights:

```python
# Early game (turns 1-10)
EARLY_WEIGHTS = [0.08, 0.06, 0.60, 0.68, 0.02]
# Components: [QueenTerritory, KingTerritory, QueenPosition, KingPosition, Mobility]

# Adjust for more aggressive/defensive play
AGGRESSIVE_WEIGHTS = [0.10, 0.08, 0.65, 0.70, 0.05]  # More mobility focus
DEFENSIVE_WEIGHTS = [0.12, 0.10, 0.55, 0.60, 0.01]   # More territory focus
```

### Opening Book Integration

Add opening book support:

```python
class BotWithOpeningBook:
    def __init__(self, bot, opening_book):
        self.bot = bot
        self.opening_book = opening_book
    
    def get_move(self, game_state):
        # Check opening book first
        book_move = self.opening_book.lookup(game_state)
        if book_move:
            return book_move
        
        # Fall back to regular bot
        return self.bot.get_move(game_state)
```

### Adaptive Difficulty

```python
class AdaptiveBot:
    def __init__(self, easy_bot, medium_bot, hard_bot):
        self.bots = [easy_bot, medium_bot, hard_bot]
        self.current_level = 1  # Medium
        
    def adjust_difficulty(self, player_skill):
        """Adjust based on player win rate"""
        if player_win_rate > 0.7:
            self.current_level = min(2, self.current_level + 1)
        elif player_win_rate < 0.3:
            self.current_level = max(0, self.current_level - 1)
    
    def get_move(self, game_state):
        return self.bots[self.current_level].get_move(game_state)
```

## Deployment Checklist

### Pre-deployment Verification
- [ ] Bot compiles/runs on target platform
- [ ] Protocol compliance verified
- [ ] Performance within acceptable limits
- [ ] Memory usage stable
- [ ] Error handling tested
- [ ] Timeout handling tested
- [ ] Move legality verified
- [ ] Multiple game test passed

### Runtime Monitoring
- [ ] Process health monitoring
- [ ] Performance metrics collection
- [ ] Error logging enabled
- [ ] Resource usage tracking
- [ ] Move validation active
- [ ] Recovery procedures tested

### Maintenance Considerations
- [ ] Bot update procedure defined
- [ ] Configuration management
- [ ] Log rotation configured
- [ ] Backup strategies in place
- [ ] Rollback procedure tested

## Troubleshooting Guide

### Common Issues and Solutions

**Issue: Bot returns illegal moves**
- Cause: State desynchronization
- Solution: Restart bot, replay move history

**Issue: Bot times out frequently**
- Cause: Hardware too slow or time limit too tight
- Solution: Increase time limit, use faster bot (bot002.cpp)

**Issue: Memory usage grows over time**
- Cause: Memory leak in bot or MCTS tree not pruned
- Solution: Restart bot periodically, monitor memory

**Issue: Bot crashes on specific positions**
- Cause: Bug in bot implementation
- Solution: Use different bot, report bug to maintainers

**Issue: Inconsistent strength**
- Cause: Random seed or non-deterministic behavior
- Solution: Set fixed random seed, use deterministic bot

## Best Practices

### For GUI Developers
1. **Always validate bot moves** against game rules
2. **Implement timeouts** at application level
3. **Monitor bot process health**
4. **Provide complete move history** to bots
5. **Handle bot failures gracefully**
6. **Log bot interactions** for debugging
7. **Test with multiple bot types**
8. **Consider player skill level** when selecting bot

### For Bot Configuration
1. **Start with bot001.cpp** for balanced performance
2. **Adjust time limits** based on GUI requirements
3. **Use environment variables** for configuration
4. **Implement fallback strategies** for bot failures
5. **Regularly update bots** to latest versions
6. **Monitor performance metrics**
7. **Collect user feedback** on bot difficulty

## References

- [Bot Integration Interface](bot_integration_interface.md) - Protocol details
- [Bot Implementations](../bots/) - Source code and documentation
- [Tournament System](../manuals/tournament_system_manual.md) - Testing framework
- [Performance Reports](../reports/) - Benchmark results

---

*Last Updated: 2025-12-25*