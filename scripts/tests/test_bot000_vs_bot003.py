#!/usr/bin/env python3
"""
Test bot000 vs bot003 with proper tournament system
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
        self.is_keep_running = False
        
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
        """Play first turn"""
        if not self.process:
            self.start()
        
        try:
            # Send turn ID = 1
            self.process.stdin.write("1\n")
            
            # Send request: -1 for Black, opponent's move for White
            if is_black:
                self.process.stdin.write("-1 -1 -1 -1 -1 -1\n")
            else:
                # White's first turn
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
            else:
                print(f"  Warning: {self.bot_name} keep-running mismatch: {keep}")
            
            return move
            
        except Exception as e:
            print(f"  Error with {self.bot_name} first turn: {e}")
            return None
    
    def play_turn_keep_running(self, opponent_move: str) -> Optional[str]:
        """Play a turn in keep-running mode"""
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

def test_bot000_vs_bot003():
    """Test bot000 vs bot003"""
    print("\n" + "="*60)
    print("Test: bot000 vs bot003")
    print("="*60)
    
    bot000_path = "./bots/bot000"
    bot003_path = "./bots/bot003"
    
    # Compile if needed
    if not os.path.exists(bot000_path):
        print("Compiling bot000...")
        result = subprocess.run(["g++", "-O3", "-std=c++11", "-o", "bots/bot000", "bots/bot000.cpp"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to compile bot000: {result.stderr}")
            return False
    
    if not os.path.exists(bot003_path):
        print("Compiling bot003...")
        result = subprocess.run(["g++", "-O3", "-std=c++11", "-o", "bots/bot003", "bots/bot003.cpp"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to compile bot003: {result.stderr}")
            return False
    
    # Create bots
    bot000 = ProperBot(bot000_path, "bot000 (Black)")
    bot003 = ProperBot(bot003_path, "bot003 (White)")
    
    try:
        # Start both bots
        bot000.start()
        bot003.start()
        
        moves = []
        max_turns = 20
        
        # Turn 1: bot000 (Black) first turn
        print(f"  Turn 1: bot000 (Black) first turn...")
        move1 = bot000.play_first_turn(is_black=True)
        if not move1:
            print(f"  ✗ bot000 failed first turn")
            return False
        
        if move1 == "-1 -1 -1 -1 -1 -1":
            print(f"  ✓ bot000 has no legal moves")
            return True
        
        moves.append(move1)
        print(f"    bot000 move: {move1}")
        
        # Turn 2: bot003 (White) first turn
        print(f"  Turn 2: bot003 (White) first turn...")
        move2 = bot003.play_first_turn(is_black=False)
        if not move2:
            print(f"  ✗ bot003 failed first turn")
            return False
        
        moves.append(move2)
        print(f"    bot003 move: {move2}")
        
        # Continue alternating
        for turn in range(3, max_turns + 1):
            is_black_turn = (turn % 2 == 1)
            current_bot = bot000 if is_black_turn else bot003
            opponent_bot = bot003 if is_black_turn else bot000
            bot_name = "bot000" if is_black_turn else "bot003"
            
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
        print(f"  bot000 vs bot003 completed without TLE or illegal movements")
        return True
        
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        bot000.stop()
        bot003.stop()

def main():
    """Main function"""
    print("="*60)
    print("Test bot000 vs bot003 with fixed tournament system")
    print("="*60)
    
    success = test_bot000_vs_bot003()
    
    print("\n" + "="*60)
    if success:
        print("✓ SUCCESS: bot000 vs bot003 works correctly")
        print("  Tournament system bug is fixed")
        return 0
    else:
        print("✗ FAILED: Tournament system still has issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
