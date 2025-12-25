# Bot Integration Interface Specification

## Overview

This document specifies the interface for integrating Amazing Amazons AI bots into external applications, particularly GUI-based board game implementations. The bots follow the **Botzone protocol** with support for **long-running mode** to minimize startup overhead.

## Protocol Fundamentals

### Communication Channels
- **Input**: Standard input (stdin) - text-based, line-oriented
- **Output**: Standard output (stdout) - text-based, line-oriented
- **Error Output**: Standard error (stderr) - for debugging/logging
- **Process Control**: Subprocess lifecycle management

### Bot Execution Model
Bots can operate in two modes:
1. **One-shot mode**: Process starts, processes one turn, exits
2. **Long-running mode**: Process stays alive between turns (recommended)

## Input Protocol Specification

### First Turn Input Format

```
<turn_id>
<move_history_line_1>
<move_history_line_2>
...
<move_history_line_N>
```

Where:
- `turn_id`: Integer (1 for first turn)
- `N = 2 * turn_id - 1` (number of history lines to read)
- Each `move_history_line` contains either:
  - `-1 -1 -1 -1 -1 -1` (no previous move)
  - `x0 y0 x1 y1 x2 y2` (actual move coordinates)

### First Turn Examples

**Black's first turn (turn_id = 1):**
```
1
-1 -1 -1 -1 -1 -1
```

**White's first turn (turn_id = 1, after Black moved):**
```
1
2 0 3 1 4 2  # Black's move (example)
```

### Subsequent Turns Input Format

In long-running mode, after the first turn, the bot receives only the opponent's last move:

```
<opponent_move>
```

Where `opponent_move` is `x0 y0 x1 y1 x2 y2` or `-1 -1 -1 -1 -1 -1`.

## Output Protocol Specification

### Move Output Format

```
x0 y0 x1 y1 x2 y2
```

Where:
- `(x0, y0)`: Starting position of amazon (0-7, 0-7)
- `(x1, y1)`: Ending position of amazon (0-7, 0-7)
- `(x2, y2)`: Arrow obstacle position (0-7, 0-7)

### Special Output Values

- **No legal moves**: `-1 -1 -1 -1 -1 -1`
- **Keep-running signal**: `>>>BOTZONE_REQUEST_KEEP_RUNNING<<<` (must follow move output)

### Output Sequence

For each turn, the bot must output:

```
<move>
>>>BOTZONE_REQUEST_KEEP_RUNNING<<<
```

The keep-running signal indicates the bot will stay alive for the next turn.

## Bot Types and Characteristics

### Available Bot Implementations

| Bot Name | Language | Algorithm | Strength | Speed | Dependencies |
|----------|----------|-----------|----------|-------|--------------|
| bot001.py | Python | Multi-Component MCTS | High | Medium | NumPy |
| bot001.cpp | C++ | Multi-Component MCTS | High | Fast | None |
| bot002.cpp | C++ | Optimized Bitboard MCTS | Medium-High | Very Fast | None |
| bot000.cpp | C++ | Random Move | Very Low | Fast | None |
| bot003.cpp | C++ | Simple Heuristic | Low | Fast | None |

### Execution Requirements

**Python Bots:**
- Python 3.6+
- NumPy library
- Execution: `python bots/bot001.py`

**C++ Bots:**
- Compiled binary (pre-compiled available)
- No external dependencies
- Execution: `./bots/bot001_cpp`

## Time Management

### Botzone Platform Limits
- **Python long-running**: First turn 12s, subsequent turns 4s
- **C++ long-running**: First turn 2s, subsequent turns 1s

### Local Execution Recommendations
- Reserve 10-20% time buffer for safety
- Monitor actual execution time
- Implement timeout mechanisms

## Error Handling

### Expected Bot Behaviors

1. **Valid Move Output**: Bot outputs legal move within time limit
2. **No Moves Available**: Bot outputs `-1 -1 -1 -1 -1 -1`
3. **Protocol Compliance**: Bot outputs keep-running signal after move
4. **Clean Exit**: Bot exits when stdin closes or receives EOF

### Error Conditions

| Error Type | Detection | Recovery Strategy |
|------------|-----------|-------------------|
| Timeout | No output within time limit | Forfeit game, restart bot |
| Protocol Error | Invalid output format | Log error, restart bot |
| Crash | Process exits unexpectedly | Restart bot, continue if possible |
| Illegal Move | Move violates game rules | Forfeit game, log violation |

## Integration Patterns

### Pattern 1: Subprocess Execution (Recommended)

```pseudocode
function execute_bot_turn(bot_path, game_history, time_limit):
    # Start or reuse bot process
    if not process_exists(bot_path):
        process = start_process(bot_path)
        send_first_turn_input(process, game_history)
    else:
        send_subsequent_turn_input(process, opponent_last_move)
    
    # Wait for output with timeout
    move_output = read_output_with_timeout(process, time_limit)
    keep_running = read_output_with_timeout(process, 0.5)
    
    # Validate output
    if not is_valid_move(move_output):
        handle_error()
    
    return parse_move(move_output)
```

### Pattern 2: Library Integration (C++ Only)

For C++ bots, alternative integration via direct library calls:

```cpp
// Bot interface class
class AmazonsBot {
public:
    virtual Move getMove(const GameState& state, Color color, TimeLimit limit) = 0;
    virtual void reset() = 0;
    virtual ~AmazonsBot() = default;
};

// Specific bot implementation
class Bot001 : public AmazonsBot {
    // Direct integration with bot001.cpp logic
};
```

### Pattern 3: Service/DAemon

Run bots as persistent services with network interfaces:

