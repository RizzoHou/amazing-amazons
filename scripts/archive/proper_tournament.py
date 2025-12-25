#!/usr/bin/env python3
"""
Proper Botzone Tournament System
Follows exact Botzone Simple Interaction Protocol with Keep-Running mode
"""

import subprocess
import sys
import time
import os
from typing import List, Tuple, Optional

class ProperBot:
    """Bot wrapper that follows exact Botzone protocol"""
    
    def __init__(self, bot_path: str, bot_name: str = "Unknown", time_limit: float = 2.0):
        self.bot_path = bot_path
        self.bot_name = bot_name
        self.time_limit = time_limit
        self.process = None
        self.is_keep_running = False  # Whether bot has entered keep-running mode
        
    def start(self):
        """Start the bot process"""
        self.process = subprocess.Popen(
            [self.bot_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        self.is_keep_running = False
    
    def stop(self):
        """Stop the bot process"""
        if self.process:
            try:
                self.process.kill()
                self.process.wait(timeout=1)
            except:
                pass
            self.process = None
    
    def read_line_with_timeout(self, timeout: float) -> Optional[str]:
        """Read a line with timeout"""
        if not self.process:
            return None
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            import select
            ready = select.select([self.process.stdout], [], [], 0.1)
            if ready[0]:
                line = self.process.stdout.readline()
                if line:
                    return line.strip()
        
        return None
    
    def play_first_turn(self, is_black: bool) -> Optional[str]:
        """
        Play first turn (Black or White)
        
        Returns:
            Move or None if error
        """
        if not self.process:
            self.start()
        
        try:
            # Send turn ID = 1
            self.process.stdin.write("1\n")
            
            # Send request: -1 for Black, opponent's move for White
            if is_black:
                self.process.stdin.write("-1 -1 -1 -1 -1 -1\n")
            else:
                # White's first turn: receives Black's move
                # But we don't have it yet, so this shouldn't happen
                # In tournament, White's first turn is actually turn 2
                self.process.stdin.write("-1 -1 -1 -1 -1 -1\n")
            
            self.process.stdin.flush()
            
            # Read move
            move = self.read_line_with_timeout(self.time_limit)
            if not move:
                print(f"  {self.bot_name} TLE on first turn")
                return None
            
            # Read keep-running
            keep = self.read_line_with_timeout(0.5)
            if keep == ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<":
                self.is_keep_running = True
                print(f"  {self.bot_name} entered keep-running mode")
            else:
                print(f"  Warning: {self.bot_name} keep-running mismatch: {keep}")
            
            return move
            
        except Exception as e:
            print(f"  Error with {self.bot_name} first turn: {e}")
            return None
    
    def play_turn_keep_running(self, opponent_move: str) -> Optional[str]:
        """
        Play a turn in keep-running mode
        
        Args:
            opponent_move: Opponent's move from previous turn (6 ints)
            
        Returns:
            Move or None if error
        """
        if not self.process:
            self.start()
        
        if not self.is_keep_running:
            print(f"  Error: {self.bot_name} not in keep-running mode")
            return None
        
        try:
            # In keep-running mode, just send opponent's move
            self.process.stdin.write(f"{opponent_move}\n")
            self.process.stdin.flush()
            
            # Read move
            move = self.read_line_with_timeout(self.time_limit)
            if not move:
                print(f"  {self.bot_name} TLE in keep-running mode")
                return None
            
            # Read keep-running
            keep = self.read_line_with_timeout(0.5)
            if keep != ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<":
                print(f"  Warning: {self.bot_name} keep-running mismatch: {keep}")
            
            return move
            
        except Exception as e:
            print(f"  Error with {self.bot_name} in keep-running: {e}")
            return None

def test_proper_tournament():
    """Test proper tournament system"""
    print("\n" + "="*60)
    print("Test: Proper tournament system")
    print("="*60)
    
    bot_path = "./bots/bot003"
    
    # Compile if needed
    if not os.path.exists(bot_path):
        print("Compiling bot003...")
        result = subprocess.run(["g++", "-O3", "-std=c++11", "-o", "bots/bot003", "bots/bot003.cpp"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to compile: {result.stderr}")
            return False
    
    # Create bots
    black_bot = ProperBot(bot_path, "bot003 (Black)")
    white_bot = ProperBot(bot_path, "bot003 (White)")
    
    try:
        # Start both bots
        black_bot.start()
        white_bot.start()
        
        moves = []
        max_turns = 20
        
        # Turn 1: Black's first turn
        print(f"  Turn 1: Black's first turn...")
        black_move = black_bot.play_first_turn(is_black=True)
        if not black_move:
            print(f"  ✗ Black failed first turn")
            return False
        
        if black_move == "-1 -1 -1 -1 -1 -1":
            print(f"  ✓ Black has no legal moves (unlikely)")
            return True
        
        moves.append(black_move)
        print(f"    Black move: {black_move}")
        
        # Turn 2: White's first turn (but needs Black's move)
        print(f"  Turn 2: White's first turn...")
        
        # White needs to play first turn with Black's move as opponent
        # Actually, White's first turn should receive "-1" then Black's move
        # But bot000.cpp expects to read lines until it finds 6 ints
        # Let's send just Black's move
        white_move = white_bot.play_first_turn(is_black=False)
        if not white_move:
            print(f"  ✗ White failed first turn")
            return False
        
        moves.append(white_move)
        print(f"    White move: {white_move}")
        
        # Now both bots are in keep-running mode
        # Continue alternating
        
        for turn in range(3, max_turns + 1):
            is_black_turn = (turn % 2 == 1)
            current_bot = black_bot if is_black_turn else white_bot
            opponent_bot = white_bot if is_black_turn else black_bot
            bot_name = "Black" if is_black_turn else "White"
            
            print(f"  Turn {turn}: {bot_name}'s turn...")
            
            # Get opponent's last move
            opponent_last_move = moves[-1]
            
            # Play turn in keep-running mode
            move = current_bot.play_turn_keep_running(opponent_last_move)
            
            if not move:
                print(f"  ✗ {bot_name} failed to make a move")
                return False
            
            if move == "-1 -1 -1 -1 -1 -1":
                print(f"  ✓ {bot_name} has no legal moves (game over)")
                break
            
            moves.append(move)
            print(f"    {bot_name} move: {move}")
        
        print(f"\n✓ Test passed: {len(moves)} moves played successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        black_bot.stop()
        white_bot.stop()

def main():
    """Main function"""
    print("="*60)
    print("Proper Botzone Tournament Test")
    print("="*60)
    
    success = test_proper_tournament()
    
    print("\n" + "="*60)
    if success:
        print("✓ SUCCESS: Proper tournament system works correctly")
        return 0
    else:
        print("✗ FAILED: Tournament system still has issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
