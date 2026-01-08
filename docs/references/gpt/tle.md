Below are concrete, “hand this to an engineer” instructions that fix the two real causes of overruns in your code:

1) **your time check only happens before an iteration, so one iteration can run past the deadline**, and  
2) you have **large, variable-time work outside the timed MCTS loop** (especially tree deletion in `advance_root`, plus an expensive `Board::copy()`).

I’m going to give you a prioritized patch plan with code-level changes.

---

## 0) What’s actually making you exceed time

### A. “One last iteration” overshoot
You check time only at the top of the loop; if there’s 1 ms left you still start an iteration that might take 30–200 ms (expansion that calls `get_legal_moves`, large vectors, etc.). That’s why it’s *intermittent*.

### B. Big work outside your MCTS timer
Two big offenders:

1) **First search: root move generation is not timed**
```cpp
if (root == nullptr) {
    root->untried_moves = root_state.get_legal_moves(root_player); // untimed currently
}
start_time = now(); // happens after
```

2) **`advance_root()` can delete a huge tree** (recursive `delete root;`)
If opponent move isn’t in your explored children (common), you delete the entire tree; if it *is* in the children you still delete all siblings. This is a huge time spike and it’s outside your iteration time checks.

### C. Your `Board::copy()` is slow and happens every iteration
Your `copy()` does:
- `Board new_board;` (constructor clears grid and calls `init_board()`)
- then overwrites grid

That’s wasted work **every single iteration**.

---

## 1) Add a hard deadline with a safety margin (stop starting work you can’t finish)

### Patch: use `time_point deadline`, not elapsed doubles
In `MCTS::search`, do this at the very top:

```cpp
Move search(const Board& root_state, int root_player) {
    using clock = chrono::steady_clock;

    // Safety margin to avoid “one last iteration” overruns
    const double SAFETY = 0.06; // 60ms (tune: 40–100ms)
    const double budget = max(0.0, time_limit - SAFETY);

    const auto start = clock::now();
    const auto deadline = start + chrono::duration_cast<clock::duration>(
        chrono::duration<double>(budget)
    );

    auto time_up = [&]() -> bool {
        return clock::now() >= deadline;
    };

    ...
}
```

### Patch: check time **before** expensive steps, not just per-iteration
Add `if (time_up()) break;` in these places:

- before entering selection loop
- inside selection loop (because tree can be wide)
- before expansion
- *right before* calling `get_legal_moves`
- right before evaluation (BFS + mobility)

Example layout:

```cpp
while (!time_up()) {
    MCTSNode* node = root;
    Board state = root_state.fast_copy(); // see section 2
    int current_player = root_player;

    // Selection
    while (node->untried_moves.empty() && !node->children.empty()) {
        if (time_up()) goto END_SEARCH;
        node = node->uct_select_child(C);
        state.apply_move(node->move);
        current_player = -current_player;
    }

    // Expansion
    if (!node->untried_moves.empty()) {
        if (time_up()) goto END_SEARCH;

        int idx = (int)(rng() % node->untried_moves.size());
        Move m = node->untried_moves[idx];

        // swap-pop removal (section 4)
        node->untried_moves[idx] = node->untried_moves.back();
        node->untried_moves.pop_back();

        state.apply_move(m);
        current_player = -current_player;

        MCTSNode* new_node = new MCTSNode(node, m, -current_player);

        if (time_up()) { delete new_node; goto END_SEARCH; } // avoid starting get_legal_moves late
        new_node->untried_moves = state.get_legal_moves(current_player);

        node->children.push_back(new_node);
        node = new_node;
    }

    if (time_up()) goto END_SEARCH;
    double win_prob = evaluate_optimized(state.grid, root_player);

    // Backprop
    while (node) { ... }
}
END_SEARCH:
```

This prevents “start a huge `get_legal_moves` when you’re already near the limit”.

---

## 2) Fix `Board::copy()` so it’s O(64) and doesn’t re-init every time

### Patch: add a “no-init” constructor and a fast copy
Change `Board` to:

```cpp
class Board {
public:
    array<array<int, GRID_SIZE>, GRID_SIZE> grid;

    Board(bool do_init = true) {
        for (int i = 0; i < GRID_SIZE; i++)
            for (int j = 0; j < GRID_SIZE; j++)
                grid[i][j] = EMPTY;
        if (do_init) init_board();
    }

    Board fast_copy() const {
        Board b(false);        // IMPORTANT: no init_board()
        b.grid = grid;
        return b;
    }

    ...
};
```

Then in search replace:
```cpp
Board state = root_state.copy();
```
with:
```cpp
Board state = root_state.fast_copy();
```

