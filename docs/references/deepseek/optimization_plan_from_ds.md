We’ll provide a structured optimization plan targeting the key bottlenecks identified in your MCTS-based Amazons bot. The suggested improvements aim to increase the number of iterations by 50‑100% while maintaining (or even improving) playing strength.

---

## 1. Move Generation – ~35% of runtime

### 1.1 Micro‑optimizations

- **Pre‑allocate the moves vector**  
  Call `moves.reserve(800);` before filling it to eliminate repeated reallocations.

- **Simplify the arrow collision check**  
  The current condition inside the arrow loop can be streamlined:
  ```cpp
  if (grid[ax][ay] != EMPTY && !(ax == px && ay == py))
      break;
  ```
  This reduces one level of nesting.

- **Use local references**  
  Capture `grid` in a local reference to help the compiler:  
  `const auto& g = grid;`

- **Unroll the direction loops?**  
  With only 8 directions, manual unrolling is unlikely to help; the compiler will likely vectorize if possible.

These changes may yield a small speedup, but the real gain lies in a more fundamental rewrite.

### 1.2 Bitboard Overhaul (Recommended)

A bitboard representation drastically reduces memory accesses and makes board copying/updating nearly free. For an 8×8 board, use three `uint64_t` masks:

```cpp
struct Board {
    uint64_t queens[2]; // BLACK = 0, WHITE = 1
    uint64_t arrows;    // obstacles (all arrows)
};
```

**Precomputed masks**  
Define masks for each direction that remove squares that would wrap around the board edges, e.g.:

```cpp
const uint64_t NOT_A_FILE = 0xfefefefefefefefe;
const uint64_t NOT_H_FILE = 0x7f7f7f7f7f7f7f7f;
```

**Shift functions**  
```
inline uint64_t shift_N (uint64_t b) { return b << 8; }
inline uint64_t shift_S (uint64_t b) { return b >> 8; }
inline uint64_t shift_E (uint64_t b) { return (b << 1) & NOT_A_FILE; }
inline uint64_t shift_W (uint64_t b) { return (b >> 1) & NOT_H_FILE; }
// similarly for NE, NW, SE, SW with appropriate masks
```

**Move generation algorithm**  
1. Compute `occupied = queens[0] | queens[1] | arrows`.  
2. For each queen of the moving player (iterate over set bits of `my_queens`):
   - Remove the queen from the occupancy: `occ_without_src = occupied ^ src_bit`.  
   - For each of the 8 directions, slide the queen bit until blocked, collecting destination bits.  
   - For each destination bit (iterate over set bits of the destinations mask):
     - Arrow occupancy = `occ_without_src | dest_bit`.  
     - For each of the 8 directions, slide the destination bit until blocked, collecting arrow bits.  
     - For each arrow bit, record a move (src, dest, arrow).  

**Benefits**  
- No bounds checks: shifts automatically stay inside the board thanks to masking.  
- Occupancy checks are simple bitwise operations.  
- Copying a `Board` is just copying three 64‑bit integers.  
- Applying a move becomes a few XORs.  
- Move generation can be 2–3× faster.

**Implementation notes**  
- Use `__builtin_ctzll` (GCC/Clang) or equivalent to iterate over set bits.  
- Precompute the index‑to‑coordinate mapping once.  
- Because the board is tiny, you can even inline the whole generation for maximum speed.

### 1.3 Move Ordering (Quality Improvement)

Once moves are generated, sort them by a cheap heuristic to improve the early focus of MCTS. A simple but effective heuristic:

```cpp
int score_move(const Move& m, const Board& b, int color) {
    // centrality of destination (precomputed table)
    static const int center[8][8] = { ... }; // e.g. 7 - max(|x-3.5|,|y-3.5|)
    int sc = center[m.x1][m.y1];

    // arrow closeness to opponent queens
    uint64_t opp_queens = b.queens[1 - color];
    int minDist = 99;
    while (opp_queens) {
        int idx = __builtin_ctzll(opp_queens);
        int qx = idx / 8, qy = idx % 8;
        int d = std::max(std::abs(m.x2 - qx), std::abs(m.y2 - qy));
        if (d < minDist) minDist = d;
        opp_queens &= opp_queens - 1;
    }
    sc += (minDist <= 6) ? (6 - minDist) : 0;   // favour close arrows
    return sc;
}
```

