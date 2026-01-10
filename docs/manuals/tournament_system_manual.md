# Tournament System Manual

## Overview

The Amazons Tournament System is a comprehensive tool for testing and evaluating Amazons (Amazon Chess) bots. It simulates the Botzone platform environment locally, allowing you to:

- Run head-to-head matches between bots
- Conduct round-robin tournaments
- Test bot reliability and detect common issues (TLE, illegal moves)
- Compile and manage bot executables

The system implements the exact Botzone protocol for Amazons, ensuring that bots tested locally will behave identically on the actual Botzone platform.

## Installation and Setup

### Prerequisites

- Python 3.7+
- g++ compiler (for C++ bots)
- Virtual environment (recommended)

### Setup

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd amazing-amazons
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt  # If requirements.txt exists
   ```

4. **Verify setup**:
   ```bash
   python -m scripts.tournament.cli --help
   ```

## Bot Requirements

### Bot Structure

Bots should be placed in the `bots/` directory with the following naming convention:
- Source code: `bots/{bot_name}.cpp` (e.g., `bots/bot003.cpp`)
- Executable: `bots/{bot_name}` (e.g., `bots/bot003`)

### Bot Protocol Compliance

Bots must follow the Botzone Amazons protocol:

1. **Input Format**:
   - First line: Turn ID (integer)
   - Subsequent lines: Move history (6 integers per line: x0 y0 x1 y1 x2 y2)
   - First request for Black: `-1 -1 -1 -1 -1 -1`

2. **Output Format**:
   - Move: 6 integers separated by spaces (x0 y0 x1 y1 x2 y2)
   - No legal moves: `-1 -1 -1 -1 -1 -1`
   - Keep-running signal: `>>>BOTZONE_REQUEST_KEEP_RUNNING<<<`

3. **Time Limits**:
   - First turn: 2.0 seconds
   - Subsequent turns: 2.0 seconds
   - The system will detect Time Limit Exceeded (TLE) and handle it appropriately

## CLI Commands

The tournament system provides a command-line interface with five main commands:

```bash
python -m scripts.tournament.cli <command> [options]
```

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `match` | Run a single match between two bots | `match bot000 bot003` |
| `series` | Run multiple matches between two bots | `series bot021 bot022 -n 10` |
| `tournament` | Run a round-robin tournament | `tournament bot000 bot001 bot002` |
| `test` | Run specific tests | `test bot002` or `test bot000_vs_bot003` |
| `compile` | Compile a bot from source | `compile bot003` |

### Common Options

- `--quiet`: Reduce output verbosity
- `--help`: Show help for specific command

## Running Matches

### Basic Match

Run a single match between two bots:

```bash
python -m scripts.tournament.cli match bot000 bot003
```

### Output Example

```
============================================================
Match: bot000 vs bot003
============================================================

Starting game: bot000 vs bot003
  Turn 1: bot000's move...
    bot000 move: 2 0 2 6 7 6
  Turn 2: bot003's move...
    bot003 move: 5 0 5 6 0 6
  ...
  Game finished: bot000 wins in 27 moves

✓ Match completed: bot000 wins in 27 moves
```

### Match Details

The system will:
1. Check if bots exist, compile if needed
2. Start both bot processes
3. Play the game following Botzone protocol
4. Track board state and validate moves
5. Detect end conditions (no legal moves)
6. Report winner and number of moves

## Running Series (Head-to-Head Matches)

The `series` command allows running multiple matches between two specific bots with configurable color assignments.

### Basic Series

Run a series of matches between two bots:

```bash
python -m scripts.tournament.cli series bot021 bot022 -n 10
```

This runs 10 matches with colors split evenly (5 matches with bot021 as Black, 5 with bot021 as White).

### Configuring Color Distribution

Specify how many matches a bot plays as Black:

```bash
# bot021 plays Black in 8 out of 10 matches
python -m scripts.tournament.cli series bot021 bot022 -n 10 --bot1-black 8

