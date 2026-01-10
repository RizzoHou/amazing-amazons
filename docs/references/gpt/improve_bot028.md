What you’re observing is real and it’s not a contradiction: **`sizeof(Move)` got smaller, but your program started *touching/committing* a lot more memory pages** in bot028, so RSS (the “memory usage” Botzone reports) becomes larger.

The key difference is this line in bot028:

```cpp
Move() : from(0), to(0), arrow(0) {}
```

That makes `Move` **non-trivial** and its default constructor **writes to memory**.

### Why that explodes RSS in bot028

#### 1) `node_pool = new MCTSNode[MAX_NODES];` now *constructs* 7,000,000 nodes
`MCTSNode` has a member `Move move;`.  
If `Move` has a user-provided default constructor, then `MCTSNode`’s implicit default constructor becomes non-trivial, so:

```cpp
new MCTSNode[MAX_NODES]
```

will run a constructor for **every** element, which runs `Move()` for every node, which **writes 3 bytes** per node.

Even though that’s “only 3 bytes per node”, those writes are spread across the entire allocated `node_pool` region, so **almost every 4KB page becomes dirty/resident**.

Result: you effectively commit most/all of the `node_pool` mapping to RSS immediately.

Rough scale:
- If `sizeof(MCTSNode)` is ~48 bytes in bot028, then 7,000,000 nodes ≈ **336 MB**.
- Touching even 1 byte in each page tends to commit the whole page → RSS ≈ hundreds of MB.

In bot027, your `Move() = default;` does **not write anything**, so even if constructors run, they can be optimized to no stores and pages stay uncommitted until you actually use nodes.

#### 2) Your global `move_pool[MAX_MOVES_POOL]` may also get dynamically initialized
For a global array of a non-trivial type, the runtime may need to run constructors before `main()`. If that constructor writes (your bot028 does), it can also commit a lot of the move pool.

---

## Fix: make `Move` trivially constructible (no constructors)

Do this in bot028:

```cpp
#pragma pack(push, 1)
struct Move {
    uint8_t from, to, arrow;
};
#pragma pack(pop)

static_assert(std::is_trivially_copyable<Move>::value, "Move must be trivial");
static_assert(std::is_trivially_default_constructible<Move>::value, "Move must be trivial");
static_assert(sizeof(Move) == 3, "Move must be 3 bytes");
```

And when you create moves, use aggregate initialization:

```cpp
move_pool[move_pool_ptr++] = Move{(uint8_t)p, (uint8_t)n_idx, (uint8_t)a_idx};
```

For invalid move:

```cpp
return Move{255,255,255};
```

Root node:

```cpp
MCTSNode* root = new_node(nullptr, Move{0,0,0}, -root_player);
```

(Or any value; root->move isn’t used.)

This single change usually makes bot028’s RSS drop dramatically, because:
- `new MCTSNode[MAX_NODES]` no longer needs to write anything across the entire pool
- global `move_pool` stays mostly uncommitted until you actually store moves

---

## Even better (optional): allocate `node_pool` without constructing anything

If you want to be absolutely sure no mass-initialization happens, allocate raw storage:

```cpp
node_pool = static_cast<MCTSNode*>(std::malloc(sizeof(MCTSNode) * MAX_NODES));
```

Since you already call `init()` manually, you don’t need constructors at all. (Just don’t add non-trivial members to `MCTSNode`.)

---

### Summary
Bot028 uses more memory because **your new `Move()` constructor writes zeros**, which forces:
- `new[]` of millions of `MCTSNode` to **touch/commit** the whole `node_pool`
- possibly the global `move_pool` too

Make `Move` a trivial POD (no constructors), and you’ll get the expected memory reduction.

If you paste bot028’s Botzone memory log (like you did for bot027), I can sanity-check whether you’re still getting early termination by `move_pool_ptr` or whether RSS is now dominated by `node_pool` growth.