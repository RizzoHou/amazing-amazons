If that “first turn 121 ms” happened locally, then yes: bot019 is almost certainly **ending the search early for a reason other than the time limit**. Your search loop has three non-time escape hatches:

```cpp
if (node_pool_ptr > MAX_NODES - 500) break;
if (move_pool_ptr > MAX_MOVES_POOL - 5000) break;
```

In Amazons, `get_legal_moves()` can easily generate **hundreds to thousands of moves per node** early game. Because you generate and store a full move list for *every expanded node*, `move_pool_ptr` can hit the cap quickly, and the search stops even though there is time left.

### 1) Use the remaining time even when pools are near full
Instead of `break`, switch to “no more expansion, only selection+eval+backprop”.

Minimal pattern:

- add a flag `bool allow_expand = true;`
- when near limits, set `allow_expand = false` (don’t break)
- if `!allow_expand`, skip expansion and just evaluate the selected leaf state

Important detail: you must not confuse “didn’t expand” with “terminal”. Your current “terminal” logic partially depends on whether moves were generated. Easiest fix is to add a `bool moves_generated` in the node (or use `moves_start_idx != -1` as a proxy) so “terminal” means “generated moves and count==0”, not “count==0 because we stopped expanding”.

---

## 2) The real fix: reduce move-pool pressure
Right now the pool is big, but the *consumption rate* is the killer.

### Option A: cap moves generated per node
Change `get_legal_moves()` to stop after `cap` moves:

- early game cap: 256–512 (usually enough)
- late game cap: can raise (branching naturally shrinks)

This alone prevents “pool-full -> early stop” and also speeds each expansion.

### Option B: progressive widening (strong + memory-friendly)
Don’t store “all untried moves” at all.

Rule: only add a new child when
`children_count < A + B * sqrt(visits)`.

When you want to expand, generate **one random legal move** (or a small batch), check it’s not already among children (linear scan is OK because children per node stays limited), then add it. This removes the need for gigantic per-node move lists.

This is the standard way to make MCTS behave in huge branching-factor games.

---

## 3) Make sure you’re not losing budget before search even starts
In `main()` you do:

```cpp
auto start_time = chrono::steady_clock::now();
// parse input...
Move best = search(..., start_time, limit - 0.05);
```

So parsing time eats into the “search deadline”. It’s probably not 1.8 seconds worth, but it’s still free strength to fix.

Do:

```cpp
// parse first
auto search_start = chrono::steady_clock::now();
double budget = limit - 0.05;
Move best = search(board, my_color, turn, search_start, budget);
```

Or even compute `budget = limit - elapsed_since_program_start - safety`.

---

## 4) Confirm your memory fits 256 MB on Botzone
Your local “2 GB” number is likely not resident RAM, but still: on a 256 MB judge you should hard-verify structure sizes.

Add:

```cpp
static_assert(sizeof(Move) == 6, "Move got padded; pack it or change pool size");
```

If `Move` ever becomes 8 bytes, then `18,000,000 * 8 = 144 MB` just for moves; still maybe ok, but you want to *know*, not guess.

If you want guaranteed compactness, pack moves into a `uint32_t` (6 coords × 3 bits = 18 bits). That cuts move pool memory ~in half.

---

## 5) Cheap speedups per iteration
These don’t fix the early-stop issue, but they increase iterations/sec:

- In `evaluate()`, stop allocating `vector<int>` every call. Use fixed arrays of size 4 and counts. Heap churn inside MCTS is costly.
- In `get_legal_moves()`, delete the dead code (`DIR_OFFSET`, `offset`, `curr`, the unused `switch(d)` etc.). Even if the compiler removes some, don’t rely on it.
- Replace `nx*8 + ny` with `(nx<<3) | ny` (minor, but it’s in hot loops).

---

### What I’d do first (highest impact)
1) Replace `break` on pool limits with “disable expansion but keep searching”.
2) Cap per-node move generation (256–512 early).
3) Remove per-eval heap allocations (vectors → fixed arrays).
4) Add `static_assert(sizeof(Move)==6)` (or pack to `uint32_t`).

If you apply (1)+(2), bot019 should start using close to the full 1s/2s budget *without* exceeding 256 MB, and strength should jump because you’ll get far more meaningful iterations instead of stopping early due to pool exhaustion.