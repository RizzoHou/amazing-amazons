#!/usr/bin/env python
"""
Command-line interface for the tournament system.

Provides commands for running matches, tournaments, tests, profiling, and compiling bots.

Features:
- Support for both long-live and traditional bots
- Configurable time/memory limits
- Unlimited mode for measuring actual resource usage
- Game analysis and report generation
- Profile mode for detailed per-turn time/memory analysis
"""

import argparse
import sys
import os
import csv
import json
import statistics
from datetime import datetime
from typing import List, Optional, Dict, Any

from .game_engine import GameEngine, GameResult, GameEndReason
from .bot_runner import BotType
from .resource_monitor import ResourceMonitor
from .game_analyzer import GameAnalyzer, print_game_analysis
from .utils import compile_bot, bot_exists, get_bot_path


def run_match(
    bot1_name: str,
    bot2_name: str,
    verbose: bool = True,
    unlimited: bool = False,
    analyze: bool = False,
    save_result: bool = False,
    generate_report: bool = False,
    first_turn_time: float = 2.0,
    turn_time: float = 1.0,
    memory_limit: int = 512 * 1024 * 1024,
    bot1_type: Optional[str] = None,
    bot2_type: Optional[str] = None
) -> Optional[GameResult]:
    """
    Run a single match between two bots.
    
    Args:
        bot1_name: Name of first bot (Black)
        bot2_name: Name of second bot (White)
        verbose: Whether to print detailed output
        unlimited: If True, don't enforce limits (measurement only)
        analyze: If True, print detailed analysis
        save_result: If True, save result to JSON
        generate_report: If True, generate markdown report
        first_turn_time: Time limit for first turn (seconds)
        turn_time: Time limit for subsequent turns (seconds)
        memory_limit: Memory limit in bytes
        bot1_type: Force bot type ('long_live', 'traditional', or None for auto)
        bot2_type: Force bot type ('long_live', 'traditional', or None for auto)
    
    Returns:
        GameResult if match completed, None if setup failed
    """
    # Check if bots exist, compile if needed
    for bot_name in [bot1_name, bot2_name]:
        if not bot_exists(bot_name):
            if not compile_bot(bot_name):
                print(f"✗ Cannot run match: {bot_name} compilation failed")
                return None
    
    bot1_path = get_bot_path(bot1_name)
    bot2_path = get_bot_path(bot2_name)
    
    if verbose:
        print("=" * 60)
        print(f"Match: {bot1_name} (Black) vs {bot2_name} (White)")
        if unlimited:
            print("Mode: UNLIMITED (no enforcement, measurement only)")
        else:
            print(f"Time limits: {first_turn_time}s (first), {turn_time}s (other)")
            print(f"Memory limit: {memory_limit // (1024*1024)} MB")
        print("=" * 60)
    
    # Create resource monitor
    resource_monitor = ResourceMonitor(
        first_turn_time=first_turn_time,
        turn_time=turn_time,
        memory_limit=memory_limit,
        enforce_limits=not unlimited
    )
    
    # Parse bot types
    b1_type = _parse_bot_type(bot1_type)
    b2_type = _parse_bot_type(bot2_type)
    
    # Create and run game
    engine = GameEngine(
        bot1_path, bot2_path,
        bot1_name, bot2_name,
        resource_monitor=resource_monitor,
        verbose=verbose,
        bot1_type=b1_type,
        bot2_type=b2_type
    )
    
    result = engine.play()
    
    # Post-game analysis
    if analyze:
        print_game_analysis(result)
    
    # Save results
    analyzer = GameAnalyzer()
    
    if save_result:
        filepath = analyzer.save_game_result(result)
        if verbose:
            print(f"\n✓ Result saved to: {filepath}")
    
    if generate_report:
        filepath = analyzer.generate_game_report(result)
        if verbose:
            print(f"✓ Report saved to: {filepath}")
    
    # Print summary
    if verbose:
        if result.winner:
            print(f"\n✓ Match completed: {result.winner} wins ({result.end_reason.value})")
        else:
            print(f"\n✗ Match ended without winner ({result.end_reason.value})")
    
    return result


