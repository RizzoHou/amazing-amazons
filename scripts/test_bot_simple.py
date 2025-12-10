#!/usr/bin/env python3
"""
Simple bot tester - Quick verification that bots can make moves
"""

import subprocess
import sys

def test_bot(bot_command, bot_name):
    """Test a bot with simple first move as BLACK"""
    print(f"\n=== Testing {bot_name} ===")
    
    # Simple test: First move as BLACK
    input_data = "1\n-1 -1 -1 -1 -1 -1\n"
    
    try:
        result = subprocess.run(
            bot_command,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            move = lines[0]
            keep_running = lines[1]
            
            print(f"  Move: {move}")
            print(f"  Keep running request: {keep_running}")
            
            move_parts = move.split()
            if len(move_parts) == 6:
                try:
                    coords = [int(x) for x in move_parts]
                    if all(-1 <= c < 8 for c in coords):
                        print(f"  ✓ Valid move produced")
                        if keep_running == ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<":
                            print(f"  ✓ Correct keep-running request")
                            return True
                        else:
                            print(f"  ✗ Missing or incorrect keep-running request")
                            return False
                except ValueError:
                    print(f"  ✗ Invalid coordinate format")
                    return False
            else:
                print(f"  ✗ Wrong number of coordinates")
                return False
        else:
            print(f"  ✗ Insufficient output")
            print(f"  stdout: {result.stdout}")
            print(f"  stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  ✗ Bot timed out")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Simple Bot Functionality Test")
    print("=" * 60)
    
    # Test Python bot (use venv python)
    py_result = test_bot(["venv/bin/python3", "bots/bot001.py"], "Python bot001")
    
    # Test C++ bot
    cpp_result = test_bot(["./bots/bot001_cpp"], "C++ bot001")
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Python bot: {'✓ PASS' if py_result else '✗ FAIL'}")
    print(f"C++ bot:    {'✓ PASS' if cpp_result else '✗ FAIL'}")
    
    if py_result and cpp_result:
        print("\n✓ Both bots are functional!")
        return 0
    else:
        print("\n✗ One or more bots failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
