#!/usr/bin/env python3
"""
Analyze bot010 turn cycle logs to identify late game slowdown patterns.
Focuses on non-search operations like advance_root().
"""

import sys
import os
import glob
from collections import defaultdict
import statistics

def analyze_turn_cycle_log(log_path):
    """Analyze a turn cycle log file for timing patterns."""
    print(f"Analyzing turn cycle log: {log_path}")
    
    # Parse log data
    turn_data = defaultdict(lambda: defaultdict(float))  # turn_number -> phase -> time
    turn_phases = defaultdict(list)  # turn_number -> list of phases in order
    
    with open(log_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split(',')
            if len(parts) < 5:
                continue
            
            try:
                turn_num = int(parts[1])
                phase = parts[2]
                phase_time = float(parts[3])
                cumulative_time = float(parts[4])
                
                # Store phase time
                turn_data[turn_num][phase] = phase_time
                turn_phases[turn_num].append(phase)
                
            except (ValueError, IndexError) as e:
                # Skip malformed lines
                continue
    
    if not turn_data:
        print("  No valid data found in log file")
        return
    
    # Filter out turn 0 (initialization)
    regular_turns = [t for t in turn_data.keys() if t > 0]
    if not regular_turns:
        print("  No regular turns found (only initialization)")
        return
    
    print(f"\nFound data for {len(regular_turns)} regular turns (excluding initialization)")
    
    # Analyze key phases
    key_phases = [
        'SEARCH_COMPLETE',
        'ADVANCE_ROOT_OPP',
        'ADVANCE_ROOT_SELF',
        'INPUT_PARSING',
        'BOARD_UPDATE_OPP',
        'BOARD_UPDATE_SELF',
        'OUTPUT_GENERATION'
    ]
    
    # Collect data for each phase across turns
    phase_times = defaultdict(list)  # phase -> list of times across turns
    
    for turn_num in sorted(regular_turns):
        for phase in key_phases:
            if phase in turn_data[turn_num]:
                phase_times[phase].append((turn_num, turn_data[turn_num][phase]))
    
    # Calculate statistics for each phase
    print(f"\nPhase timing analysis (average time in seconds):")
    print(f"{'Phase':<20} {'Avg Time':>10} {'Max Time':>10} {'Late/Avg Ratio':>15} {'Trend':>10}")
    print("-" * 75)
    
    for phase in key_phases:
        if phase not in phase_times or len(phase_times[phase]) < 3:
            continue
        
        times = [t for _, t in phase_times[phase]]
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        # Calculate late game average (last 10 turns)
        late_turns = [t for turn_num, t in phase_times[phase] if turn_num > max(regular_turns) - 10]
        if late_turns:
            late_avg = statistics.mean(late_turns)
            late_ratio = late_avg / avg_time if avg_time > 0 else 1.0
        else:
            late_avg = 0
            late_ratio = 1.0
        
        # Determine trend
        if late_ratio > 1.5:
            trend = "↑↑ SLOWDOWN"
        elif late_ratio > 1.2:
            trend = "↑ SLOWING"
        elif late_ratio < 0.8:
            trend = "↓ SPEEDUP"
        elif late_ratio < 0.9:
            trend = "↓ SPEEDING"
        else:
            trend = "→ STABLE"
        
        print(f"{phase:<20} {avg_time:>10.6f} {max_time:>10.6f} {late_ratio:>15.2f} {trend:>10}")
    
    # Analyze total turn time (excluding search)
    print(f"\nNon-search operations analysis:")
    print(f"{'Turn':>6} {'Total Non-Search':>16} {'Search Time':>12} {'Non-Search %':>12}")
    print("-" * 60)
    
    non_search_times = []
    search_times = []
    
    for turn_num in sorted(regular_turns):
        total_non_search = 0
        search_time = 0
        
        for phase, time in turn_data[turn_num].items():
            if phase == 'SEARCH_COMPLETE':
                search_time = time
            elif phase not in ['TURN_INCREMENT', 'KEEP_RUNNING_SENT']:  # Skip trivial phases
                total_non_search += time
        
        if search_time > 0:
            non_search_pct = (total_non_search / (search_time + total_non_search)) * 100
            non_search_times.append(total_non_search)
            search_times.append(search_time)
            
            print(f"{turn_num:>6} {total_non_search:>16.6f} {search_time:>12.6f} {non_search_pct:>11.1f}%")
    
    if non_search_times and search_times:
        avg_non_search = statistics.mean(non_search_times)
        avg_search = statistics.mean(search_times)
        avg_pct = (avg_non_search / (avg_search + avg_non_search)) * 100
        
        print(f"\nSummary:")
        print(f"  Average search time: {avg_search:.6f}s")
        print(f"  Average non-search time: {avg_non_search:.6f}s")
        print(f"  Non-search percentage: {avg_pct:.1f}% of total turn time")
        
        # Check for late game increase in non-search time
        early_turns = [t for i, t in enumerate(non_search_times) if i < len(non_search_times) // 3]
        late_turns = [t for i, t in enumerate(non_search_times) if i >= 2 * len(non_search_times) // 3]
        
        if early_turns and late_turns:
            early_avg = statistics.mean(early_turns)
            late_avg = statistics.mean(late_turns)
            increase_pct = ((late_avg - early_avg) / early_avg) * 100 if early_avg > 0 else 0
            
            print(f"\nLate game non-search time change:")
            print(f"  Early game (first {len(early_turns)} turns): {early_avg:.6f}s")
            print(f"  Late game (last {len(late_turns)} turns): {late_avg:.6f}s")
            print(f"  Change: {increase_pct:+.1f}%")
            
            if increase_pct > 20:
                print(f"  ⚠️  Significant late game increase in non-search operations!")
            elif increase_pct > 10:
                print(f"  ⚠️  Moderate late game increase in non-search operations")
    
    # Identify the most expensive non-search operations
    print(f"\nMost expensive non-search operations (average time):")
    non_search_phases = []
    
    for phase in key_phases:
        if phase == 'SEARCH_COMPLETE':
            continue
        if phase in phase_times and phase_times[phase]:
            times = [t for _, t in phase_times[phase]]
            avg_time = statistics.mean(times)
            if avg_time > 0.001:  # Only show operations taking >1ms
                non_search_phases.append((phase, avg_time))
    
    # Sort by average time (descending)
    non_search_phases.sort(key=lambda x: x[1], reverse=True)
    
    for phase, avg_time in non_search_phases[:5]:  # Top 5
        print(f"  {phase:<20}: {avg_time:.6f}s ({avg_time*1000:.2f}ms)")

def main():
    """Main analysis function."""
    logs_dir = "logs"
    
    # Find all turn cycle log files
    log_pattern = os.path.join(logs_dir, "bot010_turn_cycle_log_*.txt")
    log_files = glob.glob(log_pattern)
    
    if not log_files:
        print(f"No turn cycle log files found matching pattern: {log_pattern}")
        return 1
    
    print(f"Found {len(log_files)} turn cycle log file(s)")
    
    # Analyze each log file
    for log_file in sorted(log_files):
        print("\n" + "="*80)
        analyze_turn_cycle_log(log_file)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())