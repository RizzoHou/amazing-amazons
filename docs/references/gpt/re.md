Your crash is almost certainly **memory**, not time.

Evidence in the log:

- `signaled by sig = 9` → the process was **SIGKILL**’d (the sandbox/OS kills it; your code didn’t “throw”).
- `"memory": 512` right before the kill → you hit the memory ceiling (Botzone commonly kills at the limit).
- It happens “near the end” → consistent with **accumulating allocations**.

You introduced two big memory blow-ups:

1) **You intentionally leak the whole MCTS tree every turn** in `advance_root()` (by design).
2) You changed `get_legal_moves()` to `reserve(4096)` and every expanded node stores a `vector<Move> untried_moves`.  
   That means each expanded node can allocate up to ~4096 `Move`s capacity even if it only needs a fraction. With thousands of nodes, memory explodes.

### What to do

## Fix 1: Remove `reserve(4096)` (this alone can save you)
Do **not** reserve 4096 for every legal-move generation. That reserve happens for *every expansion node*, not just root.

Change:

```cpp
moves.reserve(4096);
```

to something modest like:

```cpp
moves.reserve(256);   // or 512
```

Or even remove reserve entirely (slower but safer).

Why: 4096 × sizeof(Move) is huge per node, and you create many nodes.

---

## Fix 2: Stop leaking trees, but avoid deletion spikes with incremental GC
You were right to avoid “delete root” spikes, but leaking forever guarantees OOM. The correct approach is:

- **Detach and keep the subtree you need** (new root)
- **Queue the discarded subtrees for deletion**
- **Delete a small number of nodes per turn** (amortized), under your deadline checks

### Step 2A: Make node destruction non-recursive
Your current destructor recursively deletes children. That makes deletion spiky again.

Change `MCTSNode` to **not** delete children in its destructor:

```cpp
class MCTSNode {
public:
    MCTSNode* parent;
    Move move;
    vector<MCTSNode*> children;
    double wins;
    int visits;
    vector<Move> untried_moves;
    int player_just_moved;

    MCTSNode(MCTSNode* p=nullptr, Move m=Move(), int pjm=0)
        : parent(p), move(m), wins(0.0), visits(0), player_just_moved(pjm) {}

    ~MCTSNode() = default; // IMPORTANT: no recursive delete
};
```

### Step 2B: Add a garbage stack and an incremental deleter
Add to `class MCTS`:

```cpp
vector<MCTSNode*> gc_stack;

void gc_collect_some(function<bool()> time_up, int max_nodes = 2000) {
    int freed = 0;
    while (freed < max_nodes && !gc_stack.empty() && !time_up()) {
        MCTSNode* n = gc_stack.back();
        gc_stack.pop_back();

        // schedule children for deletion
        for (MCTSNode* c : n->children) gc_stack.push_back(c);

        delete n;
        freed++;
    }
}
```

### Step 2C: In `advance_root`, detach and enqueue old stuff (no leaks)
Replace your current leak-based `advance_root` with this pattern:

```cpp
void advance_root(const Move& move) {
    if (!root) return;

    MCTSNode* new_root = nullptr;
    for (MCTSNode* child : root->children) {
        if (child->move == move) { new_root = child; break; }
    }

    if (new_root) {
        // Detach new_root from root->children using swap+pop (O(1))
        auto& ch = root->children;
        for (size_t i = 0; i < ch.size(); i++) {
            if (ch[i] == new_root) {
                ch[i] = ch.back();
                ch.pop_back();
                break;
            }
        }

        // Old root now contains only "discarded" siblings; enqueue old root
        gc_stack.push_back(root);

        // Re-root
        root = new_root;
        root->parent = nullptr;
    } else {
        // Opponent played a move not in our tree; discard whole tree
        gc_stack.push_back(root);
        root = nullptr;
    }
}
```

### Step 2D: Actually run GC each turn under your deadline
At the **start of `search()`**, after you define `time_up`, do:

```cpp
gc_collect_some(time_up, 4000); // tune 1000~10000 depending on speed
```

Also call it again right before returning if you want:

```cpp
gc_collect_some(time_up, 4000);
```

This keeps memory bounded without unpredictable spikes.

---

## Fix 3: Reduce per-node memory further (high impact)
Even with GC, MCTS trees can be big. Two good knobs:

### 3A) Shrink `Move`
Right now `Move` is 6×`int` = typically 24 bytes. On an 8×8 board, coords fit in 0..7 (and -1 sentinel). Use `int8_t`:

```cpp
#include <cstdint>
struct Move {
    int8_t x0,y0,x1,y1,x2,y2;
    ...
};
```

When printing, cast to int:

```cpp
cout << int(best_move.x0) << " " << int(best_move.y0) << ...
```

This reduces `untried_moves` memory a lot.

### 3B) Don’t keep gigantic move lists at deep nodes
Simple cap (trades some strength for stability). After generating moves:

```cpp
new_node->untried_moves = state.get_legal_moves(current_player);
auto& um = new_node->untried_moves;
const int CAP = 128; // or 64/256
if ((int)um.size() > CAP) {
    // random partial shuffle then truncate
    for (int i = 0; i < CAP; i++) {
        int j = i + (int)(rng() % (um.size() - i));
        swap(um[i], um[j]);
    }
    um.resize(CAP);
}
```

This prevents worst-case nodes from hoarding thousands of moves.

---

## Fix 4: Small correctness/efficiency note about `fast_copy`
`fast_copy()` still clears the board in the constructor loop, so it’s not actually the fastest. You can just do:

```cpp
Board state = root_state; // uses implicit copy constructor, no init_board()
```

Not related to the crash, but it’s cleaner.

---

### Summary of what caused the collapse
- **Leak in `advance_root()`** + **4096 reserve in every generated move vector** ⇒ memory hits the 512MB ceiling ⇒ Botzone SIGKILL (9) ⇒ RE.

Apply Fix 1 + Fix 2 and the crash should disappear. Fix 3 makes it much harder to hit memory again.