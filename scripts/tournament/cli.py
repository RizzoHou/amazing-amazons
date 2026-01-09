#!/usr/bin/env python
"""
Command-line interface for the tournament system.

Provides commands for running matches, tournaments, tests, and compiling bots.

Features:
- Support for both long-live and traditional bots
- Configurable time/memory limits
- Unlimited mode for measuring actual resource usage
- Game analysis and report generation
"""

import argparse
import sys
import os
from typing import List, Optional

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
    memory_limit: int = 256 * 1024 * 1024,
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


def run_tournament(
    bot_names: List[str],
    verbose: bool = True,
    unlimited: bool = False,
    generate_report: bool = True,
    first_turn_time: float = 2.0,
    turn_time: float = 1.0,
    memory_limit: int = 256 * 1024 * 1024
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
  
  %(prog)s tournament bot010 bot014 bot015        # Run round-robin tournament
  %(prog)s tournament bot003 bot010 --unlimited   # Tournament without limits
  
  %(prog)s test bot015                            # Test traditional bot support
  %(prog)s compile bot015                         # Compile a bot
  
Bot Types:
  - long_live: Bots using >>>BOTZONE_REQUEST_KEEP_RUNNING<<< (e.g., bot010)
  - traditional: Bots that exit after each turn (e.g., bot015)
  
Time Limits (default Botzone):
  - First turn: 2 seconds
  - Other turns: 1 second
  - Memory: 256 MB
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
    match_parser.add_argument("--memory", type=int, default=256,
                             help="Memory limit in MB (default: 256)")
    match_parser.add_argument("--bot1-type", choices=['long_live', 'traditional'],
                             help="Force bot1 type (default: auto-detect)")
    match_parser.add_argument("--bot2-type", choices=['long_live', 'traditional'],
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
    tournament_parser.add_argument("--memory", type=int, default=256,
                                  help="Memory limit in MB (default: 256)")
    
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
