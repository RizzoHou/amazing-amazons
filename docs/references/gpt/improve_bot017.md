Yes—your version already removed a couple of big wastes (board init in copy, `erase`, frequent clock calls, smaller `Move`). The remaining bottlenecks are now mostly:

- **Generating full legal-move lists** (extremely expensive in Amazons-like games)
- **Heap allocations** (vectors + `new MCTSNode` in the hot loop)
- **Per-evaluation allocations** (`vector<pair<int,int>>` + `reserve()` still allocates every call)

Here are improvements that are still very available, ordered by “impact / effort”.

---

## 1) Stop allocating in `evaluate_optimized` (easy, usually measurable)
Right now, every evaluation does two heap allocations because `reserve(4)` on an empty vector allocates every call.

Replace those vectors with fixed-size arrays on the stack:

```cpp
struct Pieces4 {
    uint8_t x[4], y[4];
    int n = 0;
};

inline void collect_pieces4(const array<array<int, GRID_SIZE>, GRID_SIZE>& grid,
                            int color, Pieces4& out) {
    out.n = 0;
    for (int i = 0; i < GRID_SIZE; i++)
        for (int j = 0; j < GRID_SIZE; j++)
            if (grid[i][j] == color) {
                out.x[out.n] = (uint8_t)i;
                out.y[out.n] = (uint8_t)j;
                out.n++;
            }
}
```

Then adjust BFS/mobility to accept `(x[], y[], n)` instead of `vector<pair<int,int>>`. This removes allocations from the hottest path.

---

## 2) Cache phase weights once per search (tiny change)
`evaluate_optimized()` calls `get_phase_weights(turn_number)` every iteration. It’s small, but free to remove.

In `search()`:
```cpp
const double* weights = get_phase_weights(turn_number);
```

Pass `weights` into `evaluate_optimized(grid, root_player, weights)` and use it directly.

---

## 3) Add “lazy child move generation” (good speedup, low code risk)
You currently do this on every expansion:
```cpp
new_node->untried_moves = state.get_legal_moves(current_player);
```
…but you **don’t need the child’s moves for evaluation**. Many children will never be revisited, so generating their move lists is wasted.

Add a flag in `MCTSNode`:
```cpp
bool moves_inited = false;
```

In the iteration, when you arrive at a node and might expand/select from it, initialize its moves *then*:

```cpp
// before selection/expansion decisions at this node:
if (!node->moves_inited) {
    node->untried_moves = state.get_legal_moves(current_player);
    node->moves_inited = true;
}
```

In expansion, do **not** generate the new child’s move list:
```cpp
MCTSNode* new_node = new MCTSNode(node, m, -current_player);
new_node->moves_inited = false; // leave empty
```

This often increases iterations because you stop paying “move generation for nodes you never use”.

Also add terminal handling:
- If `moves_inited==true`, `untried_moves.empty()`, and `children.empty()`, then the side to move has no moves (terminal).

---

## 4) Reserve in `get_legal_moves` (easy)
Early/midgame move counts can be large, and `push_back` reallocation is costly.

```cpp
vector<Move> moves;
moves.reserve(2048); // tune; 1024/2048/4096 depending on time/memory tradeoff
```

This helps especially at root and at frequently visited nodes.

---

## 5) Biggest win: don’t enumerate all moves at deep nodes (progressive widening / sampling)
This is the main reason Amazons bots struggle under 1s: branching factor is huge.

Two practical options:

### A) Progressive widening
Only allow a node to have up to:
```text
max_children = k * visits^alpha   (alpha ~ 0.5)
```
When you need a new child, **sample** a legal move (randomly or with a cheap heuristic) and add it, instead of storing all untried moves.

That lets you avoid `vector<Move> untried_moves` entirely at deep nodes, or keep it very small.

### B) “Top-K” move generation
At depth > 1 (or when `turn_number` is large), generate only K moves using a cheap heuristic, not all moves. Even K=32 or 64 can massively increase iterations and often *improves* strength because MCTS focuses.

If you do only one “big structural” change, do this.

---

## 6) Node pool (arena allocator) for `MCTSNode` (medium effort, big payoff)
`new MCTSNode` in a tight loop is slow and fragments memory.

Typical pattern:
- allocate a large `vector<MCTSNode>` or raw array once per search
- hand out nodes by incrementing an index
- no per-node `delete`; just reset the index each turn

This can give a noticeable iteration increase under 1s.

---

## 7) Store piece coordinates in `Board` (medium effort, helps both movegen + eval)
Both `get_legal_moves` and `evaluate_optimized` scan the whole board to find pieces.

Keep:
```cpp
array<pair<uint8_t,uint8_t>,4> black, white;
```
Update them in `apply_move` (O(4) find). Then:
- `get_legal_moves(color)` iterates 4 pieces directly
- evaluation gets piece lists without scanning or allocating

This is one of the cleaner “speed + code clarity” upgrades.

---

## 8) Consider a cheaper sigmoid (micro, but `exp` is not free)
You can clamp or approximate:
```cpp
if (score > 8) return 0.999;
if (score < -8) return 0.001;
return 1.0 / (1.0 + exp(-score));
```
This avoids `exp` in extreme cases.

---

### One thing that hurts iterations right now
`SAFETY_MARGIN = 0.20` is very conservative for a 1.00s limit. If your bot is stable after the “check every 256 iters” change, you can usually lower it (often 0.05–0.10). That’s a direct iteration gain.

---

If you want the highest “iterations per second” jump without a full rewrite, implement **(1) no-alloc evaluation + (3) lazy move init**. If you want the biggest overall leap, implement **progressive widening** so deep nodes stop enumerating thousands of moves.