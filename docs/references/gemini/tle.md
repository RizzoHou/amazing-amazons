Here are detailed, step-by-step instructions for your AI agent to optimize the C++ bot.

The core issue is that **Game of the Amazons** has a massive branching factor. A single MCTS iteration (generating moves, running BFS, evaluating) can take **50ms to 150ms**. If your code checks the time at `0.87s`, starts a new iteration, and that iteration takes `0.15s`, the bot finishes at `1.02s` and gets killed by the server.

Pass these instructions to your agent to fix the algorithmic inefficiencies and safety margins.

***

### Instruction Set: MCTS Optimization for Game of the Amazons

**Objective:** Eliminate Time Limit Exceeded (TLE) errors by reducing memory allocation overhead, optimizing vector operations from $O(N)$ to $O(1)$, and increasing safety buffers.

#### Step 1: Optimize Move Removal in `MCTS::search` (Critical)
**Context:** Currently, `node->untried_moves.erase(...)` is used. This shifts every element in the vector, which is an $O(N)$ operation. With hundreds of moves, this is too slow inside the simulation loop.
**Action:** Replace `erase` with the "Swap and Pop" idiom ($O(1)$).

*   **Locate:** The `Expansion` block inside `MCTS::search`.
*   **Change:**
    ```cpp
    // OLD CODE:
    node->untried_moves.erase(node->untried_moves.begin() + idx);

    // NEW CODE:
    node->untried_moves[idx] = node->untried_moves.back();
    node->untried_moves.pop_back();
    ```

#### Step 2: Prevent Heap Allocations in `evaluate_optimized`
**Context:** The function `evaluate_optimized` creates `vector<pair<int, int>> my_pieces` and `opp_pieces` in every single simulation. This triggers thousands of memory allocations per second.
**Action:** Make these vectors `static` to reuse the memory capacity across iterations.

*   **Locate:** The beginning of `evaluate_optimized`.
*   **Change:**
    ```cpp
    // OLD CODE:
    vector<pair<int, int>> my_pieces;
    vector<pair<int, int>> opp_pieces;
    my_pieces.reserve(4);
    opp_pieces.reserve(4);

    // NEW CODE:
    static vector<pair<int, int>> my_pieces;
    static vector<pair<int, int>> opp_pieces;
    my_pieces.clear();
    opp_pieces.clear();
    // (Note: No reserve needed after first run, capacity stays high enough)
    ```

#### Step 3: Pre-allocate Move Vector
**Context:** `get_legal_moves` pushes items to a vector, causing it to resize/reallocate multiple times as it grows.
**Action:** Reserve memory immediately.

*   **Locate:** `Board::get_legal_moves`.
*   **Change:**
    ```cpp
    vector<Move> get_legal_moves(int color) const {
        vector<Move> moves;
        moves.reserve(128); // Add this line. 128 is a safe average estimate.
        // ... rest of logic
    ```

#### Step 4: Adjust Time Safety Margins
**Context:** The current buffer of `0.12s` (`1.0 - 0.88`) is too tight. A complex board state calculation can overrun this buffer.
**Action:** Increase the buffer to roughly 250ms.

*   **Locate:** The constants at the bottom of the file.
*   **Change:**
    ```cpp
    // OLD CODE:
    const double TIME_LIMIT = 0.88;
    const double FIRST_TURN_TIME_LIMIT = 1.88;

    // NEW CODE:
    const double TIME_LIMIT = 0.72;      // Larger safety buffer
    const double FIRST_TURN_TIME_LIMIT = 1.72;
    ```

#### Step 5: (Optional) Faster Distance Reset
**Context:** In `perform_fast_bfs`, the loop to reset `dist_out` runs $8 \times 8 = 64$ times.
**Action:** Use `memset` (from `<cstring>`) which is heavily optimized by the compiler.

*   **Locate:** The start of `perform_fast_bfs`.
*   **Change:**
    ```cpp
    // OLD CODE:
    for (int i = 0; i < GRID_SIZE; i++) { ... manually setting 99 ... }

    // NEW CODE:
    // 99 is a safe byte value (doesn't overflow char), so we can use memset
    // However, since 99 isn't 0 or -1, standard loop is okay, 
    // but ensure <cstring> is included if using memset.
    // Given the unrolling you already did, you can leave this alone 
    // IF you did the previous 4 steps. 
    // If you want to use memset: 
    // memset(dist_out, 99, sizeof(int) * GRID_SIZE * GRID_SIZE);
    ```
    *(Note: The first 4 steps are sufficient to fix the TLE. Only do Step 5 if you are comfortable with raw memory operations).*