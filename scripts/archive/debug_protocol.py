#!/usr/bin/env python3
"""
Debug Botzone Protocol
"""

import subprocess
import time
import os

def test_protocol():
    """Test exact protocol with bot000"""
    
    # Compile bot000 if needed
    bot_path = "./bots/bot000"
    if not os.path.exists(bot_path):
        print("Compiling bot000...")
        result = subprocess.run(["g++", "-O3", "-std=c++11", "-o", "bots/bot000", "bots/bot000.cpp"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to compile: {result.stderr}")
            return
    
    # Start bot
    proc = subprocess.Popen(
        [bot_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    try:
        # Turn 1: Black's turn
        print("\n=== Turn 1 (Black) ===")
        print("Sending: 1")
        proc.stdin.write("1\n")
        print("Sending: -1 -1 -1 -1 -1 -1")
        proc.stdin.write("-1 -1 -1 -1 -1 -1\n")
        proc.stdin.flush()
        
        # Read response
        time.sleep(0.1)
        move = proc.stdout.readline().strip()
        print(f"Received move: {move}")
        
        keep = proc.stdout.readline().strip()
        print(f"Received keep: {keep}")
        
        # Turn 2: White's turn
        print("\n=== Turn 2 (White) ===")
        print("Sending: 2")
        proc.stdin.write("2\n")
        
        # Should send 3 lines: -1, Black's move, Black's move again
        print("Sending: -1 -1 -1 -1 -1 -1")
        proc.stdin.write("-1 -1 -1 -1 -1 -1\n")
        print(f"Sending: {move}")
        proc.stdin.write(f"{move}\n")
        print(f"Sending: {move} (again)")
        proc.stdin.write(f"{move}\n")
        proc.stdin.flush()
        
        # Read response
        time.sleep(0.1)
        move2 = proc.stdout.readline().strip()
        print(f"Received move: {move2}")
        
        keep2 = proc.stdout.readline().strip()
        print(f"Received keep: {keep2}")
        
        # Turn 3: Black's turn again
        print("\n=== Turn 3 (Black) ===")
        print("Sending: 3")
        proc.stdin.write("3\n")
        
        # Should send 5 lines: -1, Black's move, White's move, Black's move, White's move
        print("Sending: -1 -1 -1 -1 -1 -1")
        proc.stdin.write("-1 -1 -1 -1 -1 -1\n")
        print(f"Sending: {move}")
        proc.stdin.write(f"{move}\n")
        print(f"Sending: {move2}")
        proc.stdin.write(f"{move2}\n")
        print(f"Sending: {move}")
        proc.stdin.write(f"{move}\n")
        print(f"Sending: {move2}")
        proc.stdin.write(f"{move2}\n")
        proc.stdin.flush()
        
        # Read response
        time.sleep(0.1)
        move3 = proc.stdout.readline().strip()
        print(f"Received move: {move3}")
        
        keep3 = proc.stdout.readline().strip()
        print(f"Received keep: {keep3}")
        
        print("\n=== Protocol test complete ===")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        proc.kill()

if __name__ == "__main__":
    test_protocol()
