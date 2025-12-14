# Solution Request: Runtime Error (Segmentation Fault) in bot002.cpp

**Date:** 2025-12-14  
**Severity:** Critical - Bot crashes with SIGSEGV during gameplay  
**Bot:** bot002.cpp (Optimized C++ implementation with bitboards and MCTS)

---

## Problem Summary

bot002.cpp encounters a Runtime Error (signal 11 - SIGSEGV) during Botzone gameplay, causing immediate termination and disqualification. The bot successfully completes 6 turns before crashing on Turn 7 during decision-making. The crash appears to be a segmentation fault, likely caused by accessing invalid memory.

## Bug Evidence

From `logs/botzone_debug/re.json`:

### Crash Details
- **Signal:** 11 (SIGSEGV - Segmentation Fault)
- **Verdict:** RE (Runtime Error)
- **Turn:** 7 (Player 0 - BLACK)
- **Runtime at crash:** 229ms
- **Memory limit:** 256MB
- **Working directory:** /var/sandbox/box0/

### Game State at Crash
- BLACK piece count: 330
- WHITE piece count: 457
- Previous 6 moves completed successfully
- Bot was using keep_running mode successfully

### Move History Before Crash

**Turn 1 (Player 0 - BLACK):**
- Move: `5 0 5 6 2 6` ✓ OK
- Time: 929ms

**Turn 2 (Player 1 - WHITE):**
- Move: `0 5 3 2 2 3` ✓ OK
- Time: 5901ms

**Turn 3 (Player 0 - BLACK):**
- Move: `0 2 2 4 6 4` ✓ OK
- Time: 324ms

**Turn 4 (Player 1 - WHITE):**
- Move: `3 2 0 2 6 2` ✓ OK
- Time: 3806ms

**Turn 5 (Player 0 - BLACK):**
- Move: `2 0 1 1 1 2` ✓ OK
- Time: 409ms

**Turn 6 (Player 1 - WHITE):**
- Move: `7 5 6 5 2 1` ✓ OK
- Time: 3802ms

**Turn 7 (Player 0 - BLACK):**
- **CRASH** - Runtime Error (signal 11)
- Partial output shows 6 moves sent before crash

### Debug Output from Crash

```
botzone inception log:
1 line read from stdin
1 line read from stdin
...
1 line read from child
1 line read from child
...
signaled by sig = 11
verdict = RE
-- RE occurred --
working dir = /var/sandbox/box0/
```

### Bot Output Before Crash

```
stderr:
start to close fds...

stdout:
5 0 5 6 2 6
>>>BOTZONE_REQUEST_KEEP_RUNNING<<<
0 2 2 4 6 4
>>>BOTZONE_REQUEST_KEEP_RUNNING<<<
2 0 1 1 1 2
>>>BOTZONE_REQUEST_KEEP_RUNNING<<<
7 2 6 1 1 6
>>>BOTZONE_REQUEST_KEEP_RUNNING<<<
2 4 1 4 3 6
>>>BOTZONE_REQUEST_KEEP_RUNNING<<<
6 1 5 2 5 1
>>>BOTZONE_REQUEST_KEEP_RUNNING<<<
```

---

## Suspected Code Issues

### High Priority Suspects

#### 1. NodePool Memory Allocator (lines 638-668)

```cpp
class NodePool {
    vector<char> memory;
    size_t offset;
    
public:
    NodePool() : offset(0) {
        memory.reserve(10000000);  // Reserve 10MB
    }
    
    void* allocate(size_t size) {
        if (offset + size > memory.size()) {
            size_t new_size = max(memory.size() * 2, offset + size);
            memory.resize(new_size);  // ⚠️ DANGEROUS: Resizing invalidates pointers!
        }
        void* ptr = &memory[offset];
        offset += size;
        return ptr;
    }
    
    void reset() {
        offset = 0;
    }
};
```

**Issue:** When `memory.resize()` is called, it may reallocate the underlying buffer, invalidating ALL previously returned pointers. Any existing `MCTSNode*` pointers in the tree become dangling pointers.

**Scenario:**
1. Turn 1-6: Pool grows, tree is built
2. Turn 7: Pool needs more space, calls `resize()`
3. Vector reallocates to new address
4. All `parent` and `children` pointers in existing nodes become invalid
5. Next access to `node->parent` or `node->children[i]` → SIGSEGV

#### 2. Tree Traversal in advance_root (lines 816-841)

```cpp
void advance_root(const Move& move) {
    if (root == nullptr) return;
    
    MCTSNode* new_root = nullptr;
    
    // Defensive: Check children vector is valid
    if (!root->children.empty()) {
        for (size_t i = 0; i < root->children.size(); i++) {
            // Defensive: Null check each child
            if (root->children[i] != nullptr && root->children[i]->move == move) {
                new_root = root->children[i];
                break;
            }
        }
    }
    
    if (new_root != nullptr) {
        new_root->parent = nullptr;
        root = new_root;
        // Keep old tree in pool (can't reset without destroying kept subtree)
    } else {
        root = nullptr;
        // Start fresh if move not found
        pool.reset();
    }
}
```

