#!/usr/bin/env python3
"""
Botzone Simulator - Test bot I/O and functionality
Simulates the Botzone long-running protocol
"""

import subprocess
import sys
import time

def simulate_game(bot_command, test_input):
    """
    Simulate a Botzone game with the given bot
    
    Args:
        bot_command: Command to start the bot (list)
        test_input: List of input lines to send to bot
    
    Returns:
        List of output lines from bot
    """
    process = subprocess.Popen(
        bot_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    outputs = []
    
    try:
        for line in test_input:
            process.stdin.write(line + '\n')
            process.stdin.flush()
            
            # Read bot's response
            output = process.stdout.readline().strip()
            outputs.append(output)
            print(f"  Bot output: {output}")
            
            # Check for keep-running request
            keep_running = process.stdout.readline().strip()
            if keep_running == ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<":
                outputs.append(keep_running)
                print(f"  Bot output: {keep_running}")
        
        process.stdin.close()
        process.wait(timeout=5)
        
    except Exception as e:
        print(f"Error: {e}")
        process.kill()
        return None
    
    return outputs

def test_first_move_as_black():
    """Test bot playing first move as BLACK"""
    print("\n=== Test: First move as BLACK ===")
    
    # Turn 1, BLACK moves first
    test_input = [
        "1",  # Turn ID
        "-1 -1 -1 -1 -1 -1"  # No previous moves
    ]
    
    print("Testing Python bot...")
    py_output = simulate_game(["python3", "bots/bot001.py"], test_input)
    
    print("\nTesting C++ bot...")
    cpp_output = simulate_game(["./bots/bot001_cpp"], test_input)
    
    if py_output and cpp_output:
        print("\n✓ Both bots produced output")
        py_move = py_output[0].split()
        cpp_move = cpp_output[0].split()
        if len(py_move) == 6 and len(cpp_move) == 6:
            print("✓ Both produced valid 6-coordinate moves")
            return True
    return False

def test_second_move_as_white():
    """Test bot playing second move as WHITE"""
    print("\n=== Test: Second move as WHITE ===")
    
    # Turn 2, WHITE responds to BLACK's move
    test_input = [
        "2",  # Turn ID
        "-1 -1 -1 -1 -1 -1",  # BLACK's placeholder
        "0 2 1 2 0 2",  # BLACK's actual move
        "0 2 1 2 0 2"   # WHITE's turn (we respond)
    ]
    
    print("Testing Python bot...")
    py_output = simulate_game(["python3", "bots/bot001.py"], test_input)
    
    print("\nTesting C++ bot...")
    cpp_output = simulate_game(["./bots/bot001_cpp"], test_input)
    
    if py_output and cpp_output:
        print("\n✓ Both bots produced output as WHITE")
        return True
    return False

def test_multiple_turns():
    """Test bot handling multiple turns"""
    print("\n=== Test: Multiple turns (long-running mode) ===")
    
    bot_command = ["./bots/bot001_cpp"]
    
    process = subprocess.Popen(
        bot_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        # First turn
        print("Turn 1...")
        process.stdin.write("1\n")
        process.stdin.write("-1 -1 -1 -1 -1 -1\n")
        process.stdin.flush()
        
        move1 = process.stdout.readline().strip()
        keep1 = process.stdout.readline().strip()
        print(f"  Move: {move1}")
        print(f"  Keep running: {keep1}")
        
        if keep1 != ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<":
            print("✗ Bot didn't request to keep running")
            return False
        
        # Simulate opponent's move and bot's second turn
        print("Turn 2 (opponent move + our move)...")
        process.stdin.write("0 5 1 5 0 5\n")  # Opponent's move
        process.stdin.flush()
        
        time.sleep(0.1)  # Give bot time to think
        
        move2 = process.stdout.readline().strip()
        keep2 = process.stdout.readline().strip()
        print(f"  Move: {move2}")
        print(f"  Keep running: {keep2}")
        
        if move2.count(' ') == 5 and keep2 == ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<":
            print("✓ Bot successfully handled multiple turns")
            return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        process.kill()
    
    return False

def main():
    print("=" * 60)
    print("Botzone Simulator - Bot Testing")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("First move as BLACK", test_first_move_as_black()))
    results.append(("Second move as WHITE", test_second_move_as_white()))
    results.append(("Multiple turns", test_multiple_turns()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! Bot is ready for tournament.")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the bot implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