This alone can remove a lot of per-iteration overhead and variance.

---

## 3) Start timing BEFORE root initialization inside `search()`

Right now, on the first call, you do move generation before starting the clock. Fix by moving timer setup above root init (section 1 already does that).

Then keep:

```cpp
if (root == nullptr) {
    root = new MCTSNode(nullptr, Move(), -root_player);
    if (time_up()) goto END_SEARCH; // don’t start huge work if already near deadline
    root->untried_moves = root_state.get_legal_moves(root_player);
}
```

---

## 4) Remove `vector::erase` spikes (use swap-pop)

Replace:

```cpp
node->untried_moves.erase(node->untried_moves.begin() + idx);
```

with:

```cpp
node->untried_moves[idx] = node->untried_moves.back();
node->untried_moves.pop_back();
```

This avoids O(n) shifting and removes a big source of unpredictable iteration time.

Also replace `uniform_int_distribution` creation with modulo to reduce overhead:

```cpp
int idx = (int)(rng() % node->untried_moves.size());
```

Modulo bias is irrelevant here.

---

## 5) Stop `advance_root()` from causing unpredictable massive deletes

This is the #1 “sometimes it exceeds” culprit.

### Option A (fastest to implement): don’t delete trees during the match
Change `advance_root` to **never call `delete root`** (no recursive destruction spike). Yes, it leaks; but it stabilizes time immediately.

```cpp
void advance_root(const Move& move) {
    if (!root) return;

    for (auto child : root->children) {
        if (child->move == move) {
            root = child;
            root->parent = nullptr;
            return;
        }
    }
    // If not found, just drop the pointer (leak old tree)
    root = nullptr;
}
```

If you worry about memory, also do this: **stop storing `untried_moves` for every node** (biggest memory hog), or don’t reuse tree at all (see Option C).

### Option B (still reuses tree, less leak): detach new root but DON’T delete old root now
Keep a garbage list and delete at program end (or never):

```cpp
vector<MCTSNode*> garbage;

void advance_root(const Move& move) {
    if (!root) return;

    MCTSNode* old = root;
    MCTSNode* new_root = nullptr;

    for (auto child : root->children) {
        if (child->move == move) { new_root = child; break; }
    }

    if (new_root) {
        // Detach so old destructor won't delete it
        old->children.erase(remove(old->children.begin(), old->children.end(), new_root),
                            old->children.end());
        new_root->parent = nullptr;
        root = new_root;
        garbage.push_back(old);   // don't delete now
    } else {
        root = nullptr;
        garbage.push_back(old);   // don't delete now
    }
}
```

### Option C (most stable overall): remove tree reuse entirely
This eliminates both deletion spikes and cross-turn memory growth.

- Delete `advance_root()` usage (or make it `root=nullptr` always)
- In `search()`, always create a fresh root and discard after move (or keep only root but don’t carry over)

This is weaker play-wise but extremely stable under strict time limits.

---

## 6) Make `get_legal_moves` less spiky

### Patch: reserve a reasonable capacity
At the top of `get_legal_moves`:

```cpp
vector<Move> moves;
moves.reserve(4096); // tune; pick something that avoids reallocation most turns
```

Reallocations are a classic source of occasional time spikes.

---

## 7) Output path: don’t do heavy work after you’ve decided the move
Even if Botzone usually stops timing at flush, assume the worst: keep the post-decision work minimal.

After `best_move = ai.search(...)`, do **not** trigger huge deletes. With Option A/B above, `advance_root` is cheap.

---

## 8) Recommended final parameter tuning
After the above fixes, set your internal MCTS budget lower than the judge limit.

For a 1.0s judge limit:
- set `time_limit = 0.85` and `SAFETY = 0.05~0.08`

For a 2.0s judge limit:
- set `time_limit = 1.75` and `SAFETY = 0.07~0.12`

Your current `0.88` and `1.88` leave little headroom for OS scheduling + worst-case expansions.

---

## Minimal checklist to hand to your agent

1) Implement `Board fast_copy()` that doesn’t call `init_board()` and use it in every iteration.  
2) Replace elapsed-time loop with a `deadline` + `SAFETY` margin.  
3) Insert `time_up()` checks before: selection steps, expansion, `get_legal_moves`, evaluation.  
4) Replace `erase` with swap-pop; replace `uniform_int_distribution` with `rng()%n`.  
5) Remove or postpone recursive tree deletion in `advance_root` (Option A is simplest).  
6) `moves.reserve(4096)` in `get_legal_moves`.  
7) Reduce internal `time_limit` a bit further to keep margin.

If you apply only (1), (2), and (5), the “sometimes surpasses limit” problem usually disappears in practice.