```
Bot Service (TCP/WebSocket)
    ↓
Bot Process Pool
    ↓
Individual Bot Instances
```

## State Management

### Game State Synchronization

Bots internally maintain game state based on move history. The integrating application must:

1. **Provide complete history**: Bots reconstruct state from all moves
2. **Handle state mismatches**: Validate bot moves against actual game state
3. **Reset when needed**: Restart bot if state desynchronization occurs

### Bot Internal State

Bots may maintain:
- Board representation
- MCTS search tree (for reuse between turns)
- Evaluation caches
- Turn counters for phase detection

## Configuration Options

### Bot-Specific Parameters

Some bots support configuration via environment variables or command-line arguments:

```bash
# Example: Adjust time limits
TIME_LIMIT=3.5 python bots/bot001.py

# Example: Set random seed
RANDOM_SEED=42 ./bots/bot001_cpp
```

### Common Configuration Points

1. **Time Limits**: Adjust based on GUI requirements
2. **Logging Level**: Control debug output
3. **Random Seed**: For reproducible behavior
4. **Evaluation Parameters**: Tune bot strength/speed tradeoff

## Testing and Validation

### Integration Test Checklist

- [ ] Bot starts successfully
- [ ] First turn protocol handled correctly
- [ ] Subsequent turns in long-running mode
- [ ] Timeout handling
- [ ] Error recovery
- [ ] Move legality validation
- [ ] Performance within limits
- [ ] Memory usage monitoring

### Sample Test Sequence

```
Test 1: Black first turn
  Input: "1\n-1 -1 -1 -1 -1 -1\n"
  Expected: Valid move + keep-running signal
  
Test 2: White first turn (after Black move)
  Input: "1\n2 0 3 1 4 2\n"
  Expected: Valid move + keep-running signal
  
Test 3: Subsequent turn
  Input: "3 1 4 2 5 3\n"
  Expected: Valid move + keep-running signal
```

## Platform Considerations

### Operating System Compatibility

- **Linux**: Fully supported (Botzone environment)
- **macOS**: Should work with same binaries
- **Windows**: May require recompilation or WSL

### Resource Requirements

**Memory:**
- Python bots: ~100 MB
- C++ bots: ~50-80 MB

**CPU:**
- Single core only (bots are single-threaded)
- No GPU requirements

**Disk:**
- Minimal (bot binaries + temporary files)

## Security Considerations

### Sandboxing Recommendations

When executing untrusted bots:
- Run in isolated containers/namespaces
- Limit system resource access
- Monitor for malicious behavior
- Validate all output before use

### Input Validation

- Sanitize all input to bots
- Validate bot output before applying to game
- Limit maximum input size
- Handle malformed input gracefully

## Version Compatibility

### Bot Versioning

Bots follow semantic versioning:
- `bot001_v1.0.py` - Initial version
- `bot001_v1.1.py` - Bug fixes
- `bot002_v2.0.cpp` - Major algorithm change

### Protocol Versioning

- **v1.0**: Current Botzone protocol
- Future versions may add JSON support or extended features

## Troubleshooting

### Common Issues

1. **Bot hangs on first turn**
   - Check Python/NumPy installation
   - Verify input format
   - Increase timeout for first turn

2. **Illegal moves returned**
   - Bot may have internal state corruption
   - Restart bot process
   - Verify move history provided

3. **Performance degradation**
   - Monitor memory usage
   - Check for memory leaks
   - Restart bot periodically

4. **Protocol errors**
   - Ensure keep-running signal follows move
   - Check line endings (LF vs CRLF)
   - Verify stdout flushing

### Debugging Tools

- Enable bot debug logging
- Capture stdin/stdout streams
- Use tournament system for validation
- Compare with known good sequences

## References

1. [Botzone Wiki](wiki/) - Platform documentation
2. [Bot Implementations](docs/bots/) - Bot-specific documentation
3. [Tournament System](docs/manuals/tournament_system_manual.md) - Testing framework
4. [Game Rules](memorybank/projectbrief.md) - Amazons game specifications

## Appendix A: Complete Protocol Example

### Game Sequence Example

```
Turn 1 (Black):
  Input to bot: "1\n-1 -1 -1 -1 -1 -1\n"
  Output from bot: "2 0 3 1 4 2\n>>>BOTZONE_REQUEST_KEEP_RUNNING<<<"

Turn 2 (White):
  Input to bot: "1\n2 0 3 1 4 2\n"
  Output from bot: "0 5 1 4 2 3\n>>>BOTZONE_REQUEST_KEEP_RUNNING<<<"

Turn 3 (Black):
  Input to bot: "0 5 1 4 2 3\n"
  Output from bot: "3 1 4 0 5 1\n>>>BOTZONE_REQUEST_KEEP_RUNNING<<<"
```

### Error Sequence Example

```
Turn 1 (Black):
  Input: "1\n-1 -1 -1 -1 -1 -1\n"
  Output: "2 0 3 1 4 2\n"  # Missing keep-running signal
  Action: Protocol error, restart bot
```

## Appendix B: Quick Reference

### Command Summary

```bash
# Test bot functionality
python scripts/test_bot_simple.py

# Run tournament match
python scripts/tournament/cli.py match bot001 bot002

# Compile C++ bot
g++ -O2 -std=c++11 -o bots/bot001_cpp bots/bot001.cpp
```

### File Locations

- Bot implementations: `bots/`
- Compiled binaries: `bots/` (with `_cpp` suffix)
- Test scripts: `scripts/`
- Documentation: `docs/interfaces/`

---

*Last Updated: 2025-12-25*