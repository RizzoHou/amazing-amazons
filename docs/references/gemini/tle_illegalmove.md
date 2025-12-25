The primary reason `bot002.cpp` fails (TLE and Illegal Movements) despite being theoretically faster is a **critical logic error in the input parsing/replay loop**.

The bot aggressively skips "even-indexed" lines during the history replay, assuming they are duplicates. In reality, these lines contain the **opponent's moves**. By skipping them, your bot effectively plays against a "ghost" opponent—it never updates the board with the enemy's pieces.

Here is the breakdown of the problem and the solution.

### The Root Cause: Board Desynchronization

In `bot002.cpp`, lines 610-612 contain this logic:

```cpp
// Only apply response lines (odd indices). Request lines (even indices) are duplicates.
if (i % 2 == 0)
    continue;

```

**Why this fails:**
When the platform sends the game history (e.g., at Turn 3), the input lines typically look like this:

1. `Line 0`: **Request** `-1` (Game Start)
2. `Line 1`: **Response** `x y ...` (Black's Move 1)
3. `Line 2`: **Request** `x y ...` (White's Move 1)
4. `Line 3`: **Response** `x y ...` (Black's Move 2)

Your bot skips indices 0, 2, 4, etc.

* It skips `Line 0` (Correct).
* **It skips `Line 2` (White's Move 1).**
* **It skips `Line 4` (White's Move 2).**

As a result, your bot's internal board only contains **its own queens**. It thinks the opponent's pieces are still at their starting positions (or nonexistent).

* **Illegal Moves:** The bot tries to move a queen to a square that is actually occupied by an invisible opponent piece or arrow.
* **TLE:** The search tree behaves erratically because the board state is "impossible" (e.g., valid moves are blocked by ghosts), leading to inefficient expansion or hangs in the MCTS logic when it tries to simulate games on a corrupted board.

### The Solution

You need to process **every** valid move line in the history, regardless of whether it is a "Request" or "Response". To make this robust, do not rely on a simple `current_color` toggle; instead, detect the color of the piece being moved directly from the coordinates.

#### **Step 1: Replace the Replay Loop in `main**`

Replace the entire replay loop (approx. lines 603-625 in `bot002.cpp`) with this robust version:

```cpp
    // --- FIXED REPLAY LOOP ---
    for (size_t i = 0; i < lines.size(); i++) {
        const string& line_str = lines[i];
        istringstream iss2(line_str);
        vector<int> coords;
        int v;
        while (iss2 >> v) coords.push_back(v);
        
        // Skip incomplete lines or the initial "-1" request
        if (coords.size() < 6 || coords[0] == -1)
            continue;
        
        // Convert coordinates to indices
        int src_idx = coord_to_idx(coords[0], coords[1]);
        int dest_idx = coord_to_idx(coords[2], coords[3]);
        int arrow_idx = coord_to_idx(coords[4], coords[5]);
        Move m(src_idx, dest_idx, arrow_idx);
        
        // AUTO-DETECT COLOR: Check which queen is at the source position
        int move_color = -1;
        uint64_t src_bit = 1ULL << src_idx;
        
        if (board.queens[BLACK] & src_bit) {
            move_color = BLACK;
        } else if (board.queens[WHITE] & src_bit) {
            move_color = WHITE;
        } else {
            // Error: No queen at source. The board state is likely desynced 
            // or the move is invalid. For now, we skip or log error.
            continue; 
        }

        // Apply the move
        apply_move(board, m, move_color);
    }
    // -------------------------

```

#### **Step 2: Verify `apply_move` Logic**

Your `apply_move` function in `bot002` is already correct, but ensure that `generate_moves` (which uses bitboards) is not causing the TLE by looping infinitely if the board is empty. With the fix above, the board will be populated correctly, and the branching factor will be manageable.

**Why `bot000.cpp` worked:**
`bot000.cpp` used `grid[move.x0][move.y0]` to identify the piece color dynamically and processed every line that wasn't `-1`. This made it immune to the parity issue that broke `bot002`.

### Summary of Performance

Once you apply this fix, `bot002.cpp` should significantly outperform `bot000.cpp`.

* **Bitboards** allow checking move validity and generating moves in CPU cycles rather than array iterations.
* **Memory Pool** (`std::deque` in your fix) reduces `new`/`delete` overhead.
* **MCTS** logic is standard and should work well within 0.7s given the speed of bitboards.