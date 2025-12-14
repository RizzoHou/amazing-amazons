# Solution Request: Illegal Movement Bug in bot002.cpp

**Date:** 2025-12-14  
**Severity:** Critical - Bot produces illegal moves on Botzone platform  
**Bot:** bot002.cpp (Optimized C++ implementation with bitboards)

---

## Problem Summary

bot002.cpp is generating illegal moves during Botzone gameplay, resulting in immediate disqualification. The bot attempts to move pieces that are not at the specified source position, causing an "INVALIDMOVE" error.

## Bug Evidence

From `logs/botzone_debug/illegal_movemnet2.log`:

**Final illegal move (Turn 7):**
- Player: 0 (BLACK)
- Attempted move: `7 0 6 0 4 0`
  - Source: (7, 0)
  - Destination: (6, 0)
  - Arrow: (4, 0)
- Result: `INVALIDMOVE` error
- Outcome: WHITE wins by disqualification

**Move History Analysis:**
```
Turn 1 (BLACK): 7 2 7 4 6 4  ✓ OK
Turn 2 (WHITE): 5 7 5 1 2 1  ✓ OK
Turn 3 (BLACK): 5 0 7 0 1 6  ✓ OK - BLACK moves piece FROM (5,0) TO (7,0)
Turn 4 (WHITE): 2 7 1 7 3 7  ✓ OK
Turn 5 (BLACK): 7 0 7 1 2 6  ✓ OK - BLACK moves piece FROM (7,0) TO (7,1)
Turn 6 (WHITE): 0 5 2 3 0 3  ✓ OK
Turn 7 (BLACK): 7 0 6 0 4 0  ❌ ILLEGAL - No piece at (7,0)!
```

**Root Cause:**
After Turn 5, the BLACK piece at (7,0) moved to (7,1). However, in Turn 7, the bot attempts to move from (7,0) again, indicating the internal board state is incorrect.

---

## Suspected Code Issue

**Location:** `bots/bot002.cpp`, lines 889-922 (move replay section in `main()`)

### Current Implementation (bot002.cpp):

```cpp
// Determine color
istringstream iss(lines[0]);
vector<int> first_req;
int val;
while (iss >> val) first_req.push_back(val);

if (first_req[0] == -1) {
    my_color = BLACK;
} else {
    my_color = WHITE;
}

// Replay moves - Game always starts with BLACK, then alternates
// lines[] contains the full history, starting from turn 1
int current_color = BLACK;  // First actual move is always BLACK

for (size_t i = 0; i < lines.size(); i++) {
    const string& line_str = lines[i];
    istringstream iss2(line_str);
    vector<int> coords;
    int v;
    while (iss2 >> v) coords.push_back(v);
    
    // Skip invalid moves (e.g., -1 -1 -1 -1 -1 -1)
    if (coords.size() < 6 || coords[0] == -1) {
        // Don't alternate color for skipped moves
        continue;
    }
    
    // Convert from (x,y) coordinates to bitboard indices
    int src_idx = coord_to_idx(coords[0], coords[1]);
    int dest_idx = coord_to_idx(coords[2], coords[3]);
    int arrow_idx = coord_to_idx(coords[4], coords[5]);
    Move m(src_idx, dest_idx, arrow_idx);
    
    // Apply move with current color
    apply_move(board, m, current_color);
    ai.advance_root(m);
    
    // Alternate color for next actual move
    current_color = 1 - current_color;
}
```

### Comparison with bot001.cpp (Working Version):

```cpp
// Determine color
istringstream iss(lines[0]);
vector<int> first_req;
int val;
while (iss >> val) first_req.push_back(val);

if (first_req[0] == -1) {
    my_color = BLACK;
} else {
    my_color = WHITE;
}

// Replay moves
for (const string& line_str : lines) {
    istringstream iss2(line_str);
    vector<int> coords;
    int v;
    while (iss2 >> v) coords.push_back(v);
    
    if (coords[0] == -1) continue;
    
    Move m(coords[0], coords[1], coords[2], coords[3], coords[4], coords[5]);
    board.apply_move(m);
    ai.advance_root(m);
}
```

---

## Key Differences

1. **Color Tracking:** bot002.cpp explicitly tracks `current_color` during replay, while bot001.cpp does not pass color to `apply_move()`
   
2. **Apply Move Function Signature:**
   - bot002.cpp: `apply_move(board, m, current_color)` - requires color parameter
   - bot001.cpp: `board.apply_move(m)` - color is implicit (retrieved from source position)