After generating all moves, sort descending by score. This ordering can be used in two ways:

- **Deterministic expansion**: always expand the first untried move (the one with highest score). This biases the tree toward promising lines, but combined with UCT selection it usually works well.  
- **Progressive widening** (see next subsection).

### 1.4 Progressive Widening (Optional)

To reduce the branching factor and the time spent generating moves for nodes that are rarely visited, only keep the top *K* moves initially (*K* ≈ 30–40). When a node’s visits exceed a threshold (e.g., 100), add the next best moves from the reserve list. This way the expensive move generation is still performed once (when the node is created), but the tree stays narrower, allowing deeper searches.

Implementation sketch inside `MCTSNode`:

```cpp
std::vector<Move> untried;     // moves currently considered
std::vector<Move> reserved;    // moves not yet considered
int width;                     // current max number of untried moves
```

When creating a node:
- Generate all moves, score them, sort.
- `untried` = first `initialWidth` moves.
- `reserved` = remaining moves.

During expansion, if `untried` is empty but `reserved` is not, and `visits % addInterval == 0`, move a batch from `reserved` to `untried`. Then pick a random move from `untried` as before.

Progressive widening can significantly increase effective depth without increasing iteration count.

---

## 2. Territory Evaluation (BFS) – ~30% of runtime

### 2.1 Replace `std::unordered_map` and `std::deque` with plain arrays

The current BFS uses heavy containers. For a fixed 8×8 board we can use:

- A `char dist[8][8]` (or `int8_t`) initialized to `-1`.  
- A simple FIFO queue as a fixed-size array of 64 integers (packed coordinates).  
- An array `int cnt[MAX_DIST]` (MAX_DIST ≤ 64) to count cells per distance.

```cpp
void bfs_territory(const Board& b, int color, int cnt[]) {
    static char dist[8][8];
    static int queue[64];
    memset(dist, -1, sizeof(dist));
    int head = 0, tail = 0;

    // init with our queens
    uint64_t qbits = b.queens[color];
    while (qbits) {
        int idx = __builtin_ctzll(qbits);
        int x = idx >> 3, y = idx & 7;
        dist[x][y] = 0;
        queue[tail++] = idx;
        qbits &= qbits - 1;
    }

    while (head < tail) {
        int idx = queue[head++];
        int x = idx >> 3, y = idx & 7;
        int d = dist[x][y] + 1;
        for (int dir = 0; dir < 8; ++dir) {
            int nx = x + DX[dir], ny = y + DY[dir];
            if (nx < 0 || nx >= 8 || ny < 0 || ny >= 8) continue;
            if (dist[nx][ny] != -1) continue;
            // Check cell is empty (neither queen nor arrow)
            uint64_t bit = 1ULL << (nx*8+ny);
            if (b.queens[0] & bit || b.queens[1] & bit || b.arrows & bit) continue;
            dist[nx][ny] = d;
            queue[tail++] = (nx<<3) | ny;
            if (d < MAX_DIST) cnt[d]++;
        }
    }
}
```

### 2.2 Compute Weighted Sums On‑the‑Fly

Instead of storing `cnt` and later iterating, directly accumulate the four component scores during the BFS. Precompute tables for the weights:

```cpp
const double queen_terr_weight[64] = {0, 2^-1, 2^-2, ...};
const double king_terr_weight[64] = {0, ...};
// etc.
```

During the neighbor discovery:

```cpp
double queen_terr = 0.0, king_terr = 0.0, queen_pos = 0.0, king_pos = 0.0;
...
if (d < MAX_DIST) {
    queen_terr += queen_terr_weight[d];
    if (d <= 3) king_terr += king_terr_weight[d];
    queen_pos  += queen_pos_weight[d];
    king_pos   += king_pos_weight[d];
}
```

After the BFS you have the four component values ready – no extra loops.

### 2.3 Combine Both Players’ BFS

If you keep the bitboard representation, you can even compute both players’ territory in one combined BFS by using separate distance arrays and a two‑colour queue. However, the board is so small that two separate BFS runs are still cheap; the major saving comes from removing the `unordered_map` and `deque`.

---

## 3. Memory Allocation – ~15% of runtime

### 3.1 Node Pool Allocator

Replace individual `new` / `delete` for `MCTSNode` with a custom pool. Since nodes are only freed in bulk (when the tree is pruned between turns), a simple arena works well.

