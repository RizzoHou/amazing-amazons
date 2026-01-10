Your self‑play log is telling you something very specific:

- Turn 1–2 you only spend ~0.45–0.50s although you *intend* to search ~1.9s.
- At the same time RSS is ~400MB.
- In later turns you spend ~0.93s and RSS is much lower.

That pattern almost always means: **you are hitting your move pool limit early game** (or getting very close and tripping the `move_pool_ptr > MAX_MOVES_POOL - 5000` break), so the loop exits *before* the time deadline. Early game Amazons has a gigantic branching factor; your design (“store full untried move list for every expanded node”) explodes memory.

So the fastest strength gain is: **stop generating/storing *all* moves for *every* expanded node**.

Below are improvements in priority order.

---

## 1) Fix the core bottleneck: don’t materialize full move lists (progressive widening / sampled expansion)

### Why
`get_legal_moves()` is \(O(#moves)\) and you call it for every newly expanded node. In early game that’s enormous, and you also *store* all those moves in `move_pool`.

### What to do (MCTS-standard for huge branching)
Use **progressive widening**:

- Each node starts with 0 children.
- Only allow adding a new child when:
  \[
  children < k \cdot visits^\alpha
  \]
  Typical: `alpha = 0.5`, `k = 2..8`.
- When you’re allowed to add a child, generate **one random legal move** (or one “good” move) and create that child.
- Otherwise do UCT selection among existing children.

This eliminates the per-node giant move list entirely (or restrict it to near-root only).

### Practical approach
- Replace `moves_start_idx/moves_count` with:
  - `uint16_t children_count` (or compute by traversing siblings + store count)
  - maybe a flag `is_terminal_known`
- Implement `random_legal_move(board, player)` that returns a single legal move without enumerating them all.

If you’re worried about “random move generator might fail to find a move”, do:
- Try N random attempts (e.g. 64).
- If all fail, fall back to full enumeration *once* to confirm terminal / pick a move.

This one change typically lets you use the full 1s/2s every turn and increases node count a lot.

---

## 2) Compress the move representation (cheap win even if you keep a pool)

Right now you store `(x0,y0,x1,y1,x2,y2)` (6 bytes if packed, often more once embedded in `MCTSNode` due to padding).

You can store a move as **three squares** in `[0..63]`:

```cpp
#pragma pack(push, 1)
struct Move {
    uint8_t from, to, arrow;
};
#pragma pack(pop)
static_assert(sizeof(Move) == 3);
```

Then:

```cpp
inline void apply_move(const Move& m) {
    int piece = grid[m.from];
    grid[m.from] = EMPTY;
    grid[m.to] = piece;
    grid[m.arrow] = OBSTACLE;
}
```

And when outputting:
```cpp
auto x = sq / 8, y = sq % 8;
```

This alone cuts your move-pool RAM by ~2× and also improves cache behavior.

(If you still want coordinates in Move, at least reorder members in `MCTSNode` to minimize padding; but square-index moves are best.)

---

## 3) If you keep “untried moves”, don’t store *all* of them: cap / filter

If you don’t want progressive widening yet, at least do **selective move storage**:

- Generate all moves for a node, score each quickly (very cheap heuristic), and keep only top **K** (e.g. 32/64/128).
- Or keep all *queen destinations* but only best **M** arrow shots per destination.

This reduces both:
- branching factor the tree actually explores
- memory pressure on `move_pool`

A very cheap heuristic that works surprisingly well:
- mobility delta (after move)
- centralization / staying out of corners early
- arrow that reduces opponent mobility

Even “keep K random moves” already helps memory a lot.

---

## 4) Speed up move generation with precomputed rays (applies to any search)

Your `while(nx += d_row, ny += d_col)` boundary checks are fine, but you can speed it up by precomputing for each square and direction the ray squares:

```cpp
// ray[sq][dir] = list of squares in that direction
// ray_len[sq][dir] = length
```

Then move generation becomes iterating over arrays (no bounds checks, no /8,%8 inside inner loops). This is a big constant-factor win in Amazons.

Even better: represent occupancy as bitboards and use sliding attacks, but ray tables are simpler and already fast.

---

## 5) Improve evaluation quality (your current BFS is “king-distance”, not “queen-distance”)

Your `run_bfs` expands to 8 neighbors (king steps). In Amazons, territory is usually modeled with **queen-move distance** (each edge is “one queen move along a ray until blocked”).

Using king-distance can mis-evaluate who controls a region.

Two options:

1) **Queen-distance BFS** (stronger, a bit slower)
- BFS nodes are squares, neighbors are all squares reachable by a queen in one move (slide along 8 rays).

2) Hybrid (often best under 1s):
- Keep your fast king-distance BFS,
- add an explicit **region/endgame scoring**: when the board partitions into independent regions (common mid/late), flood-fill each region and count which player has queens inside → near-exact scoring.

Region partition scoring is extremely high value in Amazons.

---

## 6) Small but important correctness/quality checks

- **WEIGHTS_TABLE indexing looks off-by-one**: you do `idx = turn` (so turn=1 uses row 1, not row 0). If those weights were trained for turn starting at 1→row0, you want:
  ```cpp
  int idx = (turn >= 28) ? 27 : (turn - 1);
  ```
  If you’re not 100% sure, test both; this can noticeably change play.

- Turn 1 under-uses time: after (1)–(3), re-check you’re actually running to the deadline and not hitting pool/node cutoffs.

---

## What I would do first (minimal code churn → big gain)

1) Change `Move` to `{from,to,arrow}` (3 bytes) and adapt apply/output.
2) Add progressive widening + random move expansion so you **stop calling `get_legal_moves` for every new node**.
3) Only if needed: keep full enumeration for depth 0–1 (root and maybe its children), and sampled expansion deeper.

That combination usually gives the biggest Elo jump per hour spent on Amazons bots under 1s.

---

If you want, paste (or describe) how many iterations/nodes/moves you reach per turn (add a few counters printed to `cerr`), and I can suggest concrete `k, alpha`, plus a good fast random-move generator that respects “origin square becomes empty” without needing full enumeration.