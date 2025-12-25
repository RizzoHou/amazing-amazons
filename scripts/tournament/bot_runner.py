"""
Bot runner module for managing bot processes.

Contains the ProperBot class that handles bot process management
and communication following Botzone protocol.
"""

import subprocess
import time
from typing import Optional
import select


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