# bot021 plays Black in all matches
python -m scripts.tournament.cli series bot021 bot022 -n 10 --bot1-black 10
```

### Series Options

| Option | Description | Default |
|--------|-------------|---------|
| `-n, --matches` | Total number of matches | 10 |
| `--bot1-black` | Matches where bot1 plays Black | Half of total |
| `--report, -r` | Generate markdown report | Off |
| `--unlimited, -u` | Don't enforce time limits | Off |
| `--quiet, -q` | Reduce output | Off |

### Output Example

```
Series: bot021 vs bot022
Total matches: 10
  bot021 as Black: 5
  bot021 as White: 5
Time limits: 2.0s / 1.0s

Match 1/10: bot021 (Black) vs bot022 (White)
...
  Running: bot021 1-0 bot022

...

SERIES SUMMARY

bot021:
  Total: 7 wins, 3 losses
  As Black: 4 wins
  As White: 3 wins

bot022:
  Total: 3 wins, 7 losses
  As Black: 2 wins
  As White: 1 wins

Win rate: bot021 70.0% - bot022 30.0%
```

## Running Tournaments

### Basic Tournament

Run a round-robin tournament between multiple bots:

```bash
python -m scripts.tournament.cli tournament bot000 bot001 bot002 bot003
```

### Tournament Format

- Each bot plays every other bot once
- Results are tracked (wins, losses, errors)
- Final standings are sorted by wins

### Output Example

```
============================================================
Tournament: bot000 vs bot001 vs bot002 vs bot003
============================================================

========================================
Match 1: bot000 vs bot001
========================================
...

========================================
Match 2: bot000 vs bot002
========================================
...

============================================================
TOURNAMENT RESULTS
============================================================
bot003: 3 wins, 0 losses, 0 errors
bot000: 2 wins, 1 loss, 0 errors
bot001: 1 win, 2 losses, 0 errors
bot002: 0 wins, 3 losses, 0 errors
```

## Testing Bots

### Available Tests

The system includes two specialized tests:

1. **`bot002` Test**: Self-play test to detect illegal movements or TLE
   ```bash
   python -m scripts.tournament.cli test bot002
   ```

2. **`bot000_vs_bot003` Test**: Reliability test between two known stable bots
   ```bash
   python -m scripts.tournament.cli test bot000_vs_bot003
   ```

### Test Purposes

- **bot002 test**: Detects common bot issues:
  - Illegal moves (moves that violate game rules)
  - Invalid moves (malformed output)
  - Time Limit Exceeded (TLE)
  - Protocol violations

- **bot000_vs_bot003 test**: Verifies tournament system stability:
  - Ensures games complete naturally
  - Detects system-level bugs
  - Validates move validation logic

## Compiling Bots

### Automatic Compilation

The system automatically compiles bots when needed. Manual compilation is also available:

```bash
python -m scripts.tournament.cli compile bot003
```

### Custom Source Path

```bash
python -m scripts.tournament.cli compile bot003 --source path/to/custom.cpp
```

### Compilation Details

- Compiler: `g++`
- Flags: `-O3 -std=c++11`
- Output: `bots/{bot_name}`
- Source: `bots/{bot_name}.cpp` (default)

## Understanding Results

### Success Indicators

- **✓ Match completed**: Game finished normally
- **✓ Test passed**: Test met its objectives
- **✓ Bot compiled successfully**: Compilation succeeded

### Error Indicators

- **✗ Match error**: Game terminated due to error
- **✗ Test failed**: Test did not meet objectives
- **✗ Compilation failed**: Source code compilation error

### Common Error Messages

| Error Message | Meaning | Possible Causes |
|--------------|---------|-----------------|
| `made invalid move` | Bot output couldn't be parsed | Malformed output, wrong format |
| `has no legal moves` | Bot correctly signaled end of game | Normal game end condition |
| `TLE` | Time Limit Exceeded | Bot took too long to respond |
| `protocol error` | Bot violated protocol | Wrong keep-running signal, etc. |
| `illegal move` | Move violates game rules | Bug in bot's move generation |

## Troubleshooting

### Common Issues

1. **Bot not found**:
   ```
   ✗ Cannot run match: bot003 compilation failed
   ```
   **Solution**: Ensure `bots/bot003.cpp` exists and compiles successfully.

2. **Permission denied**:
   ```
   PermissionError: [Errno 13] Permission denied
   ```
   **Solution**: Make bot executable: `chmod +x bots/bot003`

3. **TLE (Time Limit Exceeded)**:
   ```
   bot003 TLE on first turn
   ```
   **Solution**: Optimize bot algorithm or increase time limit in `bot_runner.py`.

4. **Protocol violations**:
   ```
   Warning: bot003 keep-running mismatch: None
   ```
   **Solution**: Ensure bot outputs `>>>BOTZONE_REQUEST_KEEP_RUNNING<<<` after each move.

### Debugging Tips

1. **Enable verbose output**: Remove `--quiet` flag for detailed logs
2. **Check bot output manually**: Run bot directly to see its output
3. **Review move validation**: Use `scripts/debug_board.py` to analyze board states
4. **Examine game logs**: Moves are stored in `results/` directory

## Architecture Overview

### System Components

```
scripts/tournament/
├── cli.py              # Command-line interface
├── game_engine.py      # Game logic and state management
├── bot_runner.py       # Bot process management
└── utils.py           # Utility functions (compilation, etc.)
```

### Key Classes

1. **`FixedGame`** (`game_engine.py`):
   - Manages game state
   - Validates moves
   - Tracks board position
   - Handles game end conditions

2. **`ProperBot`** (`bot_runner.py`):
   - Manages bot subprocess
   - Implements Botzone protocol
   - Handles timeouts
   - Manages keep-running mode

3. **`Board`** (`core/game.py`):
   - Game board representation
   - Move generation
   - Move validation
   - Board state tracking

### Protocol Implementation

The system implements the exact Botzone protocol:

1. **First Turn**:
   - Send turn ID (1)
   - Send request (`-1 -1 -1 -1 -1 -1` for Black, opponent move for White)
   - Read move and keep-running signal

2. **Keep-Running Mode**:
   - Send opponent's last move
   - Read move and keep-running signal
   - Continue until game ends

## Advanced Usage

### Custom Time Limits

Modify time limits in `scripts/tournament/bot_runner.py`:

```python
def __init__(self, bot_path: str, bot_name: str = "Unknown", time_limit: float = 2.0):
    # Change time_limit as needed
