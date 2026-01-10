"""
Bot Runner module for managing bot processes.

Supports two types of bots:
1. LongLiveBot - Bots using Botzone's keep-running mode
2. TraditionalBot - Bots that restart each turn (standard Botzone protocol)

Both follow the Botzone Simple Interaction protocol.
"""

import subprocess
import time
import signal
import os
import select
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from enum import Enum

from .resource_monitor import (
    ResourceMonitor, TurnMetrics, ViolationType, MemorySampler
)


class BotType(Enum):
    """Types of bots supported."""
    LONG_LIVE = "long_live"
    TRADITIONAL = "traditional"
    UNKNOWN = "unknown"


class BotResult(Enum):
    """Result of a bot turn."""
    SUCCESS = "success"
    NO_MOVES = "no_moves"
    TIMEOUT = "timeout"
    MEMORY_EXCEEDED = "memory_exceeded"
    INVALID_OUTPUT = "invalid_output"
    CRASH = "crash"
    ERROR = "error"


class BaseBotRunner(ABC):
    """Abstract base class for bot runners."""
    
    def __init__(
        self,
        bot_path: str,
        bot_name: str = "Unknown",
        resource_monitor: Optional[ResourceMonitor] = None
    ):
        """
        Initialize bot runner.
        
        Args:
            bot_path: Path to bot executable
            bot_name: Display name for the bot
            resource_monitor: Optional resource monitor for tracking
        """
        self.bot_path = bot_path
        self.bot_name = bot_name
        self.resource_monitor = resource_monitor or ResourceMonitor()
        self.turn_metrics: List[TurnMetrics] = []
        self.process: Optional[subprocess.Popen] = None
        self.current_turn = 0
        self.history_requests: List[str] = []  # Opponent's moves (requests to this bot)
        self.history_responses: List[str] = []  # This bot's moves (responses)
        
    @abstractmethod
    def play_turn(self, opponent_move: Optional[str] = None) -> Tuple[str, BotResult]:
        """
        Play a turn and return the move.
        
        Args:
            opponent_move: The opponent's last move, or None for first turn
            
        Returns:
            (move_string, result_status)
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up any resources."""
        pass
    
    def get_turn_metrics(self) -> List[TurnMetrics]:
        """Get metrics for all turns played."""
        return self.turn_metrics
    
    def _parse_move(self, output: str) -> Tuple[Optional[str], bool]:
        """
        Parse bot output to extract move.
        
        Returns:
            (move_string, is_keep_running)
        """
        lines = output.strip().split('\n')
        if not lines:
            return None, False
        
        move = lines[0].strip()
        is_keep_running = any(
            ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<" in line 
            for line in lines
        )
        
        return move, is_keep_running
    
    def _is_valid_move_format(self, move: str) -> bool:
        """Check if move has valid format (6 integers)."""
        try:
            parts = move.split()
            if len(parts) != 6:
                return False
            for p in parts:
                int(p)
            return True
        except ValueError:
            return False
    
    def _is_no_moves_signal(self, move: str) -> bool:
        """Check if move signals no legal moves available."""
        try:
            parts = [int(x) for x in move.split()]
            return parts == [-1, -1, -1, -1, -1, -1]
        except ValueError:
            return False


