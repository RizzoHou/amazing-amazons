#!/usr/bin/env python3
"""
Competition automation script for Amazing Amazons bots.

Runs 10-game competitions between each new bot (bot004-bot008) and bot003,
collects results, and generates analysis reports.

Runs games sequentially (not in parallel) due to memory constraints.
"""

import argparse
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Add parent directory to path to import tournament modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.tournament.game_engine import FixedGame
from scripts.tournament.utils import compile_bot, bot_exists, get_bot_path


class CompetitionRunner:
    """Runs competitions between bots and collects results."""
    
    def __init__(self, output_dir: str = "results/competitions"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Results storage
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "competitions": {}
        }
    
    def run_single_game(self, bot1_name: str, bot2_name: str, game_num: int) -> Dict:
        """
        Run a single game between two bots.
        
        Returns:
            Dictionary with game results
        """
        print(f"  Game {game_num}: {bot1_name} (Black) vs {bot2_name} (White)")
        
        # Ensure bots are compiled
        for bot_name in [bot1_name, bot2_name]:
            if not bot_exists(bot_name):
                if not compile_bot(bot_name):
                    return {
                        "error": f"Failed to compile {bot_name}",
                        "winner": None,
                        "moves": 0,
                        "duration": 0
                    }
        
        bot1_path = get_bot_path(bot1_name)
        bot2_path = get_bot_path(bot2_name)
        
        start_time = time.time()
        game = FixedGame([bot1_path], [bot2_path], bot1_name, bot2_name)
        winner, moves = game.play()
        duration = time.time() - start_time
        
        result = {
            "bot1": bot1_name,
            "bot2": bot2_name,
            "winner": winner,
            "moves": len(moves),
            "duration": duration,
            "error": game.error,
            "completed": game.error is None
        }
        
        if game.error:
            print(f"    ✗ Error: {game.error}")
        else:
            print(f"    ✓ {winner} wins in {len(moves)} moves ({duration:.1f}s)")
        
        return result
    
    def run_competition(self, bot_name: str, opponent_name: str = "bot003", games: int = 10) -> Dict:
        """
        Run a competition between a bot and an opponent.
        
        Args:
            bot_name: The new bot to test
            opponent_name: Opponent bot (default: bot003)
            games: Number of games to play
        
        Returns:
            Competition results
        """
        print(f"\n{'='*60}")
        print(f"Competition: {bot_name} vs {opponent_name} ({games} games)")
        print(f"{'='*60}")
        
        competition_results = {
            "bot": bot_name,
            "opponent": opponent_name,
            "games": games,
            "start_time": datetime.now().isoformat(),
            "results": []
        }
        
        wins = 0
        losses = 0
        draws = 0
        errors = 0
        
        # Run games sequentially (not in parallel due to memory constraints)
        for i in range(1, games + 1):
            result = self.run_single_game(bot_name, opponent_name, i)
            competition_results["results"].append(result)
            
            if result["error"]:
                errors += 1
            elif result["winner"] == bot_name:
                wins += 1
            elif result["winner"] == opponent_name:
                losses += 1
            else:
                draws += 1
        
        competition_results["end_time"] = datetime.now().isoformat()
        competition_results["summary"] = {
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "errors": errors,
            "win_rate": wins / games if games > 0 else 0
        }
        
        print(f"\nSummary: {wins} wins, {losses} losses, {draws} draws, {errors} errors")
        print(f"Win rate: {competition_results['summary']['win_rate']:.1%}")
        
        return competition_results
    
    def run_all_competitions(self, bots: List[str] = None, games_per_competition: int = 10):
        """
        Run competitions for all specified bots against bot003.
        
        Args:
            bots: List of bot names (default: bot004-bot008)
            games_per_competition: Number of games per competition
        """
        if bots is None:
            bots = ["bot004", "bot005", "bot006", "bot007", "bot008"]
        
        print(f"\n{'='*60}")
        print(f"Running competitions for {len(bots)} bots")
        print(f"Opponent: bot003, Games per competition: {games_per_competition}")
        print(f"Running sequentially (not in parallel) due to memory constraints")
        print(f"{'='*60}")
        
        for bot in bots:
            competition = self.run_competition(bot, "bot003", games_per_competition)
            self.results["competitions"][bot] = competition
        
        self.save_results()
        self.generate_reports()
    
    def save_results(self):
        """Save results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"competition_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nResults saved to: {filename}")
    
    def generate_reports(self):
        """Generate markdown reports from results."""
        reports_dir = Path("docs/analysis/")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate individual reports
        for bot_name, competition in self.results["competitions"].items():
            self._generate_bot_report(bot_name, competition, reports_dir)
        
        # Generate summary report
        self._generate_summary_report(reports_dir)
    
    def _generate_bot_report(self, bot_name: str, competition: Dict, reports_dir: Path):
        """Generate a markdown report for a single bot."""
        filename = reports_dir / f"{bot_name}_vs_bot003_results.md"
        
        summary = competition["summary"]
        win_rate = summary["win_rate"]
        
        with open(filename, 'w') as f:
            f.write(f"# {bot_name} vs bot003 Competition Results\n\n")
            f.write(f"**Date:** {competition['start_time']}\n")
            f.write(f"**Games:** {competition['games']}\n")
            f.write(f"**Opponent:** {competition['opponent']}\n\n")
            
            f.write("## Summary\n\n")
            f.write(f"- **Wins:** {summary['wins']}\n")
            f.write(f"- **Losses:** {summary['losses']}\n")
            f.write(f"- **Draws:** {summary['draws']}\n")
            f.write(f"- **Errors:** {summary['errors']}\n")
            f.write(f"- **Win Rate:** {win_rate:.1%}\n\n")
            
            f.write("## Game Details\n\n")
            f.write("| Game | Winner | Moves | Duration | Error |\n")
            f.write("|------|--------|-------|----------|-------|\n")
            
            for i, result in enumerate(competition["results"], 1):
                winner = result["winner"] or "Error"
                moves = result["moves"]
                duration = f"{result['duration']:.1f}s"
                error = result["error"] or "None"
                
                f.write(f"| {i} | {winner} | {moves} | {duration} | {error[:50]} |\n")
            
            f.write("\n## Analysis\n\n")
            
            if win_rate > 0.5:
                f.write(f"✅ **{bot_name} outperforms bot003** with a {win_rate:.1%} win rate.\n")
            elif win_rate < 0.5:
                f.write(f"❌ **{bot_name} underperforms compared to bot003** with a {win_rate:.1%} win rate.\n")
            else:
                f.write(f"⚖️ **{bot_name} performs equally to bot003** with a {win_rate:.1%} win rate.\n")
            
            # Calculate average moves for wins vs losses
            win_moves = [r["moves"] for r in competition["results"] if r["winner"] == bot_name]
            loss_moves = [r["moves"] for r in competition["results"] if r["winner"] == competition["opponent"]]
            
            if win_moves:
                avg_win_moves = sum(win_moves) / len(win_moves)
                f.write(f"- Average moves when winning: {avg_win_moves:.1f}\n")
            
            if loss_moves:
                avg_loss_moves = sum(loss_moves) / len(loss_moves)
                f.write(f"- Average moves when losing: {avg_loss_moves:.1f}\n")
        
        print(f"Generated report: {filename}")
    
    def _generate_summary_report(self, reports_dir: Path):
        """Generate a summary report comparing all bots."""
        filename = reports_dir / "summary_report.md"
        
        with open(filename, 'w') as f:
            f.write("# Competition Summary Report\n\n")
            f.write(f"**Date:** {self.results['timestamp']}\n")
            f.write(f"**Total Competitions:** {len(self.results['competitions'])}\n")
            f.write(f"**Games per Competition:** 10\n\n")
            
            f.write("## Overall Results\n\n")
            f.write("| Bot | Wins | Losses | Draws | Errors | Win Rate |\n")
            f.write("|-----|------|--------|-------|--------|----------|\n")
            
            for bot_name in sorted(self.results["competitions"].keys()):
                comp = self.results["competitions"][bot_name]
                summary = comp["summary"]
                win_rate = summary["win_rate"]
                
                f.write(f"| {bot_name} | {summary['wins']} | {summary['losses']} | {summary['draws']} | {summary['errors']} | {win_rate:.1%} |\n")
            
            f.write("\n## Performance Ranking\n\n")
            
            # Sort bots by win rate
            ranked_bots = sorted(
                self.results["competitions"].items(),
                key=lambda x: x[1]["summary"]["win_rate"],
                reverse=True
            )
            
            for rank, (bot_name, comp) in enumerate(ranked_bots, 1):
                win_rate = comp["summary"]["win_rate"]
                f.write(f"{rank}. **{bot_name}**: {win_rate:.1%} win rate\n")
            
            f.write("\n## Key Findings\n\n")
            
            # Analyze which improvements were most effective
            improvements = {
                "bot004": "Move ordering heuristics",
                "bot005": "Transposition table",
                "bot006": "Progressive widening",
                "bot007": "Bitboard representation",
                "bot008": "Adaptive time management"
            }
            
            best_bot = ranked_bots[0][0] if ranked_bots else None
            worst_bot = ranked_bots[-1][0] if ranked_bots else None
            
            if best_bot:
                f.write(f"1. **Most effective improvement**: {improvements.get(best_bot, best_bot)} ({best_bot})\n")
            
            if worst_bot:
                f.write(f"2. **Least effective improvement**: {improvements.get(worst_bot, worst_bot)} ({worst_bot})\n")
            
            f.write("\n## Recommendations\n\n")
            f.write("Based on the competition results:\n\n")
            
            for bot_name, comp in ranked_bots:
                win_rate = comp["summary"]["win_rate"]
                if win_rate > 0.6:
                    f.write(f"- ✅ **{bot_name}** shows significant improvement over bot003\n")
                elif win_rate > 0.45:
                    f.write(f"- ⚠️ **{bot_name}** shows marginal improvement over bot003\n")
                else:
                    f.write(f"- ❌ **{bot_name}** does not improve upon bot003\n")
        
        print(f"Generated summary report: {filename}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run competitions between new bots and bot003",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                         # Run all competitions (default)
  %(prog)s --bots bot004 bot005    # Run specific bots
  %(prog)s --games 5               # Run 5 games per competition
  %(prog)s --output custom_results # Custom output directory
        """
    )
    
    parser.add_argument(
        "--bots",
        nargs="+",
        default=["bot004", "bot005", "bot006", "bot007", "bot008"],
        help="Bots to test (default: all new bots)"
    )
    
    parser.add_argument(
        "--games",
        type=int,
        default=10,
        help="Number of games per competition (default: 10)"
    )
    
    parser.add_argument(
        "--output",
        default="results/competitions",
        help="Output directory for results (default: results/competitions)"
    )
    
    parser.add_argument(
        "--skip-reports",
        action="store_true",
        help="Skip generating markdown reports"
    )
    
    args = parser.parse_args()
    
    print("Amazing Amazons Competition Runner")
    print("=" * 60)
    
    try:
        runner = CompetitionRunner(args.output)
        runner.run_all_competitions(args.bots, args.games)
        
        if not args.skip_reports:
            runner.generate_reports()
        
        print("\n" + "=" * 60)
        print("All competitions completed successfully!")
        print("=" * 60)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nCompetition runner interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())