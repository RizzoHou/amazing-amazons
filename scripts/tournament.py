#!/usr/bin/env python3
"""
Tournament System - Run matches between bots
Supports parallel game execution
"""

import subprocess
import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse

class GameMediator:
    """Mediates a single game between two bots"""
    
    def __init__(self, bot1_cmd, bot2_cmd, game_id, timeout=120):
        self.bot1_cmd = bot1_cmd
        self.bot2_cmd = bot2_cmd
        self.game_id = game_id
        self.timeout = timeout
        self.moves = []
        self.times = []
        
    def run_game(self):
        """Run a complete game and return result"""
        try:
            # Start both bots
            bot1 = subprocess.Popen(
                self.bot1_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            bot2 = subprocess.Popen(
                self.bot2_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            turn = 1
            max_turns = 100  # Prevent infinite games
            
            # BLACK (bot1) moves first
            bot1.stdin.write("1\n")
            bot1.stdin.write("-1 -1 -1 -1 -1 -1\n")
            bot1.stdin.flush()
            
            start_time = time.time()
            move1 = bot1.stdout.readline().strip()
            elapsed = time.time() - start_time
            keep_running1 = bot1.stdout.readline().strip()
            
            if move1.startswith("-1"):
                return self._end_game(bot1, bot2, "WHITE", "BLACK has no moves", turn)
            
            self.moves.append(("BLACK", move1))
            self.times.append(("BLACK", elapsed))
            
            # WHITE (bot2) starts
            bot2.stdin.write("2\n")
            bot2.stdin.write("-1 -1 -1 -1 -1 -1\n")
            bot2.stdin.write(f"{move1}\n")
            bot2.stdin.write(f"{move1}\n")
            bot2.stdin.flush()
            
            start_time = time.time()
            move2 = bot2.stdout.readline().strip()
            elapsed = time.time() - start_time
            keep_running2 = bot2.stdout.readline().strip()
            
            if move2.startswith("-1"):
                return self._end_game(bot1, bot2, "BLACK", "WHITE has no moves", turn)
            
            self.moves.append(("WHITE", move2))
            self.times.append(("WHITE", elapsed))
            
            turn = 2
            
            # Game loop
            while turn < max_turns:
                turn += 1
                
                # Send opponent's move to BLACK
                bot1.stdin.write(f"{move2}\n")
                bot1.stdin.flush()
                
                start_time = time.time()
                move1 = bot1.stdout.readline().strip()
                elapsed = time.time() - start_time
                keep_running1 = bot1.stdout.readline().strip()
                
                if move1.startswith("-1"):
                    return self._end_game(bot1, bot2, "WHITE", "BLACK has no moves", turn)
                
                self.moves.append(("BLACK", move1))
                self.times.append(("BLACK", elapsed))
                
                # Send opponent's move to WHITE
                bot2.stdin.write(f"{move1}\n")
                bot2.stdin.flush()
                
                start_time = time.time()
                move2 = bot2.stdout.readline().strip()
                elapsed = time.time() - start_time
                keep_running2 = bot2.stdout.readline().strip()
                
                if move2.startswith("-1"):
                    return self._end_game(bot1, bot2, "BLACK", "WHITE has no moves", turn)
                
                self.moves.append(("WHITE", move2))
                self.times.append(("WHITE", elapsed))
            
            return self._end_game(bot1, bot2, "DRAW", "Max turns reached", turn)
            
        except Exception as e:
            return {
                "game_id": self.game_id,
                "winner": "ERROR",
                "reason": str(e),
                "turns": 0,
                "moves": [],
                "times": []
            }
    
    def _end_game(self, bot1, bot2, winner, reason, turns):
        """Clean up and return game result"""
        try:
            bot1.terminate()
            bot2.terminate()
            bot1.wait(timeout=1)
            bot2.wait(timeout=1)
        except:
            bot1.kill()
            bot2.kill()
        
        return {
            "game_id": self.game_id,
            "winner": winner,
            "reason": reason,
            "turns": turns,
            "moves": self.moves,
            "times": self.times
        }

def run_single_game(args):
    """Wrapper for parallel execution"""
    game_id, bot1_cmd, bot2_cmd, swap_colors = args
    
    if swap_colors:
        # Swap bots so bot2 plays BLACK and bot1 plays WHITE
        mediator = GameMediator(bot2_cmd, bot1_cmd, game_id)
        result = mediator.run_game()
        # Swap winner names back
        if result["winner"] == "BLACK":
            result["winner"] = "BOT2"
        elif result["winner"] == "WHITE":
            result["winner"] = "BOT1"
        result["colors"] = "BOT2=BLACK, BOT1=WHITE"
    else:
        mediator = GameMediator(bot1_cmd, bot2_cmd, game_id)
        result = mediator.run_game()
        # Map to bot names
        if result["winner"] == "BLACK":
            result["winner"] = "BOT1"
        elif result["winner"] == "WHITE":
            result["winner"] = "BOT2"
        result["colors"] = "BOT1=BLACK, BOT2=WHITE"
    
    return result

def run_tournament(bot1_cmd, bot2_cmd, num_games, parallel_games, output_file):
    """Run tournament with parallel execution"""
    
    print("=" * 60)
    print("Tournament System")
    print("=" * 60)
    print(f"Bot 1: {' '.join(bot1_cmd)}")
    print(f"Bot 2: {' '.join(bot2_cmd)}")
    print(f"Games: {num_games}")
    print(f"Parallel: {parallel_games}")
    print("=" * 60)
    
    # Prepare game tasks (alternate colors)
    tasks = []
    for i in range(num_games):
        swap = (i % 2 == 1)  # Alternate colors
        tasks.append((i + 1, bot1_cmd, bot2_cmd, swap))
    
    results = []
    start_time = time.time()
    
    # Run games in parallel
    with ProcessPoolExecutor(max_workers=parallel_games) as executor:
        futures = {executor.submit(run_single_game, task): task[0] for task in tasks}
        
        for future in as_completed(futures):
            game_id = futures[future]
            try:
                result = future.result()
                results.append(result)
                
                winner_str = result["winner"]
                if result["winner"] == "BOT1":
                    winner_str = f"Bot1 ({result['colors'].split(',')[0].split('=')[1]})"
                elif result["winner"] == "BOT2":
                    winner_str = f"Bot2 ({result['colors'].split(',')[1].split('=')[1]})"
                
                print(f"Game {game_id:2d}/{num_games}: {winner_str:20s} "
                      f"({result['turns']} turns) - {result['reason']}")
            except Exception as e:
                print(f"Game {game_id} failed: {e}")
    
    elapsed = time.time() - start_time
    
    # Calculate statistics
    bot1_wins = sum(1 for r in results if r["winner"] == "BOT1")
    bot2_wins = sum(1 for r in results if r["winner"] == "BOT2")
    draws = sum(1 for r in results if r["winner"] == "DRAW")
    errors = sum(1 for r in results if r["winner"] == "ERROR")
    
    avg_turns = sum(r["turns"] for r in results) / len(results) if results else 0
    
    # Time statistics
    bot1_times = []
    bot2_times = []
    for r in results:
        for player, t in r.get("times", []):
            if (r["colors"].startswith("BOT1=BLACK") and player == "BLACK") or \
               (r["colors"].startswith("BOT2=BLACK") and player == "WHITE"):
                bot1_times.append(t)
            else:
                bot2_times.append(t)
    
    avg_time_bot1 = sum(bot1_times) / len(bot1_times) if bot1_times else 0
    avg_time_bot2 = sum(bot2_times) / len(bot2_times) if bot2_times else 0
    
    # Print summary
    print("\n" + "=" * 60)
    print("TOURNAMENT RESULTS")
    print("=" * 60)
    print(f"Total games: {len(results)}")
    print(f"Bot 1 wins:  {bot1_wins} ({bot1_wins/len(results)*100:.1f}%)")
    print(f"Bot 2 wins:  {bot2_wins} ({bot2_wins/len(results)*100:.1f}%)")
    print(f"Draws:       {draws}")
    print(f"Errors:      {errors}")
    print(f"Avg turns:   {avg_turns:.1f}")
    print(f"Avg time Bot1: {avg_time_bot1:.3f}s")
    print(f"Avg time Bot2: {avg_time_bot2:.3f}s")
    print(f"Total time:  {elapsed:.1f}s")
    print("=" * 60)
    
    # Save results
    tournament_data = {
        "timestamp": datetime.now().isoformat(),
        "bot1": " ".join(bot1_cmd),
        "bot2": " ".join(bot2_cmd),
        "num_games": num_games,
        "parallel_games": parallel_games,
        "elapsed_time": elapsed,
        "statistics": {
            "bot1_wins": bot1_wins,
            "bot2_wins": bot2_wins,
            "draws": draws,
            "errors": errors,
            "avg_turns": avg_turns,
            "avg_time_bot1": avg_time_bot1,
            "avg_time_bot2": avg_time_bot2
        },
        "games": results
    }
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(tournament_data, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    return bot1_wins > bot2_wins

def main():
    parser = argparse.ArgumentParser(description="Run bot tournament")
    parser.add_argument("--bot1", default="venv/bin/python3 bots/bot001.py",
                        help="Bot 1 command")
    parser.add_argument("--bot2", default="./bots/bot001_cpp",
                        help="Bot 2 command")
    parser.add_argument("--games", type=int, default=50,
                        help="Number of games to play")
    parser.add_argument("--parallel", type=int, default=10,
                        help="Number of parallel games")
    parser.add_argument("--output", default="results/tournament_{timestamp}.json",
                        help="Output file path")
    
    args = parser.parse_args()
    
    # Parse commands
    bot1_cmd = args.bot1.split()
    bot2_cmd = args.bot2.split()
    
    # Replace timestamp in output path
    output_file = args.output.replace(
        "{timestamp}",
        datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    
    success = run_tournament(bot1_cmd, bot2_cmd, args.games, args.parallel, output_file)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
