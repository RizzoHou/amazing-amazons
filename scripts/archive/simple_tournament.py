#!/usr/bin/env python3
"""
Simple Botzone Tournament System - More reliable version
"""

import subprocess
import sys
import time
import os
from typing import List, Tuple, Optional

class SimpleBot:
    """Simple bot wrapper that communicates exactly like Botzone"""
    
    def __init__(self, bot_path: str, bot_name: str = "Unknown"):
        self.bot_path = bot_path
        self.bot_name = bot_name
        self.process = None
        
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
    
    def stop(self):
        """Stop the bot process"""
        if self.process:
            try:
                self.process.kill()
                self.process.wait(timeout=1)
            except:
                pass
            self.process = None
    
    def send_and_receive(self, turn_id: int, history: List[str]) -> Optional[str]:
        """
        Send turn to bot and receive response
        
        Returns:
            Bot's move or None if error
        """
        if not self.process:
            self.start()
        
        try:
            # Send turn ID
            self.process.stdin.write(f"{turn_id}\n")
            
            # Send history
            for line in history:
                self.process.stdin.write(f"{line}\n")
            
            self.process.stdin.flush()
            
            # Read move (blocking with timeout)
            # Use communicate with timeout would be better but we need interactive
            # Instead, use a simple approach: readline with short timeout
            
            # First, try to read move
            move = None
            start_time = time.time()
            
            # Simple polling approach
            while time.time() - start_time < 2.0:
                # Check if there's data available
                import select
                ready = select.select([self.process.stdout], [], [], 0.1)
                if ready[0]:
                    line = self.process.stdout.readline()
                    if line:
                        move = line.strip()
                        break
            
            if not move:
                print(f"  {self.bot_name} TLE (no move)")
                return None
            
            # Read keep-running line
            keep = None
            start_time = time.time()
            while time.time() - start_time < 0.5:
                import select
                ready = select.select([self.process.stdout], [], [], 0.1)
                if ready[0]:
                    line = self.process.stdout.readline()
                    if line:
                        keep = line.strip()
                        break
            
            if keep != ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<":
                print(f"  Warning: {self.bot_name} keep-running mismatch: {keep}")
            
            return move
            
        except Exception as e:
            print(f"  Error with {self.bot_name}: {e}")
            return None

def build_history(turn_id: int, moves: List[str], is_black: bool) -> List[str]:
    """Build history for a turn"""
    history = ["-1 -1 -1 -1 -1 -1"]
    
    # Add all moves so far
    for move in moves:
        history.append(move)
    
    # White receives last move twice
    if not is_black and turn_id > 1 and len(moves) > 0:
        history.append(moves[-1])
    
    return history

def test_bot003_self_play():
    """Test bot003 self-play - should work perfectly"""
    print("\n" + "="*60)
    print("Test: bot003 self-play (should work perfectly)")
    print("="*60)
    
    bot_path = "./bots/bot003"
    
    bot1 = SimpleBot(bot_path, "bot003 (Black)")
    bot2 = SimpleBot(bot_path, "bot003 (White)")
    
    try:
        bot1.start()
        bot2.start()
        
        moves = []
        max_turns = 10
        
        for turn in range(1, max_turns + 1):
            is_black_turn = (turn % 2 == 1)
            current_bot = bot1 if is_black_turn else bot2
            bot_name = "bot003 (Black)" if is_black_turn else "bot003 (White)"
            
            print(f"  Turn {turn}: {bot_name}...")
            
            history = build_history(turn, moves, is_black_turn)
            
            move = current_bot.send_and_receive(turn, history)
            
            if not move:
                print(f"  ✗ {bot_name} failed to make a move")
                return False
            
            if move == "-1 -1 -1 -1 -1 -1":
                print(f"  ✓ {bot_name} has no legal moves (game over)")
                break
            
            # Validate move format
            parts = move.split()
            if len(parts) != 6:
                print(f"  ✗ {bot_name} made invalid move: {move}")
                return False
            
            moves.append(move)
            print(f"    Move: {move}")
        
        print(f"\n✓ Test passed: {len(moves)} moves played successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        return False
    finally:
        bot1.stop()
        bot2.stop()

def main():
    """Main function"""
    print("="*60)
    print("Simple Botzone Tournament Test")
    print("="*60)
    
    # Make sure bot003 is compiled
    bot003_path = "./bots/bot003"
    if not os.path.exists(bot003_path):
        print("Compiling bot003...")
        result = subprocess.run(["g++", "-O3", "-std=c++11", "-o", "bots/bot003", "bots/bot003.cpp"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to compile bot003: {result.stderr}")
            return 1
    
    # Run test
    success = test_bot003_self_play()
    
    print("\n" + "="*60)
    if success:
        print("✓ SUCCESS: bot003 works correctly")
        print("  The tournament system bug is isolated to the complex tournament.py")
        return 0
    else:
        print("✗ FAILED: bot003 has issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