class TraditionalBot(BaseBotRunner):
    """
    Bot runner for traditional (non-long-live) bots.
    
    Restarts the bot process for each turn, sending full history.
    This matches the standard Botzone interaction protocol.
    """
    
    def __init__(
        self,
        bot_path: str,
        bot_name: str = "Unknown",
        resource_monitor: Optional[ResourceMonitor] = None
    ):
        super().__init__(bot_path, bot_name, resource_monitor)
        
    def play_turn(self, opponent_move: Optional[str] = None) -> Tuple[str, BotResult]:
        """
        Play a turn by starting a fresh process.
        
        For traditional bots, we:
        1. Start a new process
        2. Send turn number
        3. Send full history (requests and responses interleaved)
        4. Wait for response
        5. Terminate process
        """
        self.current_turn += 1
        is_first_turn = (self.current_turn == 1)
        
        # Update history with opponent's move
        if opponent_move:
            self.history_requests.append(opponent_move)
        elif is_first_turn:
            # First turn for black gets -1 -1 -1 -1 -1 -1
            self.history_requests.append("-1 -1 -1 -1 -1 -1")
        
        # Build input for bot
        input_data = self._build_input()
        
        # Get time limit
        time_limit = self.resource_monitor.get_time_limit(is_first_turn)
        
        # Use longer timeout when not enforcing limits (unlimited mode)
        if self.resource_monitor.enforce_limits:
            subprocess_timeout = time_limit + 0.5  # Small buffer for process overhead
        else:
            subprocess_timeout = 300.0  # 5 minutes for unlimited mode
        
        # Start process and measure time
        start_time = time.perf_counter()
        
        try:
            self.process = subprocess.Popen(
                [self.bot_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            pid = self.process.pid
            
            # Start memory sampling in background
            memory_sampler = MemorySampler(pid, sample_interval=0.01)
            memory_sampler.start()
            
            # Send input and wait for response
            try:
                stdout, stderr = self.process.communicate(
                    input=input_data,
                    timeout=subprocess_timeout
                )
            except subprocess.TimeoutExpired:
                elapsed = time.perf_counter() - start_time
                
                # Stop memory sampling and get peak
                memory = memory_sampler.stop()
                
                self._kill_process()
                
                # Record metrics
                metrics = self.resource_monitor.measure_turn(
                    pid=pid,
                    turn_number=self.current_turn,
                    elapsed_time=elapsed,
                    is_first_turn=is_first_turn
                )
                metrics.memory_bytes = memory
                metrics.violation = ViolationType.TIME_LIMIT_EXCEEDED
                self.turn_metrics.append(metrics)
                
                return "", BotResult.TIMEOUT
            
            elapsed = time.perf_counter() - start_time
            
            # Stop memory sampling and get peak memory
            memory = memory_sampler.stop()
            
            # Record metrics
            metrics = self.resource_monitor.measure_turn(
                pid=pid,
                turn_number=self.current_turn,
                elapsed_time=elapsed,
                is_first_turn=is_first_turn
            )
            # Use sampled peak memory
            metrics.memory_bytes = memory
            self.turn_metrics.append(metrics)
            
            # Check for time violation
            if metrics.violation == ViolationType.TIME_LIMIT_EXCEEDED:
                self._kill_process()
                return "", BotResult.TIMEOUT
            
            # Check for memory violation
            if metrics.violation == ViolationType.MEMORY_LIMIT_EXCEEDED:
                self._kill_process()
                return "", BotResult.MEMORY_EXCEEDED
            
            # Parse output
            move, _ = self._parse_move(stdout)
            
            if not move:
                return "", BotResult.INVALID_OUTPUT
            
            # Check for no moves signal
            if self._is_no_moves_signal(move):
                return move, BotResult.NO_MOVES
            
            # Validate move format
            if not self._is_valid_move_format(move):
                return move, BotResult.INVALID_OUTPUT
            
            # Record this bot's response
            self.history_responses.append(move)
            
            return move, BotResult.SUCCESS
            
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            print(f"  Error running {self.bot_name}: {e}")
            self._kill_process()
            return "", BotResult.CRASH
        finally:
            self._kill_process()
    
    def _build_input(self) -> str:
        """Build the input string for the bot following Botzone protocol."""
        lines = []
        
        # Turn number
        lines.append(str(self.current_turn))
        
        # Interleave requests and responses
        # Format: req1, resp1, req2, resp2, ..., req_n
        # Total lines: 2 * turn - 1
        for i in range(self.current_turn):
            if i < len(self.history_requests):
                lines.append(self.history_requests[i])
            if i < len(self.history_responses):
                lines.append(self.history_responses[i])
        
        return '\n'.join(lines) + '\n'
    
    def _kill_process(self):
        """Kill the bot process if running."""
        if self.process:
            try:
                self.process.kill()
                self.process.wait(timeout=1)
            except:
                pass
            self.process = None
    
    def cleanup(self):
        """Clean up resources."""
        self._kill_process()


class LongLiveBot(BaseBotRunner):
    """
    Bot runner for long-live (keep-running) bots.
    
    Keeps the bot process running between turns, sending only
    the opponent's move each turn (except first turn which sends full protocol).
    """
    
    def __init__(
        self,
        bot_path: str,
        bot_name: str = "Unknown",
        resource_monitor: Optional[ResourceMonitor] = None
    ):
        super().__init__(bot_path, bot_name, resource_monitor)
        self.is_running = False
        
    def _start_process(self):
        """Start the bot process."""
        if self.process is None or self.process.poll() is not None:
            self.process = subprocess.Popen(
                [self.bot_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            self.is_running = False
    
    def _read_line_with_timeout(self, timeout: float) -> Optional[str]:
        """Read a line from stdout with timeout."""
        if not self.process or not self.process.stdout:
            return None
        
        start = time.perf_counter()
        while time.perf_counter() - start < timeout:
            ready = select.select([self.process.stdout], [], [], 0.01)
            if ready[0]:
                line = self.process.stdout.readline()
                if line:
                    return line.strip()
                else:
                    # EOF - process likely terminated
                    return None
        return None
    
    def play_turn(self, opponent_move: Optional[str] = None) -> Tuple[str, BotResult]:
        """
        Play a turn in keep-running mode.
        
        First turn: Send turn number and request, wait for response + keep-running signal.
        Subsequent turns: Send only opponent's move, wait for response + keep-running signal.
        """
        self.current_turn += 1
        is_first_turn = (self.current_turn == 1)
        
        # Ensure process is started
        self._start_process()
        
        # Update history
        if opponent_move:
            self.history_requests.append(opponent_move)
        elif is_first_turn:
            self.history_requests.append("-1 -1 -1 -1 -1 -1")
        
        # Get time limit
        time_limit = self.resource_monitor.get_time_limit(is_first_turn)
        
        # Use longer timeout when not enforcing limits (unlimited mode)
        if self.resource_monitor.enforce_limits:
            read_timeout = time_limit
        else:
            read_timeout = 300.0  # 5 minutes for unlimited mode
        
        # Start timing
        start_time = time.perf_counter()
        pid = self.process.pid if self.process else 0
        
        # Start memory sampling
        memory_sampler = MemorySampler(pid, sample_interval=0.01)
        memory_sampler.start()
        
        try:
            if is_first_turn or not self.is_running:
                # Send full protocol: turn number + request
                input_data = f"1\n{self.history_requests[0]}\n"
                self.process.stdin.write(input_data)
                self.process.stdin.flush()
            else:
                # Send only opponent's move
                self.process.stdin.write(f"{opponent_move}\n")
                self.process.stdin.flush()
            
            # Wait for response
            move = self._read_line_with_timeout(read_timeout)
            
            elapsed = time.perf_counter() - start_time
            
            if move is None:
                # Stop memory sampling
                memory = memory_sampler.stop()
                
                # Timeout or process died
                metrics = self.resource_monitor.measure_turn(
                    pid=pid,
                    turn_number=self.current_turn,
                    elapsed_time=elapsed,
                    is_first_turn=is_first_turn
                )
                metrics.memory_bytes = memory
                if elapsed >= time_limit:
                    metrics.violation = ViolationType.TIME_LIMIT_EXCEEDED
                    self.turn_metrics.append(metrics)
                    return "", BotResult.TIMEOUT
                else:
                    self.turn_metrics.append(metrics)
                    return "", BotResult.CRASH
            
            # Check if we accidentally read the keep-running signal from previous turn
            # This can happen if the signal wasn't fully consumed on the previous turn
            if move == ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<":
                # Read the actual move
                move = self._read_line_with_timeout(read_timeout)
                if move is None:
                    elapsed = time.perf_counter() - start_time
                    memory = memory_sampler.stop()
                    
                    metrics = self.resource_monitor.measure_turn(
                        pid=pid,
                        turn_number=self.current_turn,
                        elapsed_time=elapsed,
                        is_first_turn=is_first_turn
                    )
                    metrics.memory_bytes = memory
                    self.turn_metrics.append(metrics)
                    return "", BotResult.CRASH
            
            # Check for keep-running signal
            keep_signal = self._read_line_with_timeout(0.5)
            if keep_signal == ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<":
                self.is_running = True
            else:
                # Bot didn't output keep-running signal
                # It might have output something else or nothing
                self.is_running = False
            
            # Stop memory sampling and record metrics
            elapsed = time.perf_counter() - start_time
            memory = memory_sampler.stop()
            
            metrics = self.resource_monitor.measure_turn(
                pid=pid,
                turn_number=self.current_turn,
                elapsed_time=elapsed,
                is_first_turn=is_first_turn
            )
            metrics.memory_bytes = memory
            self.turn_metrics.append(metrics)
            
            # Check for violations
            if metrics.violation == ViolationType.TIME_LIMIT_EXCEEDED:
                return "", BotResult.TIMEOUT
            if metrics.violation == ViolationType.MEMORY_LIMIT_EXCEEDED:
                return "", BotResult.MEMORY_EXCEEDED
            
            # Check for no moves signal
            if self._is_no_moves_signal(move):
                self.history_responses.append(move)
                return move, BotResult.NO_MOVES
            
            # Validate move format
            if not self._is_valid_move_format(move):
                return move, BotResult.INVALID_OUTPUT
            
            # Record response
            self.history_responses.append(move)
            
            return move, BotResult.SUCCESS
            
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            print(f"  Error with {self.bot_name}: {e}")
            return "", BotResult.ERROR
    
    def _kill_process(self):
        """Kill the bot process."""
        if self.process:
            try:
                self.process.kill()
                self.process.wait(timeout=1)
            except:
                pass
            self.process = None
            self.is_running = False
    
    def cleanup(self):
        """Clean up resources."""
        self._kill_process()


def detect_bot_type(bot_path: str, timeout: float = 3.0) -> BotType:
    """
    Detect bot type by running first turn and checking for keep-running signal.
    
    Args:
        bot_path: Path to bot executable
        timeout: Timeout for detection
        
    Returns:
        BotType.LONG_LIVE if bot uses keep-running mode
        BotType.TRADITIONAL if bot exits after turn
        BotType.UNKNOWN if detection fails
    """
    try:
        process = subprocess.Popen(
            [bot_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Send first turn input
        input_data = "1\n-1 -1 -1 -1 -1 -1\n"
        
        try:
            stdout, _ = process.communicate(input=input_data, timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            # Process still running after timeout - might be keep-running
            return BotType.LONG_LIVE
        
        # Check output for keep-running signal
        if ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<" in stdout:
            return BotType.LONG_LIVE
        else:
            return BotType.TRADITIONAL
            
    except Exception as e:
        print(f"  Error detecting bot type: {e}")
        return BotType.UNKNOWN


def create_bot_runner(
    bot_path: str,
    bot_name: str = "Unknown",
    resource_monitor: Optional[ResourceMonitor] = None,
    bot_type: Optional[BotType] = None
) -> BaseBotRunner:
    """
    Factory function to create appropriate bot runner.
    
    Args:
        bot_path: Path to bot executable
        bot_name: Display name for the bot
        resource_monitor: Optional resource monitor
        bot_type: If None, auto-detect; otherwise use specified type
        
    Returns:
        Appropriate bot runner instance
    """
    if bot_type is None:
        bot_type = detect_bot_type(bot_path)
        print(f"  Detected {bot_name} as {bot_type.value} bot")
    
    if bot_type == BotType.LONG_LIVE:
        return LongLiveBot(bot_path, bot_name, resource_monitor)
    else:
        # Default to traditional for unknown types
        return TraditionalBot(bot_path, bot_name, resource_monitor)


# Legacy compatibility alias
ProperBot = LongLiveBot