#!/usr/bin/env python3
"""
Debug script to check board state and legal moves.
"""

import sys
sys.path.insert(0, 'core')
from game import Board, BLACK, WHITE, EMPTY, OBSTACLE


def print_board(board):
    """Print the board in a readable format"""
    print("  " + " ".join(str(i) for i in range(8)))
    for y in range(8):
        row = []
        for x in range(8):
            val = board.grid[x, y]
            if val == EMPTY:
                row.append(".")
            elif val == BLACK:
                row.append("B")
            elif val == WHITE:
                row.append("W")
            elif val == OBSTACLE:
                row.append("X")
        print(f"{y} " + " ".join(row))


def main():
    """Recreate the board state from the match that failed"""
    print("Debugging board state issue")
    print("=" * 60)
    
    # Create board and apply moves from the match
    board = Board()
    
    # Moves from the match (up to turn 51)
    moves = [
        (2, 0, 2, 6, 7, 6),  # Turn 1: bot000
        (5, 0, 5, 6, 0, 6),  # Turn 2: bot003
        (0, 2, 2, 2, 4, 2),  # Turn 3: bot000
        (2, 2, 2, 4, 1, 4),  # Turn 4: bot003
        (2, 4, 2, 2, 0, 4),  # Turn 5: bot000
        (2, 2, 2, 4, 6, 4),  # Turn 6: bot003
        (2, 4, 2, 1, 2, 4),  # Turn 7: bot000
        (2, 1, 4, 3, 1, 6),  # Turn 8: bot003
        (4, 3, 2, 1, 5, 4),  # Turn 9: bot000
        (2, 1, 2, 3, 5, 3),  # Turn 10: bot003
        (7, 2, 5, 2, 7, 4),  # Turn 11: bot000
        (2, 3, 3, 4, 4, 4),  # Turn 12: bot003
        (3, 4, 1, 2, 3, 4),  # Turn 13: bot000
        (5, 6, 4, 6, 7, 6),  # Turn 14: bot003
        (4, 6, 6, 6, 6, 7),  # Turn 15: bot000
        (6, 6, 3, 6, 6, 6),  # Turn 16: bot003
        (3, 6, 5, 6, 6, 5),  # Turn 17: bot000
        (5, 6, 2, 6, 5, 6),  # Turn 18: bot003
        (2, 6, 3, 6, 4, 6),  # Turn 19: bot000
        (3, 6, 2, 6, 1, 5),  # Turn 20: bot003
        (2, 6, 3, 6, 2, 6),  # Turn 21: bot000
        (5, 2, 6, 1, 4, 1),  # Turn 22: bot003
        (1, 2, 2, 1, 4, 3),  # Turn 23: bot000
        (2, 1, 1, 2, 3, 2),  # Turn 24: bot003
        (1, 2, 1, 1, 3, 3),  # Turn 25: bot000
        (1, 1, 1, 2, 2, 3),  # Turn 26: bot003
        (1, 2, 1, 1, 1, 3),  # Turn 27: bot000
        (2, 0, 4, 0, 7, 3),  # Turn 28: bot003
        (1, 1, 2, 1, 0, 3),  # Turn 29: bot000
        (2, 1, 1, 1, 0, 2),  # Turn 30: bot003
        (1, 1, 2, 1, 0, 1),  # Turn 31: bot000
        (4, 0, 5, 0, 0, 0),  # Turn 32: bot003
        (6, 1, 6, 2, 6, 3),  # Turn 33: bot000
        (6, 2, 6, 1, 7, 2),  # Turn 34: bot003
        (6, 1, 5, 1, 7, 1),  # Turn 35: bot000
        (5, 0, 7, 0, 5, 2),  # Turn 36: bot003
        (3, 6, 4, 5, 3, 6),  # Turn 37: bot000
        (4, 5, 3, 5, 5, 5),  # Turn 38: bot003
        (5, 1, 6, 1, 7, 0),  # Turn 39: bot000
        (6, 1, 5, 1, 4, 0),  # Turn 40: bot003
        (2, 1, 2, 0, 2, 2),  # Turn 41: bot000
        (2, 0, 2, 1, 1, 2),  # Turn 42: bot003
        (5, 1, 6, 1, 6, 2),  # Turn 43: bot000
        (2, 1, 1, 0, 3, 0),  # Turn 44: bot003
        (1, 0, 1, 1, 3, 1),  # Turn 45: bot000
        (3, 5, 2, 5, 4, 5),  # Turn 46: bot003
        (2, 5, 3, 5, 2, 5),  # Turn 47: bot000
        (1, 1, 2, 1, 1, 0),  # Turn 48: bot003
        (6, 1, 6, 0, 5, 0),  # Turn 49: bot000
        (2, 1, 2, 0, 1, 1),  # Turn 50: bot003
        (2, 0, 2, 1, 2, 0),  # Turn 51: bot000
        (6, 0, 6, 1, 5, 1),  # Turn 52: bot003
        (6, 1, 6, 0, 6, 1),  # Turn 53: bot000
    ]
    
    print("Initial board:")
    print_board(board)
    
    # Apply all moves
    for i, move in enumerate(moves):
        print(f"\nApplying move {i+1}: {move}")
        board.apply_move(move)
        print_board(board)
    
    # Now check legal moves for White (bot003's turn)
    print("\n" + "=" * 60)
    print("Checking legal moves for White (bot003's turn at move 54)")
    
    legal_moves = list(board.get_legal_moves(WHITE))
    print(f"Number of legal moves for White: {len(legal_moves)}")
    
    if legal_moves:
        print("First 5 legal moves:")
        for i, move in enumerate(legal_moves[:5]):
            print(f"  {i+1}: {move}")
    else:
        print("White has NO legal moves! Game should have ended.")
        print("The bot returning '-1 -1 -1 -1 -1 -1' is correct.")
    
    # Also check legal moves for Black
    print("\nChecking legal moves for Black:")
    legal_moves_black = list(board.get_legal_moves(BLACK))
    print(f"Number of legal moves for Black: {len(legal_moves_black)}")


if __name__ == "__main__":
    main()
