# Request: Bot002 TLE (Time Limit Exceeded) Bug Solution

**Date**: December 15, 2025  
**Requesting Assistance From**: DeepSeek  
**Bug Status**: Critical - Blocks Botzone Deployment  
**Previous Fixes Attempted**: Failed

---

## Problem Summary

Bot002 consistently exceeds the 1000ms time limit on Botzone despite implementing conservative time limits and mid-iteration safety checks. The bot experiences TLE in late-game positions (turn 25-30), and the timing issue persists even after reducing time limits from 0.8s/1.6s to 0.7s/1.4s and adding safety buffers.

**Platform Time Limits**:
- C++ long-running bots: First turn = 2000ms, Subsequent turns = 1000ms
- Memory limit: 256MB (512MB observed in logs)

---

## Timing Analysis

### Original TLE Log Pattern (tle.log)
Bot002 timing progression before fix:
- Turns 1-4: Fast (166-1000ms)
- Turns 5-14: Moderate (162-368ms)
- Turns 15-24: High (574-595ms)
- **Turn 25**: 1000ms **TLE**

### New TLE Log Pattern (still_tle.json - AFTER FIX)
Bot002 timing progression with 0.7s/1.4s limits + safety check:
- **Turn 1**: 933ms (dangerously close despite 1400ms limit!)
- Turns 2-4: 163ms, 118ms, 143ms
- Turns 5-14: 162-368ms (gradually increasing)
- Turns 15-24: 574-595ms (consistent high)
- **Turn 25**: 951ms (extremely close to limit)
- **Turn 26**: 1000ms **TLE** (exceeded)

**Critical Observation**: Bot still hits TLE despite:
- Time limit set to 700ms (vs 1000ms platform limit)
- 150ms safety buffer before evaluation
- Mid-iteration time check implemented

---

## Previous Fix Attempts

### Fix #1: Conservative Time Limits (Failed)
**Changes made**:
```cpp
const double TIME_LIMIT = 0.7;  // 300ms safety buffer
const double FIRST_TURN_TIME_LIMIT = 1.4;  // 600ms safety buffer
```

**Why it failed**:
- First turn still reached 933ms (should stop at ~1250ms)
- Late game turns reached 951ms then 1000ms (should stop at ~550ms)
- Safety buffer appears insufficient or not being applied correctly

### Fix #2: Mid-Iteration Safety Check (Implemented but Insufficient)
**Changes made** (lines 515-518 in bot002.cpp):
```cpp
// Safety check: Don't start expensive evaluation if too close to time limit
current_time = chrono::steady_clock::now();
elapsed = chrono::duration<double>(current_time - start_time).count();
if (elapsed >= time_limit - 0.15) break;  // Reserve 150ms
```

**Why it's insufficient**:
- Even with this check, bot still exceeds 1000ms
- Suggests there's significant overhead AFTER the MCTS loop
- Or evaluation is taking much longer than 150ms estimate

---

## Key Observations

### 1. Time Budget Mystery
**Expected behavior with 700ms limit + 150ms buffer**:
- MCTS loop should exit at ~550ms
- Evaluation + final operations should complete by ~700ms
- Total time should be well under 1000ms

**Actual behavior**:
- Bot somehow reaches 951ms → 1000ms
- This suggests ~300-450ms unaccounted time

### 2. Late-Game Time Explosion
- Early game: ~150-200ms per turn
- Mid game: ~350-400ms per turn  
- Late game: ~600-950ms per turn
- **3-5x slowdown** as game progresses

**Likely causes**:
- BFS becomes more expensive with fragmented board
- More arrows = more expensive mobility calculations
- Tree depth increases = more evaluations per iteration

### 3. First Turn Anomaly
- Platform allows 2000ms for first turn
- Bot configured with 1400ms limit (600ms buffer)
- Yet turn 1 reaches 933ms (66% of budget)
- This is much higher than expected for initial move

### 4. Consistent Pattern Across Both Logs
- Both logs show identical timing progression
- TLE occurs at same game stage (turn 25-26)
- Same opponent behavior (consistent 3800ms per turn)
- Suggests this is deterministic, not random variation

---

## Questions for DeepSeek

### Critical Diagnostic Questions