def run_series(
    bot1_name: str,
    bot2_name: str,
    num_matches: int = 10,
    bot1_black_count: Optional[int] = None,
    verbose: bool = True,
    unlimited: bool = False,
    generate_report: bool = False,
    first_turn_time: float = 2.0,
    turn_time: float = 1.0,
    memory_limit: int = 512 * 1024 * 1024,
    bot1_type: Optional[str] = None,
    bot2_type: Optional[str] = None
) -> bool:
    """
    Run a series of matches between two bots with configurable color assignments.
    
    Args:
        bot1_name: Name of first bot
        bot2_name: Name of second bot
        num_matches: Total number of matches to run
        bot1_black_count: Number of matches where bot1 plays Black (default: half)
        verbose: Whether to print detailed output
        unlimited: If True, don't enforce limits
        generate_report: If True, generate series report
        first_turn_time: Time limit for first turn
        turn_time: Time limit for other turns
        memory_limit: Memory limit in bytes
        bot1_type: Force bot1 type
        bot2_type: Force bot2 type
    
    Returns:
        True if series completed successfully, False otherwise
    """
    # Check and compile both bots
    for bot_name in [bot1_name, bot2_name]:
        if not bot_exists(bot_name):
            if not compile_bot(bot_name):
                print(f"✗ Cannot run series: {bot_name} compilation failed")
                return False
    
    # Calculate color distribution
    if bot1_black_count is None:
        bot1_black_count = num_matches // 2
    
    bot1_white_count = num_matches - bot1_black_count
    
    if bot1_black_count < 0 or bot1_white_count < 0:
        print(f"✗ Invalid color distribution: bot1_black={bot1_black_count}, total={num_matches}")
        return False
    
    if verbose:
        print("=" * 60)
        print(f"Series: {bot1_name} vs {bot2_name}")
        print(f"Total matches: {num_matches}")
        print(f"  {bot1_name} as Black: {bot1_black_count}")
        print(f"  {bot1_name} as White: {bot1_white_count}")
        if unlimited:
            print("Mode: UNLIMITED (no enforcement)")
        else:
            print(f"Time limits: {first_turn_time}s / {turn_time}s")
        print("=" * 60)
    
    # Track results
    results: List[GameResult] = []
    stats = {
        bot1_name: {"wins": 0, "losses": 0, "wins_as_black": 0, "wins_as_white": 0},
        bot2_name: {"wins": 0, "losses": 0, "wins_as_black": 0, "wins_as_white": 0}
    }
    
    # Schedule matches: first bot1_black_count matches with bot1 as Black
    match_schedule = []
    for _ in range(bot1_black_count):
        match_schedule.append((bot1_name, bot2_name))  # bot1 is Black
    for _ in range(bot1_white_count):
        match_schedule.append((bot2_name, bot1_name))  # bot2 is Black (bot1 is White)
    
    # Run matches sequentially
    for match_num, (black_bot, white_bot) in enumerate(match_schedule, 1):
        if verbose:
            print(f"\n{'='*40}")
            print(f"Match {match_num}/{num_matches}: {black_bot} (Black) vs {white_bot} (White)")
            print(f"{'='*40}")
        
        result = run_match(
            black_bot, white_bot,
            verbose=verbose,
            unlimited=unlimited,
            analyze=False,
            save_result=False,
            generate_report=False,
            first_turn_time=first_turn_time,
            turn_time=turn_time,
            memory_limit=memory_limit,
            bot1_type=bot1_type if black_bot == bot1_name else bot2_type,
            bot2_type=bot2_type if black_bot == bot1_name else bot1_type
        )
        
        if result:
            results.append(result)
            
            # Update stats
            if result.winner:
                winner = result.winner
                loser = result.loser
                is_winner_black = (winner == black_bot)
                
                stats[winner]["wins"] += 1
                stats[loser]["losses"] += 1
                
                if is_winner_black:
                    stats[winner]["wins_as_black"] += 1
                else:
                    stats[winner]["wins_as_white"] += 1
        
        # Print running stats
        if verbose:
            print(f"\n  Running: {bot1_name} {stats[bot1_name]['wins']}-{stats[bot1_name]['losses']} {bot2_name}")
    
    # Generate report if requested
    if generate_report and results:
        analyzer = GameAnalyzer()
        filepath = analyzer.generate_tournament_report(
            results,
            tournament_name=f"Series: {bot1_name} vs {bot2_name} ({num_matches} matches)"
        )
        if verbose:
            print(f"\n✓ Series report saved to: {filepath}")
    
    # Print final summary
    if verbose:
        print("\n" + "=" * 60)
        print("SERIES SUMMARY")
        print("=" * 60)
        print(f"\n{bot1_name}:")
        print(f"  Total: {stats[bot1_name]['wins']} wins, {stats[bot1_name]['losses']} losses")
        print(f"  As Black: {stats[bot1_name]['wins_as_black']} wins")
        print(f"  As White: {stats[bot1_name]['wins_as_white']} wins")
        print(f"\n{bot2_name}:")
        print(f"  Total: {stats[bot2_name]['wins']} wins, {stats[bot2_name]['losses']} losses")
        print(f"  As Black: {stats[bot2_name]['wins_as_black']} wins")
        print(f"  As White: {stats[bot2_name]['wins_as_white']} wins")
        
        # Win rate
        total_completed = stats[bot1_name]['wins'] + stats[bot1_name]['losses']
        if total_completed > 0:
            bot1_winrate = stats[bot1_name]['wins'] / total_completed * 100
            print(f"\nWin rate: {bot1_name} {bot1_winrate:.1f}% - {bot2_name} {100-bot1_winrate:.1f}%")
    
    return True


