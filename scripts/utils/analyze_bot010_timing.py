#!/usr/bin/env python3
"""
Analyze bot010 timing log to identify late game slowdown patterns.
"""

import sys
import os
import glob
from collections import defaultdict
import statistics

def analyze_log_file(log_path):
    """Analyze a single log file for timing patterns."""
    print(f"Analyzing log file: {log_path}")
    
    # Parse log data
    turn_data = defaultdict(list)  # turn_number -> list of (iterations, time)
    final_results = {}  # turn_number -> final data
    
    with open(log_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split(',')
            if len(parts) < 5:
                continue
            
            try:
                turn_str = parts[1]
                if turn_str == 'FINAL':
                    # Final result line
                    turn_num = int(parts[0].split('T')[0].split('-')[-1])  # Extract from timestamp
                    total_time = float(parts[3])
                    total_iterations = int(parts[4])
                    time_limit = float(parts[5]) if len(parts) > 5 else 0.88
                    turn_type = parts[6] if len(parts) > 6 else "NORMAL"
                    
                    final_results[turn_num] = {
                        'total_time': total_time,
                        'total_iterations': total_iterations,
                        'time_limit': time_limit,
                        'turn_type': turn_type,
                        'iterations_per_second': total_iterations / total_time if total_time > 0 else 0
                    }
                else:
                    # Regular log line (every 1000 iterations)
                    turn_num = int(turn_str)
                    iterations = int(parts[2])
                    elapsed_time = float(parts[3])
                    
                    turn_data[turn_num].append((iterations, elapsed_time))
            except (ValueError, IndexError) as e:
                # Skip malformed lines
                continue
    
    if not turn_data:
        print("  No valid data found in log file")
        return
    
    # Analyze each turn
    print(f"\nFound data for {len(turn_data)} turns")
    
    # Calculate iterations per second for each turn
    turn_stats = {}
    for turn_num, data_points in turn_data.items():
        if len(data_points) < 2:
            continue
        
        # Calculate average iterations per second for this turn
        # Use first and last data point to get overall rate
        first_iter, first_time = data_points[0]
        last_iter, last_time = data_points[-1]
        
        total_iterations = last_iter - first_iter
        total_time = last_time - first_time
        
        if total_time > 0:
            ips = total_iterations / total_time
            turn_stats[turn_num] = {
                'iterations_per_second': ips,
                'total_iterations': total_iterations,
                'total_time': total_time,
                'data_points': len(data_points)
            }
    
    # Sort turns by turn number
    sorted_turns = sorted(turn_stats.keys())
    
    if not sorted_turns:
        print("  Not enough data for analysis")
        return
    
    print(f"\nTurn-by-turn performance analysis:")
    print(f"{'Turn':>6} {'Iter/sec':>12} {'Total Iter':>12} {'Time (s)':>10} {'Data Pts':>10}")
    print("-" * 60)
    
    early_turns = []
    mid_turns = []
    late_turns = []
    
    for turn_num in sorted_turns:
        stats = turn_stats[turn_num]
        ips = stats['iterations_per_second']
        total_iter = stats['total_iterations']
        total_time = stats['total_time']
        data_pts = stats['data_points']
        
        print(f"{turn_num:>6} {ips:>12.0f} {total_iter:>12} {total_time:>10.3f} {data_pts:>10}")
        
        # Categorize turns
        if turn_num <= 10:
            early_turns.append(ips)
        elif turn_num <= 20:
            mid_turns.append(ips)
        else:
            late_turns.append(ips)
    
    # Calculate averages
    print(f"\nPerformance summary:")
    if early_turns:
        print(f"  Early turns (1-10): {statistics.mean(early_turns):.0f} iter/sec (n={len(early_turns)})")
    if mid_turns:
        print(f"  Mid turns (11-20): {statistics.mean(mid_turns):.0f} iter/sec (n={len(mid_turns)})")
    if late_turns:
        print(f"  Late turns (21+): {statistics.mean(late_turns):.0f} iter/sec (n={len(late_turns)})")
    
    # Check for slowdown
    if early_turns and late_turns:
        early_avg = statistics.mean(early_turns)
        late_avg = statistics.mean(late_turns)
        slowdown = (early_avg - late_avg) / early_avg * 100
        
        print(f"\nSlowdown analysis:")
        print(f"  Early game: {early_avg:.0f} iter/sec")
        print(f"  Late game: {late_avg:.0f} iter/sec")
        print(f"  Slowdown: {slowdown:.1f}%")
        
        if slowdown > 10:
            print(f"  ⚠️  Significant slowdown detected ({slowdown:.1f}%)")
        elif slowdown > 5:
            print(f"  ⚠️  Moderate slowdown detected ({slowdown:.1f}%)")
        else:
            print(f"  ✓ Minimal slowdown ({slowdown:.1f}%)")
    
    # Analyze final results
    if final_results:
        print(f"\nFinal results per turn:")
        print(f"{'Turn':>6} {'Type':>8} {'Iter/sec':>12} {'Iterations':>12} {'Time Used':>10} {'Time Limit':>10}")
        print("-" * 70)
        
        for turn_num in sorted(final_results.keys()):
            result = final_results[turn_num]
            ips = result['iterations_per_second']
            total_iter = result['total_iterations']
            time_used = result['total_time']
            time_limit = result['time_limit']
            turn_type = result['turn_type']
            
            time_usage_pct = (time_used / time_limit * 100) if time_limit > 0 else 0
            
            print(f"{turn_num:>6} {turn_type:>8} {ips:>12.0f} {total_iter:>12} {time_used:>10.3f} {time_limit:>10.3f}", end="")
            
            if time_usage_pct > 95:
                print(f"  ⚠️  {time_usage_pct:.1f}% of time limit")
            elif time_usage_pct > 80:
                print(f"  ⚠️  {time_usage_pct:.1f}% of time limit")
            else:
                print(f"  ✓ {time_usage_pct:.1f}% of time limit")

def main():
    """Main analysis function."""
    logs_dir = "logs"
    
    # Find all bot010 log files
    log_pattern = os.path.join(logs_dir, "bot010_time_log_*.txt")
    log_files = glob.glob(log_pattern)
    
    if not log_files:
        print(f"No log files found matching pattern: {log_pattern}")
        return 1
    
    print(f"Found {len(log_files)} log file(s)")
    
    # Analyze each log file
    for log_file in sorted(log_files):
        print("\n" + "="*80)
        analyze_log_file(log_file)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())