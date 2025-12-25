# Bot002 Illegal Movement Bug Fix

**Date:** 2025-12-14  
**Status:** ✅ Fixed and Committed  
**Commit:** a6ea4d3

---

## Problem Summary

bot002.cpp was generating illegal moves on Botzone, specifically attempting to move pieces from positions where no queen existed. This caused immediate disqualification with "INVALIDMOVE" error.

**Example from logs/botzone_debug/illegal_movemnet2.log:**
- Turn 5: BLACK moves from (7,0) to (7,1) ✓
- Turn 7: BLACK illegally tries to move from (7,0) again ❌

---

## Root Causes Identified

### Bug 1: Wrong Player Color in MCTS Selection Phase

**Location:** `MCTS::search()` method, Selection phase

**Problem:**
```cpp
// WRONG - inverted player
apply_move(state, node->move, 1 - node->player_just_moved);
```

**Impact:** Corrupted simulation state by applying moves to wrong player's bitboard. This caused MCTS tree to diverge from actual board state, generating illegal moves when tree was reused via `advance_root()`.

**Fix:**
```cpp
// CORRECT - use actual player
apply_move(state, node->move, node->player_just_moved);
```

### Bug 2: Duplicate Move Application in Replay Loop

**Location:** Initial move replay loop (main function, lines ~889-922)

**Problem:** 
Botzone sends alternating request/response lines:
- Line 0 (even): Request (either `-1 -1 -1 -1 -1 -1` or previous move)
- Line 1 (odd): Response (actual move)
- Line 2 (even): Request (duplicate of line 1)
- Line 3 (odd): Response (next actual move)
- etc.

The old code applied ALL non-`-1` lines, causing each move to be applied twice with alternating colors. Since `apply_move` uses XOR operations on color-specific bitboards, double-application corrupts the board state.

**Fix:**
```cpp
// Only apply response lines (odd indices)
if (i % 2 == 0)
    continue;
```

---

## Changes Made

### 1. Fixed MCTS Selection Phase
**File:** `bots/bot002.cpp` line ~559

```cpp
// Selection
while (node->untried_moves.empty() && !node->children.empty()) {
    node = node->uct_select_child(C);
    apply_move(state, node->move, node->player_just_moved);  // FIXED
    current_player = 1 - current_player;
}
```

### 2. Fixed Replay Loop
**File:** `bots/bot002.cpp` lines ~881-910

```cpp
// Replay moves - Only process response lines (odd indices)
// Botzone sends alternating request/response lines, where responses are the actual moves
int current_color = BLACK;  // First move is always by Black

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
    if (i % 2 == 0)  // NEW: Skip even-indexed lines
        continue;
    
    // Convert and apply move...
    int src_idx = coord_to_idx(coords[0], coords[1]);
    int dest_idx = coord_to_idx(coords[2], coords[3]);
    int arrow_idx = coord_to_idx(coords[4], coords[5]);
    Move m(src_idx, dest_idx, arrow_idx);
    
    apply_move(board, m, current_color);
    ai.advance_root(m);
    
    current_color = 1 - current_color;
}
```

### 3. Added Defensive Assertion
**File:** `bots/bot002.cpp` line ~218

```cpp
// Apply a move to the board
inline void apply_move(Board& board, const Move& move, int color) {
    uint64_t src_bit = 1ULL << move.src;
    uint64_t dest_bit = 1ULL << move.dest;
    uint64_t arrow_bit = 1ULL << move.arrow;
    
    // Defensive: Verify source square contains a queen of the given color
    #ifdef DEBUG
    if ((board.queens[color] & src_bit) == 0) {
        cerr << "ERROR: No queen at source position for color " << color << endl;
        cerr << "Move: src=" << move.src << " dest=" << move.dest << " arrow=" << move.arrow << endl;
    }
    #endif
    
    board.queens[color] ^= src_bit;   // Remove from source
    board.queens[color] |= dest_bit;  // Add to destination
    board.arrows |= arrow_bit;        // Place arrow
}
```

### 4. Updated Development Rules
**File:** `.clinerules/development_workflow.md`

Added rule:
```markdown
- **Testing & Tournaments**: Run bot games sequentially, not in parallel, due to memory 
  constraints on MacBook. Each bot instance can consume significant memory during MCTS simulations.
```

---

## Verification

### Compilation
```bash
g++ -std=c++11 -O2 -o bots/bot002 bots/bot002.cpp
```
✅ **Success** - Compiles with only minor warnings about `std::forward`

### Expected Behavior After Fix

1. **Correct Board State:** Replay loop maintains accurate board state by only applying actual moves once
2. **Valid MCTS Simulations:** Selection phase applies moves to correct player, keeping tree consistent
3. **No Illegal Moves:** Bot will only generate moves from squares where its queens actually exist

---

## Technical Details

### Bitboard XOR Behavior
The `apply_move` function uses XOR to remove pieces:
```cpp
board.queens[color] ^= src_bit;  // Toggle bit off
```

If called twice on the same square with the same color:
1. First call: Bit is ON → XOR toggles it OFF ✓
2. Second call: Bit is OFF → XOR toggles it ON ❌ (creates phantom piece!)

If called with wrong color:
- Toggles bit in wrong bitboard, leaving actual piece untouched
- Creates corrupt state with pieces in multiple bitboards

### Botzone Input Format
For turn N, Botzone sends `2*N - 1` lines:
```
Turn 1: Line 0 = Request(-1), Line 1 = Response(Move1)
Turn 2: Line 0 = Request(-1), Line 1 = Response(Move1), Line 2 = Request(Move1), Line 3 = Response(Move2)
Turn 3: [5 lines total]
```

Only odd-indexed lines are new information (actual moves).

---

## Next Steps

1. ✅ Code fixes implemented
2. ✅ Changes committed to git
3. ⏳ Deploy to Botzone for real-world testing
4. ⏳ Monitor game logs for any remaining issues
5. ⏳ Run tournament vs bot001.cpp to verify strategic strength maintained

---

## References

- **Bug Report Log:** `logs/botzone_debug/illegal_movemnet2.log`
- **Solution Analysis:** `docs/references/deepseek/solution_to_illegal_movement.md`
- **Solution Request:** `docs/requests/illegal_movement_bug_solution_request.md`
- **Bot Implementation:** `bots/bot002.cpp`
- **Git Commit:** a6ea4d3