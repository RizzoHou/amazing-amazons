Biggest lever for “more MCTS iterations per second” in your code is reducing **per-iteration overhead** (allocations, move-list handling, time checks, copying). In your current loop the dominant costs are usually:

1) generating/storing **huge legal-move lists** (`get_legal_moves`)  
2) **heap allocations** (`new MCTSNode`, vectors growing, erase shifting)  
3) **time check every iteration** (`steady_clock::now()` + duration math)  
4) unnecessary work in `Board::copy()` (it calls `init_board()` every time!)

Below are concrete changes (roughly ordered by “easy + high impact”).

---

## 1) Fix `Board::copy()` (it’s doing extra work every iteration)
Right now:

```cpp
Board copy() const {
    Board new_board;      // calls init_board()
    new_board.grid = this->grid;
    return new_board;
}
```

This means **every MCTS iteration** does an `init_board()` (plus full clearing in the constructor) and then overwrites it. That’s pure waste.

### Minimal fix
Remove `copy()` and just use the implicit copy constructor:

```cpp
Board state = root_state; // memberwise copy of grid, no init_board()
```

In `search()` replace:
```cpp
Board state = root_state.copy();
```
with:
```cpp
Board state = root_state;
```

If you want to keep `copy()`, add a “no-init” constructor:

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

    Board copy() const {
        Board b(false);      // skip init_board
        b.grid = grid;
        return b;
    }
};
```

This alone can noticeably bump iteration count.

---

## 2) Don’t `erase()` from the middle of `untried_moves` (O(n) shift)
You do:

```cpp
node->untried_moves.erase(node->untried_moves.begin() + idx);
```

That shifts all elements after `idx` every expansion. Replace with swap-pop (O(1)):

```cpp
int idx = (int)(rng() % node->untried_moves.size());
Move m = node->untried_moves[idx];

// swap-pop removal
node->untried_moves[idx] = node->untried_moves.back();
node->untried_moves.pop_back();
```

Also: constructing `uniform_int_distribution` each time is avoidable (see above).

---

## 3) Stop calling `steady_clock::now()` every iteration
Time-check overhead becomes non-trivial when you push iterations high.

Use a **deadline** and check every N iterations:

```cpp
auto deadline = search_start_time + chrono::duration<double>(adjusted_time_limit);

for (int iterations = 0; ; ++iterations) {
    if ((iterations & 0xFF) == 0) { // every 256 iters
        if (chrono::steady_clock::now() >= deadline) break;
    }

    ...
}
```

This is a classic speedup for tight MCTS loops.

---

## 4) Shrink `Move` dramatically (memory + cache wins)
`Move` is 6 `int`s = typically 24 bytes. Your node stores lots of moves (root and many children), so this bloats memory bandwidth/cache.

On an 8×8 board, coordinates fit in 0..7, and you also use -1 for “pass”. Use `int8_t`:

```cpp
struct Move {
    int8_t x0, y0, x1, y1, x2, y2;
    Move() : x0(0), y0(0), x1(0), y1(0), x2(0), y2(0) {}
    Move(int a,int b,int c,int d,int e,int f)
        : x0((int8_t)a), y0((int8_t)b), x1((int8_t)c), y1((int8_t)d), x2((int8_t)e), y2((int8_t)f) {}
};
```

When outputting, cast to int:
```cpp
cout << (int)best_move.x0 << " " << (int)best_move.y0 << ...
```

This often helps both **speed and node capacity** under 256MB.

---

## 5) Reserve capacity in `get_legal_moves`
Avoid repeated reallocations:

```cpp
vector<Move> moves;
moves.reserve(2000); // tune; amazons can be large early
```

Also consider reserving `children` (small) and `untried_moves` in nodes if you know typical sizes.

---

## 6) Add terminal handling (strength + avoids wasted evaluation)
If the side to move has no legal moves, it’s terminal (in Amazons-like rules). Right now you still call `evaluate_optimized`.

At the point you compute `new_node->untried_moves = ...`, if it’s empty you can short-circuit the value.

Example (conceptually):
- If `current_player` (side to play) has **no moves**, then the player who just moved wins.

So inside your simulation, after you reach the leaf:
```cpp
double win_prob;
auto leaf_moves = state.get_legal_moves(current_player);
if (leaf_moves.empty()) {
    // current_player cannot move => loses
    win_prob = (current_player == root_player) ? 0.0 : 1.0;
} else {
    win_prob = evaluate_optimized(state.grid, root_player);
}
```

This improves play and also prevents “sigmoid + BFS” on obvious terminals.

---

## 7) Biggest structural bottleneck: generating full move lists at every new node
In Amazons-style games, branching factor is huge. Your expansion does:
```cpp
new_node->untried_moves = state.get_legal_moves(current_player);
```
That is expensive and also memory heavy.

Two practical approaches:

### A) Progressive widening (often a big win in high-branching games)
Instead of enumerating *all* legal moves at a node immediately, only allow a small number of children initially, and expand more as visits grow.

Rule of thumb:
```text
allow_children = k * visits^alpha   (alpha ~ 0.5)
```

Then you don’t need `untried_moves` to hold everything. You can generate a *batch* of candidate moves (or sample random legal moves) when widening triggers.

This is more code, but it’s one of the most effective changes for this kind of game.

### B) Heuristic top-K move generation
Generate all legal moves only at the root (or shallow depths), but at deeper nodes generate only K “promising” moves using a cheap heuristic (mobility delta, territory delta, etc.). This reduces both time and memory per node dramatically.

---

## 8) Memory allocation: use an arena/pool for nodes (and ideally move storage)
`new MCTSNode` in a tight loop is slow. A simple node pool can help a lot.

Even without fully redesigning vectors, you can at least pool the nodes:

- Preallocate `MCTSNode` objects in a big array.
- Replace `new`/`delete` with pool allocation.
- Don’t recursively delete children; just reset pool pointer each search.

This reduces allocator overhead and fragmentation.

---

## 9) Cheap evaluation speedups
If evaluation is a significant slice (it often is), consider:

- Replace `1/(1+exp(-score))` with a fast approximation (saves `exp`):
  ```cpp
  inline double fast_sigmoid(double x) {
      return 0.5 * (x / (1.0 + fabs(x)) + 1.0);
  }
  ```
  (This changes scaling a bit, but MCTS usually tolerates it.)

- Avoid rebuilding `my_pieces/opp_pieces` vectors each eval by storing piece coordinates in `Board` and updating them in `apply_move`. (This also helps move generation.)

---

## 10) Time budget tuning
Your `SAFETY_MARGIN = 0.10` is conservative for a 1.00s limit. If your bot rarely times out, dropping it to `0.05` (or dynamic: bigger on turn 1, smaller later) directly gives more iterations. Do this only after you reduce overhead and confirm you have stable runtime.

---

### If you only do 4 changes, do these:
1) **Fix `Board::copy()`** so it doesn’t run `init_board()` every iteration  
2) **swap-pop instead of `erase`** in `untried_moves`  
3) **time check every 256 iterations using a deadline**  
4) **shrink `Move`** to `int8_t` (or packed)

Those are straightforward edits and typically give the biggest “iterations per second” jump without redesigning the bot.

If you want, I can sketch a concrete progressive widening design that fits your current node structure (minimal rewrite), but the above should already move the needle a lot.