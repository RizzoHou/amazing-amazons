"""
Game engine module for running Amazons games.

Features:
- Proper game end detection matching Botzone behavior
- Support for both long-live and traditional bots
- Integrated resource monitoring
- Move validation
- Detailed game analysis
"""

import sys
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

sys.path.insert(0, 'core')
from game import Board, BLACK, WHITE

from .bot_runner import (
    BaseBotRunner, BotResult, BotType,
    create_bot_runner, TraditionalBot, LongLiveBot
)
from .resource_monitor import (
    ResourceMonitor, TurnMetrics, GameMetrics,
    ViolationType, format_time, format_bytes
)


class GameEndReason(Enum):
    """Reason for game ending."""
    NO_MOVES = "no_moves"           # Player has no legal moves
    TIMEOUT = "timeout"             # Player exceeded time limit
    MEMORY_EXCEEDED = "memory"      # Player exceeded memory limit
    INVALID_MOVE = "invalid_move"   # Player made an illegal move
    CRASH = "crash"                 # Player's bot crashed
    ERROR = "error"                 # Other error
    MAX_TURNS = "max_turns"         # Maximum turns reached


@dataclass
class GameResult:
    """Complete result of a game."""
    winner: Optional[str] = None
    loser: Optional[str] = None
    end_reason: GameEndReason = GameEndReason.NO_MOVES
    total_turns: int = 0
    moves: List[str] = field(default_factory=list)
    bot1_metrics: Optional[GameMetrics] = None
    bot2_metrics: Optional[GameMetrics] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "winner": self.winner,
            "loser": self.loser,
            "end_reason": self.end_reason.value,
            "total_turns": self.total_turns,
            "moves": self.moves,
            "error_message": self.error_message,
            "bot1_stats": self._metrics_to_dict(self.bot1_metrics) if self.bot1_metrics else None,
            "bot2_stats": self._metrics_to_dict(self.bot2_metrics) if self.bot2_metrics else None,
        }
    
    def _metrics_to_dict(self, m: GameMetrics) -> Dict[str, Any]:
        return {
            "bot_name": m.bot_name,
            "total_time": m.total_time,
            "total_turns": m.total_turns,
            "first_turn_time": m.first_turn_time,
            "avg_time": m.avg_time,
            "max_time": m.max_time,
            "min_time": m.min_time if m.min_time != float('inf') else 0,
            "avg_memory_mb": m.avg_memory / (1024 * 1024) if m.avg_memory else 0,
            "max_memory_mb": m.max_memory / (1024 * 1024) if m.max_memory else 0,
        }