def run_tournament(
    bot_names: List[str],
    verbose: bool = True,
    unlimited: bool = False,
    generate_report: bool = True,
    first_turn_time: float = 2.0,
    turn_time: float = 1.0,
    memory_limit: int = 512 * 1024 * 1024
) -> bool:
    """
    Run a round-robin tournament between multiple bots.
    
    Args:
        bot_names: List of bot names
        verbose: Whether to print detailed output
        unlimited: If True, don't enforce limits
        generate_report: If True, generate tournament report
        first_turn_time: Time limit for first turn
        turn_time: Time limit for other turns
        memory_limit: Memory limit in bytes
    
    Returns:
        True if tournament completed successfully, False otherwise
    """
    # Check and compile all bots
    for bot_name in bot_names:
        if not bot_exists(bot_name):
            if not compile_bot(bot_name):
                print(f"✗ Cannot run tournament: {bot_name} compilation failed")
                return False
    
    if verbose:
        print("=" * 60)
        print(f"Tournament: {' vs '.join(bot_names)}")
        if unlimited:
            print("Mode: UNLIMITED (no enforcement)")
        else:
            print(f"Time limits: {first_turn_time}s / {turn_time}s")
        print("=" * 60)
    
    # Run round-robin matches
    results: List[GameResult] = []
    match_num = 0
    total_matches = len(bot_names) * (len(bot_names) - 1) // 2
    
    for i, bot1 in enumerate(bot_names):
        for j, bot2 in enumerate(bot_names):
            if i >= j:  # Skip self-play and duplicates
                continue
            
            match_num += 1
            if verbose:
                print(f"\n{'='*40}")
                print(f"Match {match_num}/{total_matches}: {bot1} vs {bot2}")
                print(f"{'='*40}")
            
            result = run_match(
                bot1, bot2,
                verbose=verbose,
                unlimited=unlimited,
                analyze=False,
                save_result=False,
                generate_report=False,
                first_turn_time=first_turn_time,
                turn_time=turn_time,
                memory_limit=memory_limit
            )
            
            if result:
                results.append(result)
    
    # Generate tournament report
    if generate_report and results:
        analyzer = GameAnalyzer()
        filepath = analyzer.generate_tournament_report(
            results,
            tournament_name=f"Tournament: {' vs '.join(bot_names)}"
        )
        if verbose:
            print(f"\n✓ Tournament report saved to: {filepath}")
    
    # Print summary
    if verbose:
        print("\n" + "=" * 60)
        print("TOURNAMENT SUMMARY")
        print("=" * 60)
        
        # Count wins
        wins = {}
        for bot in bot_names:
            wins[bot] = sum(1 for r in results if r.winner == bot)
        
        # Sort by wins
        sorted_bots = sorted(bot_names, key=lambda x: wins[x], reverse=True)
        
        for bot in sorted_bots:
            w = wins[bot]
            total = len([r for r in results if bot in [r.winner, r.loser]])
            print(f"  {bot}: {w} wins / {total} games")
    
    return True


