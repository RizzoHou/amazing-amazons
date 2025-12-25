"""
Utility functions for the tournament system.

Contains helper functions for compilation, file handling, and other utilities.
"""

import subprocess
import os


def compile_bot(bot_name: str, source_path: str = None) -> bool:
    """
    Compile a bot from C++ source.
    
    Args:
        bot_name: Name of the bot (e.g., 'bot003')
        source_path: Optional path to source file. If None, uses bots/{bot_name}.cpp
    
    Returns:
        True if compilation succeeded, False otherwise
    """
    if source_path is None:
        source_path = f"bots/{bot_name}.cpp"
    
    output_path = f"bots/{bot_name}"
    
    print(f"Compiling {bot_name}...")
    result = subprocess.run(
        ["g++", "-O3", "-std=c++11", "-o", output_path, source_path],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✓ {bot_name} compiled successfully")
        return True
    else:
        print(f"✗ {bot_name} compilation failed:")
        print(f"  stderr: {result.stderr}")
        return False


def bot_exists(bot_name: str) -> bool:
    """
    Check if a bot executable exists.
    
    Args:
        bot_name: Name of the bot (e.g., 'bot003')
    
    Returns:
        True if bot executable exists, False otherwise
    """
    bot_path = f"bots/{bot_name}"
    return os.path.exists(bot_path)


def get_bot_path(bot_name: str) -> str:
    """
    Get the full path to a bot executable.
    
    Args:
        bot_name: Name of the bot (e.g., 'bot003')
    
    Returns:
        Full path to bot executable
    """
    return f"./bots/{bot_name}"
