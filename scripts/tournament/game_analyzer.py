"""
Game Analyzer module for post-game analysis and report generation.

Provides comprehensive statistics and reports for games and tournaments.
"""

import json
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from .game_engine import GameResult, GameEndReason
from .resource_monitor import GameMetrics, format_time, format_bytes


@dataclass
class TournamentStats:
    """Statistics for a tournament (multiple games)."""
    bot_name: str
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    
    # Win reasons
    wins_by_no_moves: int = 0
    wins_by_timeout: int = 0
    wins_by_invalid_move: int = 0
    wins_by_crash: int = 0
    
    # Loss reasons
    losses_by_no_moves: int = 0
    losses_by_timeout: int = 0
    losses_by_invalid_move: int = 0
    losses_by_crash: int = 0
    
    # Timing stats (aggregated across all games)
    total_time: float = 0.0
    total_turns: int = 0
    avg_time_per_turn: float = 0.0
    max_time_single_turn: float = 0.0
    min_time_single_turn: float = float('inf')
    
    # Memory stats
    max_memory: int = 0
    avg_memory: int = 0
    
    @property
    def win_rate(self) -> float:
        if self.games_played == 0:
            return 0.0
        return self.wins / self.games_played * 100


class GameAnalyzer:
    """Analyzes game results and generates reports."""
    
    def __init__(self, results_dir: str = "results", reports_dir: str = "reports"):
        """
        Initialize game analyzer.
        
        Args:
            results_dir: Directory to save JSON results
            reports_dir: Directory to save reports
        """
        self.results_dir = results_dir
        self.reports_dir = reports_dir
        
        # Create directories if they don't exist
        os.makedirs(results_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)
    
    def analyze_game(self, result: GameResult) -> Dict[str, Any]:
        """
        Analyze a single game result.
        
        Args:
            result: GameResult from game engine
            
        Returns:
            Dictionary with analysis
        """
        analysis = {
            "winner": result.winner,
            "loser": result.loser,
            "end_reason": result.end_reason.value,
            "total_turns": result.total_turns,
            "bots": {}
        }
        
        # Analyze each bot
        for metrics in [result.bot1_metrics, result.bot2_metrics]:
            if metrics:
                bot_analysis = self._analyze_bot_metrics(metrics)
                analysis["bots"][metrics.bot_name] = bot_analysis
        
        return analysis
    
    def _analyze_bot_metrics(self, metrics: GameMetrics) -> Dict[str, Any]:
        """Analyze metrics for a single bot."""
        return {
            "total_turns": metrics.total_turns,
            "total_time": metrics.total_time,
            "first_turn_time": metrics.first_turn_time,
            "avg_time": metrics.avg_time,
            "max_time": metrics.max_time,
            "min_time": metrics.min_time if metrics.min_time != float('inf') else 0,
            "max_time_turn": metrics.max_time_turn,
            "min_time_turn": metrics.min_time_turn,
            "avg_memory_bytes": metrics.avg_memory,
            "max_memory_bytes": metrics.max_memory,
            "min_memory_bytes": metrics.min_memory,
        }
    
    def save_game_result(
        self,
        result: GameResult,
        filename: Optional[str] = None
    ) -> str:
        """
        Save game result to JSON file.
        
        Args:
            result: GameResult to save
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"game_{timestamp}.json"
        
        filepath = os.path.join(self.results_dir, filename)
        
        data = result.to_dict()
        data["timestamp"] = datetime.now().isoformat()
        data["analysis"] = self.analyze_game(result)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filepath
    
    def generate_game_report(
        self,
        result: GameResult,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate a markdown report for a single game.
        
        Args:
            result: GameResult to report
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to saved report
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"game_report_{timestamp}.md"
        
        filepath = os.path.join(self.reports_dir, filename)
        
        report_lines = [
            "# Game Analysis Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Game Summary",
            "",
            f"- **Winner:** {result.winner or 'None'}",
            f"- **Loser:** {result.loser or 'None'}",
            f"- **End Reason:** {result.end_reason.value}",
            f"- **Total Turns:** {result.total_turns}",
        ]
        
        if result.error_message:
            report_lines.extend([
                "",
                f"**Error:** {result.error_message}",
            ])
        
        # Add bot statistics
        for metrics in [result.bot1_metrics, result.bot2_metrics]:
            if metrics and metrics.total_turns > 0:
                report_lines.extend([
                    "",
                    f"## {metrics.bot_name} Statistics",
                    "",
                    "### Timing",
                    "",
                    f"| Metric | Value |",
                    f"|--------|-------|",
                    f"| First Turn Time | {format_time(metrics.first_turn_time)} |",
                    f"| Average Time (excl. first) | {format_time(metrics.avg_time)} |",
                    f"| Maximum Time | {format_time(metrics.max_time)} (turn {metrics.max_time_turn}) |",
                    f"| Minimum Time | {format_time(metrics.min_time) if metrics.min_time != float('inf') else 'N/A'} (turn {metrics.min_time_turn}) |",
                    f"| Total Time | {format_time(metrics.total_time)} |",
                ])
                
                if metrics.max_memory > 0:
                    report_lines.extend([
                        "",
                        "### Memory",
                        "",
                        f"| Metric | Value |",
                        f"|--------|-------|",
                        f"| Average Memory | {format_bytes(metrics.avg_memory)} |",
                        f"| Maximum Memory | {format_bytes(metrics.max_memory)} (turn {metrics.max_memory_turn}) |",
                        f"| Minimum Memory | {format_bytes(metrics.min_memory)} (turn {metrics.min_memory_turn}) |",
                    ])
        
        # Add move history (condensed)
        if result.moves:
            report_lines.extend([
                "",
                "## Move History",
                "",
                "```",
            ])
            for i, move in enumerate(result.moves, 1):
                player = "Black" if i % 2 == 1 else "White"
                report_lines.append(f"{i:3d}. [{player}] {move}")
            report_lines.append("```")
        
        report = '\n'.join(report_lines)
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        return filepath
    
    def aggregate_tournament_stats(
        self,
        results: List[GameResult]
    ) -> Dict[str, TournamentStats]:
        """
        Aggregate statistics for multiple games (tournament).
        
        Args:
            results: List of game results
            
        Returns:
            Dictionary mapping bot name to TournamentStats
        """
        stats: Dict[str, TournamentStats] = {}
        
        for result in results:
            # Update winner stats
            if result.winner:
                if result.winner not in stats:
                    stats[result.winner] = TournamentStats(bot_name=result.winner)
                
                s = stats[result.winner]
                s.games_played += 1
                s.wins += 1
                
                # Record win reason
                if result.end_reason == GameEndReason.NO_MOVES:
                    s.wins_by_no_moves += 1
                elif result.end_reason == GameEndReason.TIMEOUT:
                    s.wins_by_timeout += 1
                elif result.end_reason == GameEndReason.INVALID_MOVE:
                    s.wins_by_invalid_move += 1
                elif result.end_reason == GameEndReason.CRASH:
                    s.wins_by_crash += 1
            
            # Update loser stats
            if result.loser:
                if result.loser not in stats:
                    stats[result.loser] = TournamentStats(bot_name=result.loser)
                
                s = stats[result.loser]
                s.games_played += 1
                s.losses += 1
                
                # Record loss reason
                if result.end_reason == GameEndReason.NO_MOVES:
                    s.losses_by_no_moves += 1
                elif result.end_reason == GameEndReason.TIMEOUT:
                    s.losses_by_timeout += 1
                elif result.end_reason == GameEndReason.INVALID_MOVE:
                    s.losses_by_invalid_move += 1
                elif result.end_reason == GameEndReason.CRASH:
                    s.losses_by_crash += 1
            
            # Update timing stats from metrics
            for metrics in [result.bot1_metrics, result.bot2_metrics]:
                if metrics and metrics.bot_name:
                    if metrics.bot_name not in stats:
                        stats[metrics.bot_name] = TournamentStats(bot_name=metrics.bot_name)
                    
                    s = stats[metrics.bot_name]
                    s.total_time += metrics.total_time
                    s.total_turns += metrics.total_turns
                    
                    if metrics.max_time > s.max_time_single_turn:
                        s.max_time_single_turn = metrics.max_time
                    if metrics.min_time < s.min_time_single_turn and metrics.min_time > 0:
                        s.min_time_single_turn = metrics.min_time
                    if metrics.max_memory > s.max_memory:
                        s.max_memory = metrics.max_memory
        
        # Calculate averages
        for s in stats.values():
            if s.total_turns > 0:
                s.avg_time_per_turn = s.total_time / s.total_turns
        
        return stats
    
    def generate_tournament_report(
        self,
        results: List[GameResult],
        tournament_name: str = "Tournament",
        filename: Optional[str] = None
    ) -> str:
        """
        Generate a markdown report for a tournament.
        
        Args:
            results: List of game results
            tournament_name: Name of the tournament
            filename: Optional filename
            
        Returns:
            Path to saved report
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tournament_report_{timestamp}.md"
        
        filepath = os.path.join(self.reports_dir, filename)
        
        stats = self.aggregate_tournament_stats(results)
        
        report_lines = [
            f"# {tournament_name} Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Games:** {len(results)}",
            "",
            "## Standings",
            "",
            "| Bot | Games | Wins | Losses | Win Rate | Avg Time | Max Time |",
            "|-----|-------|------|--------|----------|----------|----------|",
        ]
        
        # Sort by wins descending
        sorted_stats = sorted(stats.values(), key=lambda x: x.wins, reverse=True)
        
        for s in sorted_stats:
            report_lines.append(
                f"| {s.bot_name} | {s.games_played} | {s.wins} | {s.losses} | "
                f"{s.win_rate:.1f}% | {format_time(s.avg_time_per_turn)} | "
                f"{format_time(s.max_time_single_turn)} |"
            )
        
        # Detailed breakdown
        report_lines.extend([
            "",
            "## Win/Loss Breakdown",
            "",
        ])
        
        for s in sorted_stats:
            report_lines.extend([
                f"### {s.bot_name}",
                "",
                f"**Wins ({s.wins}):**",
                f"- By no moves: {s.wins_by_no_moves}",
                f"- By timeout: {s.wins_by_timeout}",
                f"- By invalid move: {s.wins_by_invalid_move}",
                f"- By crash: {s.wins_by_crash}",
                "",
                f"**Losses ({s.losses}):**",
                f"- By no moves: {s.losses_by_no_moves}",
                f"- By timeout: {s.losses_by_timeout}",
                f"- By invalid move: {s.losses_by_invalid_move}",
                f"- By crash: {s.losses_by_crash}",
                "",
            ])
        
        # Game-by-game results
        report_lines.extend([
            "## Game Results",
            "",
            "| Game | Winner | Loser | Reason | Turns |",
            "|------|--------|-------|--------|-------|",
        ])
        
        for i, r in enumerate(results, 1):
            report_lines.append(
                f"| {i} | {r.winner or '-'} | {r.loser or '-'} | "
                f"{r.end_reason.value} | {r.total_turns} |"
            )
        
        report = '\n'.join(report_lines)
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        return filepath


def print_game_analysis(result: GameResult):
    """Print detailed analysis to console."""
    analyzer = GameAnalyzer()
    analysis = analyzer.analyze_game(result)
    
    print("\n" + "="*60)
    print("DETAILED GAME ANALYSIS")
    print("="*60)
    
    print(f"\nResult: {analysis['winner']} wins by {analysis['end_reason']}")
    print(f"Total turns: {analysis['total_turns']}")
    
    for bot_name, bot_stats in analysis["bots"].items():
        print(f"\n{bot_name}:")
        print(f"  Turns played: {bot_stats['total_turns']}")
        print(f"  First turn: {format_time(bot_stats['first_turn_time'])}")
        print(f"  Average time: {format_time(bot_stats['avg_time'])}")
        print(f"  Max time: {format_time(bot_stats['max_time'])} (turn {bot_stats['max_time_turn']})")
        print(f"  Min time: {format_time(bot_stats['min_time'])} (turn {bot_stats['min_time_turn']})")
        if bot_stats['max_memory_bytes'] > 0:
            print(f"  Max memory: {format_bytes(bot_stats['max_memory_bytes'])}")