def run_profile(
    bot1_name: str,
    bot2_name: str,
    unlimited: bool = True,
    output_csv: Optional[str] = None,
    output_json: Optional[str] = None,
    first_turn_time: float = 2.0,
    turn_time: float = 1.0,
    memory_limit: int = 512 * 1024 * 1024,
    bot1_type: Optional[str] = None,
    bot2_type: Optional[str] = None,
    profiles_dir: str = "profiles"
) -> Optional[GameResult]:
    """
    Run a profiling match between two bots with detailed per-turn time/memory tracking.
    
    This mode is designed for performance analysis and bottleneck identification.
    It records detailed metrics for each turn and exports them for analysis.
    
    Args:
        bot1_name: Name of first bot (Black)
        bot2_name: Name of second bot (White)
        unlimited: If True, don't enforce limits (recommended for accurate measurement)
        output_csv: Path to save CSV output (auto-generated if None)
        output_json: Path to save JSON output (None to skip JSON)
        first_turn_time: Time limit for first turn (seconds)
        turn_time: Time limit for subsequent turns (seconds)
        memory_limit: Memory limit in bytes
        bot1_type: Force bot type ('long_live', 'traditional', or None for auto)
        bot2_type: Force bot type ('long_live', 'traditional', or None for auto)
        profiles_dir: Directory to store profile outputs
    
    Returns:
        GameResult if match completed, None if setup failed
    """
    from .resource_monitor import TurnMetrics, format_time, format_bytes
    
    # Create profiles directory
    os.makedirs(profiles_dir, exist_ok=True)
    
    # Check if bots exist, compile if needed
    for bot_name in [bot1_name, bot2_name]:
        if not bot_exists(bot_name):
            if not compile_bot(bot_name):
                print(f"✗ Cannot run profile: {bot_name} compilation failed")
                return None
    
    bot1_path = get_bot_path(bot1_name)
    bot2_path = get_bot_path(bot2_name)
    
    # Print header
    print("=" * 80)
    print(f"PROFILE MATCH: {bot1_name} (Black) vs {bot2_name} (White)")
    print("=" * 80)
    if unlimited:
        print("Mode: UNLIMITED (measurement only - no time enforcement)")
    else:
        print(f"Mode: ENFORCED (first turn: {first_turn_time}s, other: {turn_time}s)")
    print(f"Memory limit: {memory_limit // (1024*1024)} MB")
    print("=" * 80)
    print()
    
    # Print table header
    print(f"{'Turn':<6} {'Player':<12} {'Move':<24} {'Time':<12} {'Memory':<12} {'Status':<10}")
    print("-" * 80)
    
    # Create resource monitor
    resource_monitor = ResourceMonitor(
        first_turn_time=first_turn_time,
        turn_time=turn_time,
        memory_limit=memory_limit,
        enforce_limits=not unlimited
    )
    
    # Parse bot types
    b1_type = _parse_bot_type(bot1_type)
    b2_type = _parse_bot_type(bot2_type)
    
    # Create and run game with custom verbose handler
    engine = GameEngine(
        bot1_path, bot2_path,
        bot1_name, bot2_name,
        resource_monitor=resource_monitor,
        verbose=False,  # We'll handle output ourselves
        bot1_type=b1_type,
        bot2_type=b2_type
    )
    
    result = engine.play()
    
    # Collect all per-turn metrics
    all_turn_data: List[Dict[str, Any]] = []
    bot1_turns = engine.bot1.get_turn_metrics()
    bot2_turns = engine.bot2.get_turn_metrics()
    
    # Combine and sort by turn number
    # Bot1 (Black) plays on odd turns: internal turn 1 -> game turn 1, internal turn 2 -> game turn 3
    # Bot2 (White) plays on even turns: internal turn 1 -> game turn 2, internal turn 2 -> game turn 4
    memory_limit_mb = memory_limit / (1024 * 1024)
    
    for metrics in bot1_turns:
        game_turn = metrics.turn_number * 2 - 1  # Black plays on odd turns
        all_turn_data.append({
            "turn": game_turn,
            "player": bot1_name,
            "move": result.moves[game_turn - 1] if game_turn <= len(result.moves) else "",
            "time_seconds": metrics.time_seconds,
            "memory_bytes": metrics.memory_bytes,
            "memory_mb": metrics.memory_bytes / (1024 * 1024),
            "memory_limit_mb": memory_limit_mb,
            "time_limit": metrics.time_limit,
            "is_first_turn": metrics.is_first_turn,
            "violation": metrics.violation.value
        })
    
    for metrics in bot2_turns:
        game_turn = metrics.turn_number * 2  # White plays on even turns
        all_turn_data.append({
            "turn": game_turn,
            "player": bot2_name,
            "move": result.moves[game_turn - 1] if game_turn <= len(result.moves) else "",
            "time_seconds": metrics.time_seconds,
            "memory_bytes": metrics.memory_bytes,
            "memory_mb": metrics.memory_bytes / (1024 * 1024),
            "memory_limit_mb": memory_limit_mb,
            "time_limit": metrics.time_limit,
            "is_first_turn": metrics.is_first_turn,
            "violation": metrics.violation.value
        })
    
    # Sort by turn number
    all_turn_data.sort(key=lambda x: x["turn"])
    
    # Print per-turn data
    for data in all_turn_data:
        move_str = data["move"][:22] + ".." if len(data["move"]) > 24 else data["move"]
        time_str = format_time(data["time_seconds"])
        mem_str = f"{data['memory_mb']:.1f} MB" if data["memory_bytes"] > 0 else "N/A"
        status = "OK" if data["violation"] == "none" else data["violation"].upper()
        
        print(f"{data['turn']:<6} {data['player']:<12} {move_str:<24} {time_str:<12} {mem_str:<12} {status:<10}")
    
    print("-" * 80)
    print()
    
    # Print statistical analysis for each bot
    for bot_name_stat, turns in [(bot1_name, bot1_turns), (bot2_name, bot2_turns)]:
        if not turns:
            continue
        
        times = [t.time_seconds for t in turns]
        memories = [t.memory_bytes for t in turns if t.memory_bytes > 0]
        
        # Separate first turn
        first_turn = [t for t in turns if t.is_first_turn]
        other_turns = [t for t in turns if not t.is_first_turn]
        other_times = [t.time_seconds for t in other_turns]
        
        print(f"=== TIMING ANALYSIS: {bot_name_stat} ===")
        print(f"Total turns:     {len(turns)}")
        
        if first_turn:
            print(f"First turn:      {format_time(first_turn[0].time_seconds)}")
        
        if other_times:
            avg_time = statistics.mean(other_times)
            print(f"Avg time:        {format_time(avg_time)}")
            
            if len(other_times) >= 2:
                median_time = statistics.median(other_times)
                stdev_time = statistics.stdev(other_times)
                print(f"Median time:     {format_time(median_time)}")
                print(f"Std dev:         {format_time(stdev_time)}")
            
            max_time = max(other_times)
            min_time = min(other_times)
            max_turn = [t.turn_number for t in other_turns if t.time_seconds == max_time][0]
            min_turn = [t.turn_number for t in other_turns if t.time_seconds == min_time][0]
            print(f"Max time:        {format_time(max_time)} (turn {max_turn})")
            print(f"Min time:        {format_time(min_time)} (turn {min_turn})")
            
            # Percentiles
            if len(other_times) >= 5:
                sorted_times = sorted(other_times)
                p95_idx = int(len(sorted_times) * 0.95)
                p99_idx = int(len(sorted_times) * 0.99)
                print(f"P95:             {format_time(sorted_times[p95_idx])}")
                print(f"P99:             {format_time(sorted_times[p99_idx])}")
        
        print(f"Total time:      {format_time(sum(times))}")
        
        if memories:
            print()
            print(f"=== MEMORY ANALYSIS: {bot_name_stat} ===")
            avg_mem = statistics.mean(memories)
            max_mem = max(memories)
            min_mem = min(memories)
            print(f"Avg memory:      {format_bytes(int(avg_mem))}")
            print(f"Max memory:      {format_bytes(max_mem)}")
            print(f"Min memory:      {format_bytes(min_mem)}")
        
        print()
    
    # Print game result
    print("=" * 80)
    if result.winner:
        print(f"RESULT: {result.winner} wins ({result.end_reason.value})")
    else:
        print(f"RESULT: No winner ({result.end_reason.value})")
    print(f"Total turns: {result.total_turns}")
    print("=" * 80)
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"profile_{bot1_name}_vs_{bot2_name}_{timestamp}"
    
    # Save CSV
    if output_csv is None:
        output_csv = os.path.join(profiles_dir, f"{base_filename}.csv")
    
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "turn", "player", "move", "time_seconds", "memory_bytes", 
            "memory_mb", "memory_limit_mb", "time_limit", "is_first_turn", "violation"
        ])
        writer.writeheader()
        writer.writerows(all_turn_data)
    
    print(f"\n✓ CSV profile saved to: {output_csv}")
    
    # Save JSON if requested
    if output_json:
        json_data = {
            "match": {
                "bot1": bot1_name,
                "bot2": bot2_name,
                "winner": result.winner,
                "loser": result.loser,
                "end_reason": result.end_reason.value,
                "total_turns": result.total_turns,
                "timestamp": datetime.now().isoformat()
            },
            "settings": {
                "unlimited": unlimited,
                "first_turn_time": first_turn_time,
                "turn_time": turn_time,
                "memory_limit": memory_limit
            },
            "turns": all_turn_data,
            "moves": result.moves,
            "statistics": {}
        }
        
        # Add statistics for each bot
        for bot_name_stat, turns in [(bot1_name, bot1_turns), (bot2_name, bot2_turns)]:
            if turns:
                times = [t.time_seconds for t in turns]
                other_times = [t.time_seconds for t in turns if not t.is_first_turn]
                memories = [t.memory_bytes for t in turns if t.memory_bytes > 0]
                
                stats = {
                    "total_turns": len(turns),
                    "total_time": sum(times),
                    "first_turn_time": turns[0].time_seconds if turns and turns[0].is_first_turn else None,
                }
                
                if other_times:
                    stats["avg_time"] = statistics.mean(other_times)
                    stats["max_time"] = max(other_times)
                    stats["min_time"] = min(other_times)
                    if len(other_times) >= 2:
                        stats["median_time"] = statistics.median(other_times)
                        stats["stdev_time"] = statistics.stdev(other_times)
                
                if memories:
                    stats["avg_memory"] = statistics.mean(memories)
                    stats["max_memory"] = max(memories)
                    stats["min_memory"] = min(memories)
                
                json_data["statistics"][bot_name_stat] = stats
        
        with open(output_json, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"✓ JSON profile saved to: {output_json}")
    
    return result