```cpp
class NodePool {
    std::vector<char> memory;
    size_t offset;
public:
    void* allocate(size_t size) {
        if (offset + size > memory.size())
            memory.resize(std::max(memory.size() * 2, offset + size));
        void* ptr = &memory[offset];
        offset += size;
        return ptr;
    }
    void reset() { offset = 0; }   // call only when whole tree is discarded
};

template<typename T, typename... Args>
T* pool_new(NodePool& pool, Args&&... args) {
    void* p = pool.allocate(sizeof(T));
    return new (p) T(std::forward<Args>(args)...);
}
```

In `MCTSNode` constructor, use `pool_new<Node>(pool, ...)`. Because nodes contain `std::vector` members, they will still allocate their own dynamic memory for children and untried moves. To reduce that overhead you can:

- Store children as a small array of pointers, but a `std::vector` is fine.  
- If you implement progressive widening, the number of children per node stays small, so vector reallocations are minimal.

### 3.2 Reuse Tree Between Turns

You already keep the subtree of the chosen move. Ensure that nodes that are discarded are actually returned to the pool (e.g., by resetting the whole pool at the end of each turn after copying the kept subtree). A more sophisticated free‑list can be used, but a simple reset is acceptable because the kept subtree is usually small (a few hundred nodes) and can be deep‑copied.

---

## 4. Random Number Generation – ~5% of runtime

Replace `std::mt19937` with a fast 64‑bit Xorshift:

```cpp
static uint64_t seed = 123456789;
inline uint64_t xorshift64() {
    seed ^= seed << 13;
    seed ^= seed >> 7;
    seed ^= seed << 17;
    return seed;
}
```

To pick a random index from `0..n-1`: `int idx = xorshift64() % n;` (bias negligible for n ≤ 800). If you need a double in [0,1): `(xorshift64() >> 11) * (1.0 / (1ULL << 53))`.

---

## 5. Compiler & Micro‑Optimizations

- **Compiler flags**  
  If Botzone allows, change to `-O3 -march=native -flto`. Even `-Ofast -march=native` can be tried (be careful with floating‑point semantics).  
- **Inline hot functions**  
  Mark `uct_select_child`, `evaluate_multi_component`, and move generation as `inline` (or define them in the class body).  
- **Use `constexpr` and `static` for constants**  
  E.g., direction arrays.  
- **Avoid virtual functions** – not an issue.

---

## 6. Transposition Table (Optional, Higher Effort)

Zobrist hashing can detect duplicate states and reuse their evaluation statistics. However, merging nodes turns the tree into a graph, complicating backpropagation. A simpler approach: cache only the evaluation result (win probability) in a global hash table keyed by board state + player to move. When a leaf state is reached, first look up the table; if found, use the cached value, otherwise compute and store. This avoids duplicate BFS computations without altering the tree structure.

Implementation steps:
- Precompute two 64‑bit random numbers for each cell and each piece type (black queen, white queen, arrow).  
- Compute hash incrementally when making/unmaking moves.  
- Use an `unordered_map<uint64_t, double>` or a custom open‑addressing table.  
- Because the cache lives only for one search, you can clear it each turn.

This can significantly reduce the number of evaluations when transpositions are frequent.

---

## 7. Time Management

Your current fixed time limits are fine. However, you can add a simple dynamic adjustment: if the best move’s visit count is already dominant early, you may stop earlier, saving time for later moves. But this is low priority.

---

## Expected Speedup

Applying the core optimisations:

- Bitboard move generation → ~2× faster.  
- Optimised BFS → ~2–3× faster.  
- Node pool + faster PRNG → ~1.2× faster.  
- Compiler flags → ~1.1× faster.

Cumulatively you can expect at least a 50‑100% increase in iterations (i.e., 1.5× to 2× current). Moreover, move ordering and progressive widening will improve the quality of each iteration, effectively increasing strength further.

---

## Implementation Order

We recommend implementing changes in this order:

1. Bitboard representation + move generation.  
2. BFS optimisation (array‑based, on‑the‑fly sums).  
3. Node pool and fast PRNG.  
4. Move ordering and (optionally) progressive widening.  
5. Transposition table (if still needed).

Each step is testable and should yield measurable speed improvements.

---

Let us know if you need further details on any specific part. Good luck with the optimisation!