```

### Adding New Tests

Add new test functions in `scripts/tournament/cli.py`:

```python
def test_new_bot(verbose: bool = True) -> bool:
    """Test new bot functionality"""
    # Implementation
```

### Extending Tournament Format

Modify `run_tournament()` function in `scripts/tournament/cli.py` to support:
- Double elimination
- Swiss system
- Custom scoring

### Integration with CI/CD

Example GitHub Actions workflow:

```yaml
name: Test Bots
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
      - name: Test bots
        run: |
          python -m scripts.tournament.cli test bot002
          python -m scripts.tournament.cli test bot000_vs_bot003
```

## Best Practices

### Bot Development

1. **Test locally first**: Use the tournament system before submitting to Botzone
2. **Handle all edge cases**: Empty move list, board boundaries, etc.
3. **Optimize for time**: Stay within 2-second limit
4. **Follow protocol exactly**: Match Botzone requirements precisely

### Tournament Management

1. **Keep bots updated**: Recompile after changes
2. **Archive results**: Save match logs for analysis
3. **Monitor performance**: Track win rates and error rates
4. **Regular testing**: Run tests before major changes

### System Maintenance

1. **Update dependencies**: Keep Python and compiler versions current
2. **Backup configurations**: Save working bot versions
3. **Document changes**: Update this manual when system changes
4. **Monitor disk space**: Clean up old executables and logs

## Support and Resources

### Documentation

- This manual: `docs/manuals/tournament_system_manual.md`
- Botzone documentation: `wiki/` directory
- Bot implementation guides: `docs/bots/implementations/`

### Source Code

- Tournament system: `scripts/tournament/`
- Core game logic: `core/`
- Example bots: `bots/`

### Troubleshooting Resources

- Error logs: `logs/` directory
- Match results: `results/` directory
- Debug scripts: `scripts/debug_board.py`, `scripts/check_legal_moves.py`

### Getting Help

1. Review this manual and existing documentation
2. Check error logs for detailed information
3. Examine bot source code for protocol compliance
4. Use debug scripts to analyze specific issues

---

*Last updated: December 2025*  
*System version: Tournament System v2.0*  
*Compatible with: Botzone Amazons Protocol*