class GameEngine:
    """
    Game engine that manages Amazons games between two bots.
    
    Follows Botzone protocol exactly:
    - Black moves first
    - Game ends when a player has no legal moves (opponent wins)
    - Game ends on timeout, memory limit, invalid move, or crash
    """
    
    MAX_TURNS = 200  # Safety limit to prevent infinite games
    
    def __init__(
        self,
        bot1_path: str,
        bot2_path: str,
        bot1_name: str = "Bot1",
        bot2_name: str = "Bot2",
        resource_monitor: Optional[ResourceMonitor] = None,
        verbose: bool = True,
        bot1_type: Optional[BotType] = None,
        bot2_type: Optional[BotType] = None
    ):
        """
        Initialize game engine.
        
        Args:
            bot1_path: Path to first bot (Black)
            bot2_path: Path to second bot (White)
            bot1_name: Display name for first bot
            bot2_name: Display name for second bot
            resource_monitor: Optional resource monitor
            verbose: Whether to print progress
            bot1_type: Force bot type (None for auto-detect)
            bot2_type: Force bot type (None for auto-detect)
        """
        self.bot1_name = bot1_name
        self.bot2_name = bot2_name
        self.resource_monitor = resource_monitor or ResourceMonitor()
        self.verbose = verbose
        
        # Create bot runners
        self.bot1 = create_bot_runner(
            bot1_path, bot1_name, self.resource_monitor, bot1_type
        )
        self.bot2 = create_bot_runner(
            bot2_path, bot2_name, self.resource_monitor, bot2_type
        )
        
        # Game state
        self.board = Board()
        self.current_player = BLACK  # Black moves first
        self.moves: List[str] = []
        self.turn_number = 0
        
    def play(self) -> GameResult:
        """
        Play a complete game.
        
        Returns:
            GameResult with all game information
        """
        if self.verbose:
            print(f"\nStarting game: {self.bot1_name} (Black) vs {self.bot2_name} (White)")
        
        result = GameResult()
        result.moves = []
        
        try:
            while self.turn_number < self.MAX_TURNS:
                self.turn_number += 1
                
                # Determine current bot
                is_black_turn = (self.current_player == BLACK)
                current_bot = self.bot1 if is_black_turn else self.bot2
                current_name = self.bot1_name if is_black_turn else self.bot2_name
                opponent_name = self.bot2_name if is_black_turn else self.bot1_name
                
                if self.verbose:
                    print(f"  Turn {self.turn_number}: {current_name}'s move...")
                
                # Get opponent's last move (or None for first turn)
                opponent_move = self.moves[-1] if self.moves else None
                
                # Play turn
                move, bot_result = current_bot.play_turn(opponent_move)
                
                # Handle result
                if bot_result == BotResult.TIMEOUT:
                    result.winner = opponent_name
                    result.loser = current_name
                    result.end_reason = GameEndReason.TIMEOUT
                    result.error_message = f"{current_name} exceeded time limit"
                    if self.verbose:
                        print(f"    {current_name} TIMEOUT")
                    break
                
                if bot_result == BotResult.MEMORY_EXCEEDED:
                    result.winner = opponent_name
                    result.loser = current_name
                    result.end_reason = GameEndReason.MEMORY_EXCEEDED
                    result.error_message = f"{current_name} exceeded memory limit"
                    if self.verbose:
                        print(f"    {current_name} MEMORY EXCEEDED")
                    break
                
                if bot_result == BotResult.CRASH:
                    result.winner = opponent_name
                    result.loser = current_name
                    result.end_reason = GameEndReason.CRASH
                    result.error_message = f"{current_name} crashed"
                    if self.verbose:
                        print(f"    {current_name} CRASHED")
                    break
                
                if bot_result == BotResult.INVALID_OUTPUT:
                    result.winner = opponent_name
                    result.loser = current_name
                    result.end_reason = GameEndReason.INVALID_MOVE
                    result.error_message = f"{current_name} produced invalid output: {move}"
                    if self.verbose:
                        print(f"    {current_name} INVALID OUTPUT: {move}")
                    break
                
                if bot_result == BotResult.NO_MOVES:
                    result.winner = opponent_name
                    result.loser = current_name
                    result.end_reason = GameEndReason.NO_MOVES
                    if self.verbose:
                        print(f"    {current_name} has no legal moves")
                    break
                
                if bot_result == BotResult.ERROR:
                    result.winner = opponent_name
                    result.loser = current_name
                    result.end_reason = GameEndReason.ERROR
                    result.error_message = f"{current_name} encountered an error"
                    if self.verbose:
                        print(f"    {current_name} ERROR")
                    break
                
                # Validate and apply move
                validation_result = self._validate_and_apply_move(move)
                if validation_result is not None:
                    result.winner = opponent_name
                    result.loser = current_name
                    result.end_reason = GameEndReason.INVALID_MOVE
                    result.error_message = f"{current_name}: {validation_result}"
                    if self.verbose:
                        print(f"    {current_name} INVALID MOVE: {validation_result}")
                    break
                
                # Record move
                self.moves.append(move)
                result.moves.append(move)
                
                if self.verbose:
                    print(f"    {current_name} plays: {move}")
                
                # Switch player
                self.current_player = WHITE if self.current_player == BLACK else BLACK
            
            else:
                # Max turns reached
                result.end_reason = GameEndReason.MAX_TURNS
                result.error_message = f"Game exceeded {self.MAX_TURNS} turns"
                if self.verbose:
                    print(f"  Game exceeded maximum turns ({self.MAX_TURNS})")
            
        except Exception as e:
            result.error_message = f"Game error: {str(e)}"
            result.end_reason = GameEndReason.ERROR
            if self.verbose:
                print(f"  Game error: {e}")
        
        finally:
            # Clean up bots
            self.bot1.cleanup()
            self.bot2.cleanup()
        
        # Compute metrics
        result.total_turns = len(result.moves)
        result.bot1_metrics = self.resource_monitor.compute_game_metrics(
            self.bot1_name, self.bot1.get_turn_metrics()
        )
        result.bot2_metrics = self.resource_monitor.compute_game_metrics(
            self.bot2_name, self.bot2.get_turn_metrics()
        )
        
        if self.verbose:
            self._print_summary(result)
        
        return result
    
    def _validate_and_apply_move(self, move: str) -> Optional[str]:
        """
        Validate move and apply to board.
        
        Returns:
            None if valid, error message if invalid
        """
        try:
            parts = [int(x) for x in move.split()]
            if len(parts) != 6:
                return f"Move must have 6 integers, got {len(parts)}"
            
            x0, y0, x1, y1, x2, y2 = parts
            
            # Check if piece exists at start position
            if self.board.grid[x0, y0] != self.current_player:
                return f"No piece at ({x0}, {y0}) for current player"
            
            # Check if destination is empty
            if self.board.grid[x1, y1] != 0:  # EMPTY = 0
                return f"Destination ({x1}, {y1}) is not empty"
            
            # Check if arrow position is valid
            # After moving piece, arrow can go to original position or any empty square
            if self.board.grid[x2, y2] != 0 and not (x2 == x0 and y2 == y0):
                return f"Arrow position ({x2}, {y2}) is not valid"
            
            # Apply move
            move_tuple = (x0, y0, x1, y1, x2, y2)
            self.board.apply_move(move_tuple)
            
            return None
            
        except ValueError as e:
            return f"Invalid move format: {e}"
        except Exception as e:
            return f"Error applying move: {e}"
    
    def _print_summary(self, result: GameResult):
        """Print game summary."""
        print(f"\n{'='*50}")
        print(f"GAME SUMMARY")
        print(f"{'='*50}")
        
        if result.winner:
            print(f"Winner: {result.winner}")
            print(f"Reason: {result.end_reason.value}")
        else:
            print(f"No winner (game ended due to {result.end_reason.value})")
        
        print(f"Total turns: {result.total_turns}")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        # Print timing stats
        for metrics in [result.bot1_metrics, result.bot2_metrics]:
            if metrics and metrics.total_turns > 0:
                print(f"\n{metrics.bot_name} Statistics:")
                print(f"  First turn time: {format_time(metrics.first_turn_time)}")
                if metrics.total_turns > 1:
                    print(f"  Avg turn time: {format_time(metrics.avg_time)}")
                    print(f"  Max turn time: {format_time(metrics.max_time)} (turn {metrics.max_time_turn})")
                    print(f"  Min turn time: {format_time(metrics.min_time)} (turn {metrics.min_time_turn})")
                if metrics.max_memory > 0:
                    print(f"  Avg memory: {format_bytes(metrics.avg_memory)}")
                    print(f"  Max memory: {format_bytes(metrics.max_memory)}")


# Legacy compatibility - keep FixedGame for backwards compatibility
class FixedGame:
    """Legacy compatibility wrapper for GameEngine."""
    
    def __init__(
        self,
        bot1_cmd: List[str],
        bot2_cmd: List[str],
        bot1_name: str = "Bot1",
        bot2_name: str = "Bot2"
    ):
        bot1_path = bot1_cmd[0] if isinstance(bot1_cmd, list) else bot1_cmd
        bot2_path = bot2_cmd[0] if isinstance(bot2_cmd, list) else bot2_cmd
        
        self.engine = GameEngine(
            bot1_path, bot2_path, bot1_name, bot2_name,
            verbose=True
        )
        self.bot1_name = bot1_name
        self.bot2_name = bot2_name
        self.moves = []
        self.winner = None
        self.error = None
    
    def play(self) -> Tuple[Optional[str], List[str]]:
        """Play game and return (winner, moves)."""
        result = self.engine.play()
        
        self.moves = result.moves
        self.winner = result.winner
        self.error = result.error_message
        
        if result.error_message and not result.winner:
            return result.error_message, result.moves
        
        return result.winner, result.moves