def _parse_bot_type(type_str: Optional[str]) -> Optional[BotType]:
    """Parse bot type string to BotType enum."""
    if type_str is None:
        return None
    if type_str.lower() in ['long_live', 'longlive', 'long-live']:
        return BotType.LONG_LIVE
    if type_str.lower() in ['traditional', 'trad', 'standard']:
        return BotType.TRADITIONAL
    return None


def run_test(test_name: str, verbose: bool = True) -> bool:
    """
    Run a specific test.
    
    Args:
        test_name: Name of test to run
        verbose: Whether to print detailed output
    
    Returns:
        True if test passed, False otherwise
    """
    if test_name == "bot002":
        return test_bot002(verbose)
    elif test_name == "bot000_vs_bot003":
        return test_bot000_vs_bot003(verbose)
    elif test_name == "bot015":
        return test_traditional_bot(verbose)
    else:
        print(f"✗ Unknown test: {test_name}")
        print("Available tests: bot002, bot000_vs_bot003, bot015")
        return False


def test_bot002(verbose: bool = True) -> bool:
    """Test bot002 self-play."""
    if verbose:
        print("\n" + "=" * 60)
        print("Test: bot002 self-play")
        print("=" * 60)
    
    result = run_match("bot002", "bot002", verbose=verbose, analyze=True)
    return result is not None