1. **Where is the unaccounted time being spent?**
   - If MCTS loop exits at 550ms (700ms - 150ms), why does total reach 1000ms?
   - Is there 450ms overhead somewhere?
   - Could board copying, move selection, or I/O be that expensive?

2. **Is the time limit being applied correctly?**
   - The time check happens at loop start and before evaluation
   - Are there any operations that bypass these checks?
   - Could compiler optimizations be affecting timing measurements?

3. **Why does evaluation cost grow 3-5x in late game?**
   - BFS is O(V+E) where V=64, should be relatively constant
   - Mobility calculation visits more cells, but still bounded
   - Is there a performance cliff we're hitting?

4. **Should we use adaptive time management?**
   - Track actual iteration costs with exponential moving average
   - Stop when: `elapsed + predicted_iteration_cost > limit`
   - Would this be more reliable than fixed safety buffers?

5. **Are there more aggressive BFS optimizations?**
   - Can we cache BFS results for similar positions?
   - Should we use incremental BFS updates?
   - Can we reduce BFS frequency in late game?

### Solution Direction Questions

6. **Should we increase time limits closer to platform max?**
   - Use 1.8s first turn (vs 2.0s limit) = 200ms buffer
   - Use 0.85s regular (vs 1.0s limit) = 150ms buffer
   - Risk: Less safety margin but more MCTS iterations

7. **Should we reduce safety buffer threshold?**
   - Current: `time_limit - 0.15` (150ms reserve)
   - Try: `time_limit - 0.25` (250ms reserve)
   - Trade-off: Fewer iterations but safer timing

8. **Is there a critical evaluation that should be skipped in late game?**
   - Can we simplify evaluation when time is very low?
   - Use lightweight heuristic instead of full BFS?
   - Reduce BFS depth or mobility calculation scope?

---

## Additional Context

### Bot Architecture
- **MCTS**: Monte Carlo Tree Search with UCB1 selection
- **Evaluation**: 5-component function (BFS territory, mobility, position)
- **Board Representation**: Bitboards (3x uint64_t)
- **Memory Management**: std::deque<MCTSNode> for pointer stability
- **Move Ordering**: Centrality + arrow proximity (root node only)

### Performance Characteristics
- **Early game**: 12k-32k MCTS iterations per turn (~200ms)
- **Late game**: Unknown iterations (times out before completion)
- **BFS cost**: 2 calls per evaluation (player + opponent)
- **Mobility cost**: 1 call per evaluation

### Code Sections Referenced
- **Time limit constants**: Lines 568-569
- **Main MCTS loop**: Lines 502-546
- **Time check**: Lines 504-505
- **Mid-iteration safety**: Lines 515-518
- **Evaluation call**: Line 522

---

## What We Need

### Immediate Goal
Identify why the bot exceeds 1000ms despite 700ms limit + 150ms safety buffer, and provide a solution that:
1. Guarantees no TLE on Botzone
2. Maximizes MCTS iterations within time budget
3. Handles late-game performance degradation

### Acceptable Trade-offs
- Willing to sacrifice MCTS iterations for timing safety
- Can simplify late-game evaluation if needed
- Open to architectural changes (adaptive timing, caching, etc.)

### Success Criteria
- Bot completes 40+ turn games without TLE
- Average turn time: 500-800ms (good safety margin)
- Late game timing stable (no progressive degradation)
- First turn timing predictable and safe

---

## Files Referenced

**Will be provided separately**:
- `bots/bot002.cpp` - Complete source code
- `logs/botzone_debug/still_tle.json` - Latest TLE log after attempted fix
- `logs/botzone_debug/tle.log` - Original TLE log before fix

**Supporting documentation**:
- `docs/bot_implementation/bot002_tle_fix.md` - Previous fix attempt details
- `docs/reference/deepseek/optimization_plan_from_ds.md` - Original optimization plan

---

## Request Summary

We need DeepSeek's expertise to:

1. **Diagnose** why 700ms limit + 150ms buffer results in 1000ms TLE
2. **Identify** the source of unaccounted time (~300-450ms)
3. **Explain** why late-game timing degrades 3-5x
4. **Provide** a robust solution with guaranteed timing safety
5. **Suggest** optimizations for late-game BFS/evaluation if applicable

Thank you for your assistance in resolving this critical bug!
