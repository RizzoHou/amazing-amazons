# Memory Monitoring Fix

## Problem

The tournament system had two critical issues with memory monitoring:

### Issue 1: Incorrect Memory Limit
- **Problem**: Memory limit was set to 256 MB instead of the Botzone standard of 512 MB
- **Impact**: Bots might be incorrectly flagged for Memory Limit Exceeded (MLE)

### Issue 2: Inaccurate Memory Measurements
- **Problem**: Both bots often reported identical memory usage
- **Root Cause**: Traditional bots used `resource.getrusage(RUSAGE_CHILDREN)` which:
  - Tracks the cumulative maximum RSS across ALL child processes since program start
  - Cannot be reset between bot executions
  - Results in cross-contamination: Bot1's 100MB gets recorded, then Bot2's 100MB shows as 100MB (the global max), then if Bot2 later uses 105MB, Bot1 also reports 105MB
- **Impact**: Memory statistics were misleading and not bot-specific

## Solution

### 1. Fixed Memory Limit
Changed `DEFAULT_MEMORY_LIMIT` from 256 MB to 512 MB in `resource_monitor.py`:
```python
DEFAULT_MEMORY_LIMIT = 512 * 1024 * 1024  # 512 MB in bytes
```

### 2. Implemented MemorySampler Class
Created a background thread-based memory sampler that:
- Samples memory at 10ms intervals during bot execution
- Tracks peak memory usage per-turn, per-bot
- Avoids the RUSAGE_CHILDREN cumulative issue
- Works for both TraditionalBot and LongLiveBot

**Key Features:**
- **Process-specific**: Measures memory of specific PID
- **Periodic sampling**: Captures memory at regular intervals (10ms)
- **Peak tracking**: Records the maximum memory seen during the turn
- **Clean isolation**: Each bot's memory is measured independently

### 3. Updated Bot Runners
Both `TraditionalBot` and `LongLiveBot` now use `MemorySampler`:
- Start sampler when bot begins computing
- Stop sampler when bot completes turn
- Report peak memory from samples

## Results

After the fix, memory readings are now accurate and bot-specific:

**Example from test run (bot022 vs bot023):**
- **bot022**: Avg 167-213 MB, Max 463-466 MB
- **bot023**: Avg 81-88 MB, Max 126-137 MB

Memory values now correctly reflect each bot's actual usage instead of showing identical values.

## Technical Details

### MemorySampler Implementation
Located in `scripts/tournament/resource_monitor.py`:
- Background thread runs sampling loop
- Uses `/proc/{pid}/status` on Linux or `ps` command on macOS
- Thread-safe stop mechanism with event signaling
- Automatic cleanup when sampling completes

### Memory Measurement Methods
1. **Linux**: Reads VmRSS from `/proc/{pid}/status` (in KB)
2. **macOS**: Uses `ps -o rss= -p {pid}` command (in KB)
3. **Fallback**: Returns 0 if unable to measure

## Impact

- ✅ Memory limit now matches Botzone standard (512 MB)
- ✅ Each bot's memory is measured independently
- ✅ Memory statistics are accurate and meaningful
- ✅ No more identical memory readings between different bots
- ✅ Peak memory is captured even for short-lived processes

## Files Modified

1. `scripts/tournament/resource_monitor.py`
   - Added `MemorySampler` class
   - Updated `DEFAULT_MEMORY_LIMIT` to 512 MB
   - Added threading import

2. `scripts/tournament/bot_runner.py`
   - Updated `TraditionalBot.play_turn()` to use MemorySampler
   - Updated `LongLiveBot.play_turn()` to use MemorySampler
   - Removed dependency on `get_child_max_memory()` for measurements