3. **Bitboard Representation:** bot002.cpp uses bitboard indices (`coord_to_idx()`), while bot001.cpp uses direct (x,y) coordinates

---

## Potential Root Causes

### Hypothesis 1: Color Tracking Logic Error
The color alternation logic may not be correctly synchronized with the actual game state. The comment says "Game always starts with BLACK" but:
- `lines[0]` might be the request (with -1s), not the first move
- The interpretation of who plays first might be incorrect based on `my_color` value

### Hypothesis 2: Apply Move Implementation Error
The `apply_move()` function in bot002.cpp may have a bug:

```cpp
inline void apply_move(Board& board, const Move& move, int color) {
    uint64_t src_bit = 1ULL << move.src;
    uint64_t dest_bit = 1ULL << move.dest;
    uint64_t arrow_bit = 1ULL << move.arrow;
    
    board.queens[color] ^= src_bit;   // Remove from source
    board.queens[color] |= dest_bit;  // Add to destination
    board.arrows |= arrow_bit;        // Place arrow
}
```

**Issue:** This assumes the piece at `move.src` belongs to `color`. If the wrong color is passed, it will:
- Remove the bit from the wrong color's bitboard (XOR with non-existent bit)
- Add the bit to the wrong color's bitboard
- Leave the actual piece in place, creating phantom pieces

### Hypothesis 3: Lines Array Interpretation
The `lines[]` array structure may not match expectations:
- Does `lines[0]` contain the initial request or the first actual move?
- Are requests (with -1s) interleaved with moves?
- Should certain lines be skipped?

---

## Expected Behavior

The replay logic should:
1. Correctly parse the move history from the `lines[]` array
2. Apply each historical move to the internal board state in the correct order
3. Track which player made each move accurately
4. Result in a board state that matches the actual game state
5. Generate only legal moves based on the accurate board state

---

## Debugging Information Needed

To diagnose this issue, we need to understand:

1. **Lines Array Content:** What exactly is in `lines[]`? 
   - Is `lines[0]` always the initial request with -1s?
   - Are both players' moves included, or only the opponent's moves?
   - How does the array structure differ between BLACK and WHITE perspective?

2. **Board State After Replay:** What is the actual bitboard state after the replay completes?
   - Which positions have BLACK queens?
   - Which positions have WHITE queens?
   - Are there any duplicate or missing pieces?

3. **Color Tracking:** During replay, which color should be assigned to each move?
   - Should color alternate with every line?
   - Should color be determined by the turn number and bot's color?

---

## Request for Solution

**Please provide:**

1. **Root Cause Analysis:** Identify the exact bug in the move replay logic
   
2. **Corrected Code:** A fixed version of the replay section (lines 889-922) that:
   - Correctly interprets the `lines[]` array structure
   - Applies moves to the correct player's pieces
   - Maintains accurate board state synchronization
   
3. **Explanation:** Clarify the intended structure and interpretation of:
   - The `lines[]` array from Botzone input
   - The relationship between line index, turn number, and player color
   - The correct way to track which player made each move

4. **Additional Safeguards:** Suggest any defensive programming measures, such as:
   - Validation that a piece exists at the source position before moving
   - Verification that the piece belongs to the expected player
   - Assertions or error checking during replay

---

## Additional Context

### Bitboard Coordinate System

```cpp
inline int coord_to_idx(int x, int y) {
    return x * 8 + y;
}
```

- Position (7, 0) → index 56
- Position (7, 1) → index 57
- Position (6, 0) → index 48

### Initial Board Configuration

```
BLACK queens (color=0):
- (0, 2) → index 2
- (2, 0) → index 16
- (5, 0) → index 40
- (7, 2) → index 58

WHITE queens (color=1):
- (0, 5) → index 5
- (2, 7) → index 23
- (5, 7) → index 47
- (7, 5) → index 61
```

### Botzone Long-Running Protocol

The bot uses Botzone's long-running mode:
1. First turn: Receives turn_id and move history
2. Outputs move and `>>>BOTZONE_REQUEST_KEEP_RUNNING<<<`
3. Subsequent turns: Receives opponent move, outputs own move
4. Internal state (board, MCTS tree) persists between turns

---

## References

- **Log File:** `logs/botzone_debug/illegal_movemnet2.log`
- **Bot Implementation:** `bots/bot002.cpp`
- **Working Reference:** `bots/bot001.cpp` (has simpler replay logic that works)
- **Game Rules:** `wiki/Amazons - Botzone Wiki.pdf`

---

## Thank You

This bug is preventing bot002.cpp from competing on Botzone. Any insights or solutions would be greatly appreciated!
