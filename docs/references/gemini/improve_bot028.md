The reason `bot028` consumes more memory than `bot027`—despite having smaller structs and smaller pool limits—is **Eager Initialization caused by the user-defined constructor**.

### The Technical Explanation

1.  **In `bot027` (Lazy Allocation):**
    ```cpp
    Move() = default; 
    ```
    This defines a **Trivial Type**.
    *   **Global `move_pool`:** The OS reserves 420MB of virtual address space but maps it to a zero-page. Physical RAM is only consumed (committed) when your code actually *writes* to a specific index in the array during the search.
    *   **Heap `node_pool`:** `new MCTSNode[MAX_NODES]` allocates virtual space. Because `Move` (and thus `MCTSNode`) is trivial, the `new` operator **does not initialize** the elements. No code runs to write to this memory. The OS does not allocate physical RAM for the array until you actually grab a node from the pool.
    *   **Result:** Memory usage grows slowly as the tree grows. Unused parts of the pools cost $0$ RAM.

2.  **In `bot028` (Eager Initialization):**
    ```cpp
    Move() : from(0), to(0), arrow(0) {} 
    ```
    This defines a **Non-Trivial Constructor**.
    *   **Global `move_pool`:** At program startup, the C++ runtime **must** run a loop to call this constructor for every single one of the 50,000,000 elements. This writes zeros to the entire 150MB array, forcing the OS to allocate physical RAM for 100% of it immediately.
    *   **Heap `node_pool`:** When you call `new MCTSNode[...]`, the compiler generates a loop to initialize the `move` member of all 7,000,000 nodes. This writes to the entire ~336MB block immediately.
    *   **Result:** You instantly consume ~486MB of physical RAM at the very first line of `main()`, which is dangerously close to the 512MB limit and much higher than `bot027`'s average usage.

### The Fix

Change the `Move` constructor back to `= default`. You do not need moves to be initialized to zero; you only need them valid when you actually generate a move.

**In `bot028`, replace the `Move` struct with this:**

```cpp
#pragma pack(push, 1)
struct Move {
    uint8_t from, to, arrow;
    
    // CHANGE THIS BACK TO DEFAULT
    // This restores "Trivial" status, allowing lazy memory allocation.
    Move() = default; 
    
    Move(int from_sq, int to_sq, int arrow_sq) 
        : from((uint8_t)from_sq), to((uint8_t)to_sq), arrow((uint8_t)arrow_sq) {}
};
#pragma pack(pop)
```

### Additional Safety Tweak

Even with the fix, `MAX_NODES = 7,000,000` is risky for `bot028` if the game goes long and fills the tree.
*   7M nodes $\times$ ~44 bytes $\approx$ 308 MB.
*   50M moves $\times$ 3 bytes $\approx$ 150 MB.
*   Total = 458 MB (plus stack + executable overhead).

This fits, but is tight. `bot027` survived because it likely never filled the pools. If you want to be safe on Botzone (512MB limit), I recommend slightly lowering the move pool, as 35M moves is usually plenty for 1 second of search.

```cpp
const int MAX_NODES = 7000000;      // ~308 MB
const int MAX_MOVES_POOL = 35000000; // ~105 MB -> Total ~413 MB (Safe)
```