"""
Game engine module for running Amazons games.

Contains the FixedGame class that manages game state and bot interactions.
"""

import sys
from typing import List, Tuple, Optional
sys.path.insert(0, 'core')
from game import Board, BLACK, WHITE

from .bot_runner import ProperBot


class FixedGame:
    """Fixed game class that uses ProperBot and tracks game state"""
    
    def __init__(self, bot1_cmd: List[str], bot2_cmd: List[str], 
                 bot1_name: str = "Bot1", bot2_name: str = "Bot2"):
        self.bot1 = ProperBot(bot1_cmd[0] if isinstance(bot1_cmd, list) else bot1_cmd, bot1_name)
        self.bot2 = ProperBot(bot2_cmd[0] if isinstance(bot2_cmd, list) else bot2_cmd, bot2_name)
        self.bot1_name = bot1_name
        self.bot2_name = bot2_name
        self.moves = []
        self.winner = None
        self.error = None
        self.board = Board()  # Track game state
        self.current_player = BLACK  # BLACK moves first
        
    def play(self) -> Tuple[Optional[str], List[str]]:
        """
        Play a game between two bots until natural end
        
        Returns:
            (winner_name_or_error, list_of_moves)
        """
        print(f"\nStarting game: {self.bot1_name} vs {self.bot2_name}")
        
        try:
            # Start both bots
            self.bot1.start()
            self.bot2.start()
            
            # Turn 1: bot1 (Black) first turn
            print(f"  Turn 1: {self.bot1_name}'s move...")
            move1 = self.bot1.play_first_turn(is_black=True)
            if not move1:
                self.error = f"{self.bot1_name} failed first turn"
                return self.error, self.moves
            
            # Check if move is valid and apply to board
            try:
                # Special case: bot might return keep-running signal as move (protocol error)
                if move1 == ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<":
                    # Bot error: returned keep-running signal as move
                    self.error = f"{self.bot1_name} protocol error: returned keep-running signal as move"
                    self.winner = self.bot2_name
                    return self.winner, self.moves
                
                move_tuple = tuple(map(int, move1.split()))
                if len(move_tuple) != 6:
                    self.error = f"{self.bot1_name} made invalid move: {move1}"
                    self.winner = self.bot2_name
                    return self.winner, self.moves
                
                # Check for no legal moves signal
                if move_tuple == (-1, -1, -1, -1, -1, -1):
                    self.winner = self.bot2_name
                    print(f"    {self.bot1_name} has no legal moves (signaled -1 -1 -1 -1 -1 -1)")
                    return self.winner, self.moves
                
                # Apply move to board
                self.board.apply_move(move_tuple)
                self.moves.append(move1)
                print(f"    {self.bot1_name} move: {move1}")
                self.current_player = WHITE  # Switch to White
            except Exception as e:
                self.error = f"{self.bot1_name} made invalid move: {move1} ({e})"
                self.winner = self.bot2_name
                return self.winner, self.moves
            
            # Turn 2: bot2 (White) first turn
            print(f"  Turn 2: {self.bot2_name}'s move...")
            move2 = self.bot2.play_first_turn(is_black=False)
            if not move2:
                self.error = f"{self.bot2_name} failed first turn"
                return self.error, self.moves
            
            # Check if move is valid and apply to board
            try:
                # Special case: bot might return keep-running signal as move (protocol error)
                if move2 == ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<":
                    # Bot error: returned keep-running signal as move
                    self.error = f"{self.bot2_name} protocol error: returned keep-running signal as move"
                    self.winner = self.bot1_name
                    return self.winner, self.moves
                
                move_tuple = tuple(map(int, move2.split()))
                if len(move_tuple) != 6:
                    self.error = f"{self.bot2_name} made invalid move: {move2}"
                    self.winner = self.bot1_name
                    return self.winner, self.moves
                
                # Check for no legal moves signal
                if move_tuple == (-1, -1, -1, -1, -1, -1):
                    self.winner = self.bot1_name
                    print(f"    {self.bot2_name} has no legal moves (signaled -1 -1 -1 -1 -1 -1)")
                    return self.winner, self.moves
                
                # Apply move to board
                self.board.apply_move(move_tuple)
                self.moves.append(move2)
                print(f"    {self.bot2_name} move: {move2}")
                self.current_player = BLACK  # Switch to Black
            except Exception as e:
                self.error = f"{self.bot2_name} made invalid move: {move2} ({e})"
                self.winner = self.bot1_name
                return self.winner, self.moves
            
            # Continue alternating until game ends naturally
            turn = 3
            while True:
                is_black_turn = (self.current_player == BLACK)
                current_bot = self.bot1 if is_black_turn else self.bot2
                opponent_bot = self.bot2 if is_black_turn else self.bot1
                current_name = self.bot1_name if is_black_turn else self.bot2_name
                
                print(f"  Turn {turn}: {current_name}'s move...")
                
                # Check if current player has any legal moves
                # get_legal_moves returns a generator, need to check if it yields any moves
                has_legal_moves = False
                for _ in self.board.get_legal_moves(self.current_player):
                    has_legal_moves = True
                    break
                
                if not has_legal_moves:
                    self.winner = opponent_bot.bot_name
                    print(f"  {current_name} has no legal moves (game ends)")
                    break
                
                # Get opponent's last move
                opponent_last_move = self.moves[-1]
                
                # Play turn in keep-running mode
                move = current_bot.play_turn_keep_running(opponent_last_move)
                
                if not move:
                    self.error = f"{current_name} failed to make a move"
                    self.winner = opponent_bot.bot_name
                    break
                
                # Check if move is valid and apply to board
                try:
                    # Special case: bot might return keep-running signal as move (protocol error)
                    if move == ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<":
                        # Check if player actually has legal moves
                        has_legal_moves_check = False
                        for _ in self.board.get_legal_moves(self.current_player):
                            has_legal_moves_check = True
                            break
                        
                        if not has_legal_moves_check:
                            # Bot is signaling no moves (in wrong way)
                            self.winner = opponent_bot.bot_name
                            print(f"    {current_name} has no legal moves (signaled with >>>BOTZONE_REQUEST_KEEP_RUNNING<<<)")
                            break
                        else:
                            # Bot error: has moves but returned wrong signal
                            self.error = f"{current_name} protocol error: returned keep-running signal as move"
                            self.winner = opponent_bot.bot_name
                            break
                    
                    move_tuple = tuple(map(int, move.split()))
                    if len(move_tuple) != 6:
                        self.error = f"{current_name} made invalid move: {move}"
                        self.winner = opponent_bot.bot_name
                        break
                    
                    # Check for no legal moves signal
                    if move_tuple == (-1, -1, -1, -1, -1, -1):
                        self.winner = opponent_bot.bot_name
                        print(f"    {current_name} has no legal moves (signaled -1 -1 -1 -1 -1 -1)")
                        break
                    
                    # Apply move to board
                    self.board.apply_move(move_tuple)
                    self.moves.append(move)
                    print(f"    {current_name} move: {move}")
                    
                    # Switch player
                    self.current_player = WHITE if self.current_player == BLACK else BLACK
                    
                except Exception as e:
                    self.error = f"{current_name} made invalid move: {move} ({e})"
                    self.winner = opponent_bot.bot_name
                    break
                
                turn += 1
            
        except Exception as e:
            self.error = f"Game error: {e}"
        finally:
            self.bot1.stop()
            self.bot2.stop()
        
        if self.error:
            print(f"  Game error: {self.error}")
            return self.error, self.moves
        else:
            print(f"  Game finished: {self.winner} wins in {len(self.moves)} moves")
            return self.winner, self.moves