**Issues:**
- Setting `new_root->parent = nullptr` might access freed memory if pool was corrupted
- Accessing `root->children` when root might be in invalidated memory
- Comment says "can't reset without destroying kept subtree" but doesn't free old nodes

#### 3. UCT Selection (lines 693-710)

```cpp
MCTSNode* uct_select_child(double C) {
    double log_visits = log(static_cast<double>(visits));
    double best_score = -1e9;
    MCTSNode* best_child = nullptr;
    
    for (size_t i = 0; i < children.size(); i++) {
        MCTSNode* c = children[i];  // ⚠️ Potential dangling pointer
        double exploit = c->wins / c->visits;  // ⚠️ Access through potentially invalid pointer
        double explore = C * sqrt(log_visits / c->visits);
        double score = exploit + explore;
        if (score > best_score) {
            best_score = score;
            best_child = c;
        }
    }
    return best_child;
}
```

**Issue:** If pool was resized, `children[i]` points to invalid memory.

#### 4. MCTS Search Loop (lines 720-805)

The main search loop performs:
- Node selection (traverses tree using potentially invalid pointers)
- Expansion (allocates new nodes, potentially triggering resize)
- Backpropagation (traverses parent pointers)

**Potential crash points:**
```cpp
// Selection
while (node->untried_moves.empty() && !node->children.empty()) {
    node = node->uct_select_child(C);  // ⚠️ May return invalid pointer
    apply_move(state, node->move, node->player_just_moved);  // ⚠️ Access invalid node
    current_player = 1 - current_player;
}

// Backpropagation
while (node != nullptr) {
    node->visits++;  // ⚠️ Writing to invalid memory
    if (node->player_just_moved == root_player) {
        node->wins += win_prob;
    } else {
        node->wins += (1.0 - win_prob);
    }
    node = node->parent;  // ⚠️ Following invalid pointer
}
```

### Medium Priority Suspects

#### 5. BFS Evaluation with Static Arrays (lines 460-521)

```cpp
void bfs_evaluate(const Board& board, int color, double& queen_terr, double& king_terr,
                  double& queen_pos, double& king_pos) {
    static char dist[64];
    static int queue[64];
    
    memset(dist, -1, 64);
    int head = 0, tail = 0;
    
    // ... BFS logic
}
```

**Issue:** Static arrays shared across recursive calls. If BFS is called recursively or from multiple evaluation paths, data corruption could occur.

#### 6. Move Replay Logic (lines 889-930)

The replay logic now has filtering for request/response lines:

```cpp
// Only apply response lines (odd indices). Request lines (even indices) are duplicates.
if (i % 2 == 0)
    continue;
```

**Issue:** This assumes a specific line pattern that might not match re.json structure. Misapplied moves could corrupt board state, leading to invalid MCTS tree structure.

---

## Analysis of re.json Structure

The log shows alternating patterns:
1. **Request** (from judge): `{"keep_running": false, "output": {...}}`
2. **Response** (from player): `{"0": {...}}` or `{"1": {...}}`

For Player 0's perspective:
- Turn 1: Request → Player 0 response
- Turn 2: Request → Player 1 response
- Turn 3: Request → Player 0 response
- ...
- Turn 7: Request → **Player 0 crashes during response**

**Question:** Does the bot receive the request data or just the opponent's moves?

---

## Root Cause Hypothesis

### Primary Hypothesis: NodePool Vector Reallocation

The most likely cause is:

1. **Turns 1-6:** Bot builds MCTS tree successfully, NodePool grows to ~600KB
2. **Turn 7:** MCTS search needs more nodes, triggers condition `offset + size > memory.size()`
3. **Vector resize:** `memory.resize()` reallocates to new buffer (2x size)
4. **Invalidation:** All previously allocated `MCTSNode*` become dangling pointers
5. **Crash:** Next access to `root->children[i]` or `node->parent` → SIGSEGV

**Why it happens on Turn 7:**
- Early turns have simpler game states (more open board)
- As game progresses, branching factor changes
- Turn 7 might be first time pool needs to grow beyond initial reserve
- Could also be cumulative: tree kept across turns eventually exceeds capacity

### Secondary Hypothesis: Memory Corruption in advance_root

When `advance_root()` keeps a subtree but doesn't reset the pool:
- Old nodes remain in pool memory
- New allocations might overlap with old tree data
- Accessing old tree through kept `new_root` reads corrupted data

---

## Request for Solution

**Please provide:**

