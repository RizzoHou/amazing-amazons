"""
Resource Monitor module for tracking time and memory usage of bot processes.

Provides external monitoring of bot resource consumption to match Botzone behavior.
Supports both enforced limits and unlimited (measurement-only) mode.
"""

import os
import time
import subprocess
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class ViolationType(Enum):
    """Types of resource violations."""
    NONE = "none"
    TIME_LIMIT_EXCEEDED = "tle"
    MEMORY_LIMIT_EXCEEDED = "mle"


@dataclass
class TurnMetrics:
    """Metrics for a single turn."""
    turn_number: int
    time_seconds: float
    memory_bytes: int
    is_first_turn: bool = False
    time_limit: float = 0.0
    memory_limit: int = 0
    violation: ViolationType = ViolationType.NONE


@dataclass
class GameMetrics:
    """Aggregated metrics for an entire game."""
    bot_name: str
    turns: List[TurnMetrics] = field(default_factory=list)
    total_time: float = 0.0
    total_turns: int = 0
    
    # Time stats (excluding first turn)
    avg_time: float = 0.0
    max_time: float = 0.0
    min_time: float = float('inf')
    max_time_turn: int = 0
    min_time_turn: int = 0
    
    # Memory stats
    avg_memory: int = 0
    max_memory: int = 0
    min_memory: int = 0
    max_memory_turn: int = 0
    min_memory_turn: int = 0
    
    # First turn stats
    first_turn_time: float = 0.0
    first_turn_memory: int = 0


class ResourceMonitor:
    """
    Monitor and optionally enforce resource limits for bot processes.
    
    Botzone limits:
    - First turn: 2 seconds
    - Subsequent turns: 1 second
    - Memory: 256 MB
    """
    
    # Default Botzone limits
    DEFAULT_FIRST_TURN_TIME = 2.0  # seconds
    DEFAULT_TURN_TIME = 1.0  # seconds
    DEFAULT_MEMORY_LIMIT = 256 * 1024 * 1024  # 256 MB in bytes
    
    def __init__(
        self,
        first_turn_time: float = DEFAULT_FIRST_TURN_TIME,
        turn_time: float = DEFAULT_TURN_TIME,
        memory_limit: int = DEFAULT_MEMORY_LIMIT,
        enforce_limits: bool = True
    ):
        """
        Initialize resource monitor.
        
        Args:
            first_turn_time: Time limit for first turn in seconds
            turn_time: Time limit for subsequent turns in seconds
            memory_limit: Memory limit in bytes
            enforce_limits: If True, enforce limits; if False, only measure
        """
        self.first_turn_time = first_turn_time
        self.turn_time = turn_time
        self.memory_limit = memory_limit
        self.enforce_limits = enforce_limits
        
    def get_time_limit(self, is_first_turn: bool) -> float:
        """Get the time limit for a turn."""
        return self.first_turn_time if is_first_turn else self.turn_time
    
    def get_process_memory(self, pid: int) -> int:
        """
        Get memory usage of a process in bytes.
        
        Uses /proc on Linux/macOS or ps command as fallback.
        Returns 0 if unable to measure.
        """
        try:
            # Try using /proc filesystem (Linux)
            with open(f'/proc/{pid}/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        # VmRSS is in KB
                        return int(line.split()[1]) * 1024
        except (FileNotFoundError, PermissionError):
            pass
        
        try:
            # Fallback: use ps command (works on macOS and Linux)
            result = subprocess.run(
                ['ps', '-o', 'rss=', '-p', str(pid)],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0 and result.stdout.strip():
                # ps reports in KB
                return int(result.stdout.strip()) * 1024
        except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
            pass
        
        return 0
    
    def measure_turn(
        self,
        pid: int,
        turn_number: int,
        elapsed_time: float,
        is_first_turn: bool = False
    ) -> TurnMetrics:
        """
        Measure and record metrics for a turn.
        
        Args:
            pid: Process ID of the bot
            turn_number: Current turn number
            elapsed_time: Time taken for the turn in seconds
            is_first_turn: Whether this is the first turn
            
        Returns:
            TurnMetrics with measurements and any violations
        """
        memory = self.get_process_memory(pid) if pid > 0 else 0
        time_limit = self.get_time_limit(is_first_turn)
        
        # Check for violations
        violation = ViolationType.NONE
        if self.enforce_limits:
            if elapsed_time > time_limit:
                violation = ViolationType.TIME_LIMIT_EXCEEDED
            elif memory > self.memory_limit:
                violation = ViolationType.MEMORY_LIMIT_EXCEEDED
        
        return TurnMetrics(
            turn_number=turn_number,
            time_seconds=elapsed_time,
            memory_bytes=memory,
            is_first_turn=is_first_turn,
            time_limit=time_limit,
            memory_limit=self.memory_limit,
            violation=violation
        )
    
    def compute_game_metrics(
        self,
        bot_name: str,
        turns: List[TurnMetrics]
    ) -> GameMetrics:
        """
        Compute aggregated metrics for a game.
        
        Args:
            bot_name: Name of the bot
            turns: List of turn metrics
            
        Returns:
            GameMetrics with aggregated statistics
        """
        metrics = GameMetrics(bot_name=bot_name)
        
        if not turns:
            return metrics
        
        metrics.turns = turns
        metrics.total_turns = len(turns)
        metrics.total_time = sum(t.time_seconds for t in turns)
        
        # Separate first turn from rest
        non_first_turns = [t for t in turns if not t.is_first_turn]
        first_turns = [t for t in turns if t.is_first_turn]
        
        # First turn stats
        if first_turns:
            metrics.first_turn_time = first_turns[0].time_seconds
            metrics.first_turn_memory = first_turns[0].memory_bytes
        
        # Time stats for non-first turns
        if non_first_turns:
            times = [t.time_seconds for t in non_first_turns]
            metrics.avg_time = sum(times) / len(times)
            metrics.max_time = max(times)
            metrics.min_time = min(times)
            
            # Find which turns had max/min time
            for t in non_first_turns:
                if t.time_seconds == metrics.max_time:
                    metrics.max_time_turn = t.turn_number
                if t.time_seconds == metrics.min_time:
                    metrics.min_time_turn = t.turn_number
        
        # Memory stats for all turns
        memories = [t.memory_bytes for t in turns if t.memory_bytes > 0]
        if memories:
            metrics.avg_memory = sum(memories) // len(memories)
            metrics.max_memory = max(memories)
            metrics.min_memory = min(memories)
            
            for t in turns:
                if t.memory_bytes == metrics.max_memory:
                    metrics.max_memory_turn = t.turn_number
                if t.memory_bytes > 0 and t.memory_bytes == metrics.min_memory:
                    metrics.min_memory_turn = t.turn_number
        
        return metrics


def format_bytes(num_bytes: int) -> str:
    """Format bytes as human-readable string."""
    if num_bytes >= 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024 * 1024):.2f} GB"
    elif num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.2f} MB"
    elif num_bytes >= 1024:
        return f"{num_bytes / 1024:.2f} KB"
    else:
        return f"{num_bytes} B"


def format_time(seconds: float) -> str:
    """Format seconds as human-readable string."""
    if seconds >= 1.0:
        return f"{seconds:.3f}s"
    else:
        return f"{seconds * 1000:.1f}ms"
