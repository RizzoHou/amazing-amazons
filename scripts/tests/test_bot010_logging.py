#!/usr/bin/env python3
"""
Test script to verify bot010 logging functionality.
Runs a simple game to see if log files are created.
"""

import subprocess
import os
import time
import sys

def test_bot010_logging():
    """Test that bot010 creates log files when run."""
    
    print("Testing bot010 logging functionality...")
    
    # Check if bot010 executable exists
    bot_path = "bots/testing/bot010"
    if not os.path.exists(bot_path):
        print(f"Error: Bot executable not found at {bot_path}")
        print("Please compile bot010 first.")
        return False
    
    # Create test input (simplified first turn)
    test_input = "1\n-1 -1 -1 -1 -1 -1\n"
    
    # Run the bot with test input
    print(f"Running bot010 with test input...")
    try:
        start_time = time.time()
        result = subprocess.run(
            [bot_path],
            input=test_input.encode(),
            capture_output=True,
            timeout=5.0  # 5 second timeout
        )
        elapsed = time.time() - start_time
        
        print(f"Bot completed in {elapsed:.2f} seconds")
        print(f"Exit code: {result.returncode}")
        
        if result.stdout:
            print(f"Stdout: {result.stdout.decode().strip()}")
        if result.stderr:
            print(f"Stderr: {result.stderr.decode().strip()}")
        
    except subprocess.TimeoutExpired:
        print("Error: Bot timed out after 5 seconds")
        return False
    except Exception as e:
        print(f"Error running bot: {e}")
        return False
    
    # Check for log files
    logs_dir = "logs"
    if os.path.exists(logs_dir):
        log_files = [f for f in os.listdir(logs_dir) if f.startswith("bot010_time_log_")]
        if log_files:
            print(f"\n✓ Log files created successfully!")
            print(f"Found {len(log_files)} log file(s):")
            for log_file in sorted(log_files)[:3]:  # Show first 3
                file_path = os.path.join(logs_dir, log_file)
                file_size = os.path.getsize(file_path)
                print(f"  - {log_file} ({file_size} bytes)")
            
            # Show first few lines of the most recent log
            if log_files:
                latest_log = sorted(log_files)[-1]
                latest_path = os.path.join(logs_dir, latest_log)
                print(f"\nFirst few lines of {latest_log}:")
                try:
                    with open(latest_path, 'r') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines[:5]):
                            print(f"  {i+1}: {line.strip()}")
                except Exception as e:
                    print(f"  Error reading log file: {e}")
            
            return True
        else:
            print(f"\n✗ No log files found in {logs_dir}/")
            return False
    else:
        print(f"\n✗ Logs directory {logs_dir}/ does not exist")
        return False

if __name__ == "__main__":
    success = test_bot010_logging()
    sys.exit(0 if success else 1)