### 1. Root Cause Identification
- Is the NodePool vector reallocation the primary issue?
- Are there other memory safety problems?
- Is the static array in `bfs_evaluate()` causing issues?

### 2. Fix for NodePool
How should the pool allocator be redesigned to prevent pointer invalidation?

**Option A: Pre-allocate sufficient memory**
```cpp
NodePool() : offset(0) {
    memory.resize(50000000);  // Allocate 50MB upfront, never resize
}
```

**Option B: Use stable allocations**
```cpp
// Use vector of chunks instead of single vector
vector<unique_ptr<char[]>> chunks;
// Or use std::deque which guarantees pointer stability
```

**Option C: Reset pool after each turn**
```cpp
// Don't keep tree between turns
// Rebuild from scratch each time (simpler but slower)
```

### 3. Fix for advance_root
How should tree reuse be handled safely?
- Should we abandon tree reuse entirely?
- Is there a safe way to keep subtrees while resetting the pool?
- Should we use reference counting or smart pointers?

### 4. Additional Safeguards

**Memory safety checks:**
```cpp
#ifdef DEBUG
// Verify pointers are within pool bounds
bool is_valid_pointer(void* ptr) {
    return ptr >= &memory[0] && ptr < &memory[offset];
}
#endif
```

**Crash diagnostics:**
```cpp
// Add logging before potential crash points
cerr << "Accessing node at " << node << endl;
cerr << "Children size: " << node->children.size() << endl;
```

### 5. Performance Implications
- What's the performance impact of different fixes?
- Can we maintain tree reuse without memory issues?
- Is it better to trade off tree persistence for stability?

---

## Additional Context

### System Constraints
- **Time limits:** 2s first turn, 1s subsequent turns (using 1.6s / 0.8s conservatively)
- **Memory limit:** 256MB
- **Platform:** Botzone sandbox (Linux, x86_64)

### Bot Architecture
- **Board representation:** Bitboards (uint64_t)
- **Search:** Monte Carlo Tree Search with UCB1
- **Evaluation:** Multi-component heuristic (5 features)
- **Optimizations:** 
  - Custom pool allocator (problematic)
  - Move ordering by centrality
  - Fast BFS with static arrays
  - Xorshift64 PRNG

### Performance Requirements
The bot needs to:
- Complete 50-100% more MCTS iterations than bot001.py
- Run stably for full games (50+ turns)
- Maintain tree between turns for speed

### Known Working Reference
bot001.py (Python version) doesn't crash but is slower. Key differences:
- Python handles memory automatically
- No custom allocator
- Doesn't reuse tree between turns
- Simpler but more reliable

---

## Complete re.json Log

```json
[see attached re.json file]
```

*(Full log provided in separate file)*

---

## Code Sections for Reference

### NodePool Implementation
See lines 638-668 in bot002.cpp

### MCTSNode Structure  
See lines 670-710 in bot002.cpp

### MCTS::search() Method
See lines 720-805 in bot002.cpp

### MCTS::advance_root() Method
See lines 816-841 in bot002.cpp

### BFS Evaluation
See lines 460-521 in bot002.cpp

---

## Debugging Questions

To help diagnose the issue, please clarify:

1. **NodePool behavior:**
   - Is vector reallocation the root cause?
   - How can we ensure pointer stability?
   - What's the safest allocation strategy?

2. **Tree reuse:**
   - Is it safe to keep subtrees across turns?
   - Should we reset the pool after each search?
   - How to handle `advance_root()` safely?

3. **Memory usage:**
   - How much memory does the tree typically need?
   - What's a safe pre-allocation size?
   - Should we monitor pool growth?

4. **Alternative approaches:**
   - Should we use `std::deque<MCTSNode>` instead?
   - Should we use `new`/`delete` with custom memory manager?
   - Should we abandon tree reuse for stability?

---

## Expected Solution Characteristics

An ideal solution would:
1. **Eliminate segmentation faults** - No pointer invalidation
2. **Maintain performance** - Still faster than Python version
3. **Be simple and maintainable** - Easy to understand and debug
4. **Work reliably** - Stable for 50+ turn games
5. **Use memory efficiently** - Stay within 256MB limit

**Trade-offs acceptable:**
- Slightly slower MCTS if it means stability
- No tree reuse if necessary for safety
- More memory usage if it prevents crashes

---

## References

- **Log File:** `logs/botzone_debug/re.json`
- **Bot Implementation:** `bots/bot002.cpp`
- **Working Reference:** `bots/bot001.py` (slower but stable)
- **Platform:** Botzone (https://botzone.org.cn)

---

## Thank You

This Runtime Error is preventing bot002.cpp from competing on Botzone. The bot shows good performance (fast MCTS iterations) but crashes unpredictably. Any insights on fixing the memory management issues would be greatly appreciated!

**Priority:** Critical - Need stable bot for tournament play.
