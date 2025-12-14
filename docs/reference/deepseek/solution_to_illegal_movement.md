The illegal move stems from two bugs in `bot002.cpp`:

1. **Wrong player color in MCTS selection** – In `MCTS::search`, the selection step applied a node’s move using `1 - node->player_just_moved` instead of `node->player_just_moved`. This corrupted the simulation state, leading to an MCTS tree that did not match the real board. When reusing the tree via `advance_root`, the root node’s move list included moves from squares that no longer contained a queen, causing an illegal move.

2. **Replay of duplicate request lines** – The initial replay loop applied every line that was not `-1`, including both response moves and the following request lines (which repeat the same move). For a White player, this would apply the same move twice with alternating colors, corrupting the board because `apply_move` uses a color‑sensitive XOR. Although the observed crash came from Black, this bug would break White games as well.

### 🔧 Fixed Code Sections

#### 1. Correct the MCTS selection (in `MCTS::search`)
Change the `apply_move` argument from `1 - node->player_just_moved` to `node->player_just_moved`:

```cpp
// before
apply_move(state, node->move, 1 - node->player_just_moved);

// after
apply_move(state, node->move, node->player_just_moved);
```

#### 2. Replay only actual moves (response lines)
Replace the replay loop (lines ~889‑922) with the following logic that applies only lines at odd indices (the responses) and skips request lines:

```cpp
int current_color = BLACK;  // first move is always by Black

for (size_t i = 0; i < lines.size(); i++) {
    const string& line_str = lines[i];
    istringstream iss2(line_str);
    vector<int> coords;
    int v;
    while (iss2 >> v) coords.push_back(v);

    // Skip incomplete lines or the initial "-1" request
    if (coords.size() < 6 || coords[0] == -1)
        continue;

    // Only apply response lines (odd indices). Request lines (even indices) are duplicates.
    if (i % 2 == 0)
        continue;

    int src_idx = coord_to_idx(coords[0], coords[1]);
    int dest_idx = coord_to_idx(coords[2], coords[3]);
    int arrow_idx = coord_to_idx(coords[4], coords[5]);
    Move m(src_idx, dest_idx, arrow_idx);

    apply_move(board, m, current_color);
    ai.advance_root(m);

    current_color = 1 - current_color;
}
```

### 📖 Explanation of the Input Format

Botzone sends a turn ID followed by `2 * turn_id - 1` lines of history. These lines alternate between **requests** and **responses**, starting with a request.  
- Request lines: either `-1 -1 -1 -1 -1 -1` (first turn) or the opponent’s move.  
- Response lines: the move executed by the player who just acted.

To reconstruct the board, only the response lines (odd indices) should be applied. Skipping the duplicate request lines prevents double application and ensures the correct color is used each time (`current_color` toggles only after a real move).

### ✅ Additional Safeguards (Optional)

For debugging, you could add an assertion in `apply_move` to verify that the source square actually contains a queen of the given color:

```cpp
assert((board.queens[color] & src_bit) != 0);
```

This would catch similar logic errors early. In the final optimized version it can be removed.

With these corrections, the board state remains accurate throughout the game, and the MCTS tree stays consistent, eliminating illegal moves.