def test_bot000_vs_bot003(verbose: bool = True) -> bool:
    """Test bot000 vs bot003."""
    if verbose:
        print("\n" + "=" * 60)
        print("Test: bot000 vs bot003")
        print("=" * 60)
    
    result = run_match("bot000", "bot003", verbose=verbose, analyze=True)
    return result is not None and result.winner is not None


def test_traditional_bot(verbose: bool = True) -> bool:
    """Test traditional (non-long-live) bot like bot015."""
    if verbose:
        print("\n" + "=" * 60)
        print("Test: Traditional bot (bot015) vs Long-live bot (bot010)")
        print("=" * 60)
    
    # Force bot types to test mixed mode
    result = run_match(
        "bot015", "bot010",
        verbose=verbose,
        analyze=True,
        bot1_type="traditional",
        bot2_type="long_live"
    )
    return result is not None


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Amazons Tournament System - Run bot matches with resource monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s match bot010 bot015                    # Run a single match
  %(prog)s match bot010 bot015 --unlimited        # Run without time limits
  %(prog)s match bot010 bot015 --analyze          # Run with detailed analysis
  %(prog)s match bot010 bot015 --report           # Generate markdown report
  
  %(prog)s series bot021 bot022 -n 10             # Run 10 matches (5 Black, 5 White each)
  %(prog)s series bot021 bot022 -n 10 --bot1-black 8   # bot021 plays Black in 8 matches
  %(prog)s series bot021 bot022 -n 6 --report     # Run 6 matches with report
  
  %(prog)s tournament bot010 bot014 bot015        # Run round-robin tournament
  %(prog)s tournament bot003 bot010 --unlimited   # Tournament without limits
  
  %(prog)s profile bot026 bot027                  # Profile match with per-turn metrics
  %(prog)s profile bot026 bot027 --json           # Also save JSON output
  %(prog)s profile bot026 bot027 -o myprofile.csv # Custom output filename
  
  %(prog)s test bot015                            # Test traditional bot support
  %(prog)s compile bot015                         # Compile a bot
  
Bot Types:
  - long_live: Bots using >>>BOTZONE_REQUEST_KEEP_RUNNING<<< (e.g., bot010)
  - traditional: Bots that exit after each turn (e.g., bot015)
  
Time Limits (default Botzone):
  - First turn: 2 seconds
  - Other turns: 1 second
  - Memory: 512 MB
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Match command
    match_parser = subparsers.add_parser("match", help="Run a single match")
    match_parser.add_argument("bot1", help="First bot name (plays Black)")
    match_parser.add_argument("bot2", help="Second bot name (plays White)")
    match_parser.add_argument("--quiet", "-q", action="store_true", help="Reduce output")
    match_parser.add_argument("--unlimited", "-u", action="store_true",
                             help="Don't enforce time/memory limits (measurement only)")
    match_parser.add_argument("--analyze", "-a", action="store_true",
                             help="Print detailed post-game analysis")
    match_parser.add_argument("--save", "-s", action="store_true",
                             help="Save result to JSON file")
    match_parser.add_argument("--report", "-r", action="store_true",
                             help="Generate markdown report")
    match_parser.add_argument("--first-time", type=float, default=2.0,
                             help="Time limit for first turn (default: 2.0s)")
    match_parser.add_argument("--turn-time", type=float, default=1.0,
                             help="Time limit for other turns (default: 1.0s)")
    match_parser.add_argument("--memory", type=int, default=512,
                             help="Memory limit in MB (default: 512)")
    match_parser.add_argument("--bot1-type", choices=['long_live', 'traditional'],
                             help="Force bot1 type (default: auto-detect)")
    match_parser.add_argument("--bot2-type", choices=['long_live', 'traditional'],
                             help="Force bot2 type (default: auto-detect)")
    
    # Series command
    series_parser = subparsers.add_parser("series", help="Run multiple matches between two bots")
    series_parser.add_argument("bot1", help="First bot name")
    series_parser.add_argument("bot2", help="Second bot name")
    series_parser.add_argument("-n", "--matches", type=int, default=10,
                              help="Total number of matches (default: 10)")
    series_parser.add_argument("--bot1-black", type=int, default=None,
                              help="Number of matches where bot1 plays Black (default: half of total)")
    series_parser.add_argument("--quiet", "-q", action="store_true", help="Reduce output")
    series_parser.add_argument("--unlimited", "-u", action="store_true",
                              help="Don't enforce time/memory limits")
    series_parser.add_argument("--report", "-r", action="store_true",
                              help="Generate series report")
    series_parser.add_argument("--first-time", type=float, default=2.0,
                              help="Time limit for first turn (default: 2.0s)")
    series_parser.add_argument("--turn-time", type=float, default=1.0,
                              help="Time limit for other turns (default: 1.0s)")
    series_parser.add_argument("--memory", type=int, default=512,
                              help="Memory limit in MB (default: 512)")
    series_parser.add_argument("--bot1-type", choices=['long_live', 'traditional'],
                              help="Force bot1 type (default: auto-detect)")
    series_parser.add_argument("--bot2-type", choices=['long_live', 'traditional'],
                              help="Force bot2 type (default: auto-detect)")
    
    # Tournament command
    tournament_parser = subparsers.add_parser("tournament", help="Run a tournament")
    tournament_parser.add_argument("bots", nargs="+", help="Bot names")
    tournament_parser.add_argument("--quiet", "-q", action="store_true", help="Reduce output")
    tournament_parser.add_argument("--unlimited", "-u", action="store_true",
                                  help="Don't enforce time/memory limits")
    tournament_parser.add_argument("--no-report", action="store_true",
                                  help="Don't generate tournament report")
    tournament_parser.add_argument("--first-time", type=float, default=2.0,
                                  help="Time limit for first turn (default: 2.0s)")
    tournament_parser.add_argument("--turn-time", type=float, default=1.0,
                                  help="Time limit for other turns (default: 1.0s)")
    tournament_parser.add_argument("--memory", type=int, default=512,
                                  help="Memory limit in MB (default: 512)")
    
    # Profile command
    profile_parser = subparsers.add_parser("profile", 
        help="Run a profiling match with detailed per-turn time/memory tracking")
    profile_parser.add_argument("bot1", help="First bot name (plays Black)")
    profile_parser.add_argument("bot2", help="Second bot name (plays White)")
    profile_parser.add_argument("-o", "--output", dest="output_csv",
                               help="Path for CSV output (default: auto-generated in profiles/)")
    profile_parser.add_argument("--json", dest="output_json", nargs='?', const='auto',
                               help="Also save JSON output (optionally specify path)")
    profile_parser.add_argument("--enforced", "-e", action="store_true",
                               help="Enforce time limits (default: unlimited for accurate measurement)")
    profile_parser.add_argument("--first-time", type=float, default=2.0,
                               help="Time limit for first turn (default: 2.0s)")
    profile_parser.add_argument("--turn-time", type=float, default=1.0,
                               help="Time limit for other turns (default: 1.0s)")
    profile_parser.add_argument("--memory", type=int, default=512,
                               help="Memory limit in MB (default: 512)")
    profile_parser.add_argument("--bot1-type", choices=['long_live', 'traditional'],
                               help="Force bot1 type (default: auto-detect)")
    profile_parser.add_argument("--bot2-type", choices=['long_live', 'traditional'],
                               help="Force bot2 type (default: auto-detect)")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run a test")
    test_parser.add_argument("test_name", help="Test name (bot002, bot000_vs_bot003, bot015)")
    test_parser.add_argument("--quiet", "-q", action="store_true", help="Reduce output")
    
    # Compile command
    compile_parser = subparsers.add_parser("compile", help="Compile a bot")
    compile_parser.add_argument("bot_name", help="Bot name to compile")
    compile_parser.add_argument("--source", help="Path to source file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    verbose = not getattr(args, "quiet", False)
    
    try:
        if args.command == "match":
            result = run_match(
                args.bot1, args.bot2,
                verbose=verbose,
                unlimited=args.unlimited,
                analyze=args.analyze,
                save_result=args.save,
                generate_report=args.report,
                first_turn_time=args.first_time,
                turn_time=args.turn_time,
                memory_limit=args.memory * 1024 * 1024,
                bot1_type=args.bot1_type,
                bot2_type=args.bot2_type
            )
            return 0 if result and result.winner else 1
        
        elif args.command == "series":
            success = run_series(
                args.bot1, args.bot2,
                num_matches=args.matches,
                bot1_black_count=args.bot1_black,
                verbose=verbose,
                unlimited=args.unlimited,
                generate_report=args.report,
                first_turn_time=args.first_time,
                turn_time=args.turn_time,
                memory_limit=args.memory * 1024 * 1024,
                bot1_type=args.bot1_type,
                bot2_type=args.bot2_type
            )
            return 0 if success else 1
            
        elif args.command == "tournament":
            success = run_tournament(
                args.bots,
                verbose=verbose,
                unlimited=args.unlimited,
                generate_report=not args.no_report,
                first_turn_time=args.first_time,
                turn_time=args.turn_time,
                memory_limit=args.memory * 1024 * 1024
            )
            return 0 if success else 1
        
        elif args.command == "profile":
            # Handle JSON output path
            output_json = None
            if args.output_json:
                if args.output_json == 'auto':
                    # Auto-generate JSON path based on CSV path or default
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_json = os.path.join("profiles", f"profile_{args.bot1}_vs_{args.bot2}_{timestamp}.json")
                else:
                    output_json = args.output_json
            
            result = run_profile(
                args.bot1, args.bot2,
                unlimited=not args.enforced,
                output_csv=args.output_csv,
                output_json=output_json,
                first_turn_time=args.first_time,
                turn_time=args.turn_time,
                memory_limit=args.memory * 1024 * 1024,
                bot1_type=args.bot1_type,
                bot2_type=args.bot2_type
            )
            return 0 if result else 1
            
        elif args.command == "test":
            success = run_test(args.test_name, verbose)
            return 0 if success else 1
            
        elif args.command == "compile":
            source_path = getattr(args, "source", None)
            success = compile_bot(args.bot_name, source_path)
            return 0 if success else 1
            
    except KeyboardInterrupt:
        print("\n✗ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())