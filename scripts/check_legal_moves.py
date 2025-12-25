#!/usr/bin/env python3
"""
Check legal moves in detail.
"""

import sys
sys.path.insert(0, 'core')
from game import Board, BLACK, WHITE, EMPTY, OBSTACLE
import numpy as np


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
    """Check legal moves in detail"""
    # Recreate the exact board state from debug_board.py
    board = Board()
    
    # Apply all 53 moves from the match
    moves = [
        (2, 0, 2, 6, 7, 6), (5, 0, 5, 6, 0, 6), (0, 2, 2, 2, 4, 2),
        (2, 2, 2, 4, 1, 4), (2, 4, 2, 2, 0, 4), (2, 2, 2, 4, 6, 4),
        (2, 4, 2, 1, 2, 4), (2, 1, 4, 3, 1, 6), (4, 3, 2, 1, 5, 4),
        (2, 1, 2, 3, 5, 3), (7, 2, 5, 2, 7, 4), (2, 3, 3, 4, 4, 4),
        (3, 4, 1, 2, 3, 4), (5, 6, 4, 6, 7, 6), (4, 6, 6, 6, 6, 7),
        (6, 6, 3, 6, 6, 6), (3, 6, 5, 6, 6, 5), (5, 6, 2, 6, 5, 6),
        (2, 6, 3, 6, 4, 6), (3, 6, 2, 6, 1, 5), (2, 6, 3, 6, 2, 6),
        (5, 2, 6, 1, 4, 1), (1, 2, 2, 1, 4, 3), (2, 1, 1, 2, 3, 2),
        (1, 2, 1, 1, 3, 3), (1, 1, 1, 2, 2, 3), (1, 2, 1, 1, 1, 3),
        (2, 0, 4, 0, 7, 3), (1, 1, 2, 1, 0, 3), (2, 1, 1, 1, 0, 2),
        (1, 1, 2, 1, 0, 1), (4, 0, 5, 0, 0, 0), (6, 1, 6, 2, 6, 3),
        (6, 2, 6, 1, 7, 2), (6, 1, 5, 1, 7, 1), (5, 0, 7, 0, 5, 2),
        (3, 6, 4, 5, 3, 6), (4, 5, 3, 5, 5, 5), (5, 1, 6, 1, 7, 0),
        (6, 1, 5, 1, 4, 0), (2, 1, 2, 0, 2, 2), (2, 0, 2, 1, 1, 2),
        (5, 1, 6, 1, 6, 2), (2, 1, 1, 0, 3, 0), (1, 0, 1, 1, 3, 1),
        (3, 5, 2, 5, 4, 5), (2, 5, 3, 5, 2, 5), (1, 1, 2, 1, 1, 0),
        (6, 1, 6, 0, 5, 0), (2, 1, 2, 0, 1, 1), (2, 0, 2, 1, 2, 0),
        (6, 0, 6, 1, 5, 1), (6, 1, 6, 0, 6, 1)
    ]
    
    for move in moves:
        board.apply_move(move)
    
    print("Final board state:")
    print_board(board)
    
    print("\n" + "="*60)
    print("White pieces (W):")
    white_pieces = np.argwhere(board.grid == WHITE)
    for x, y in white_pieces:
        print(f"  Queen at ({x}, {y})")
    
    print("\nBlack pieces (B):")
    black_pieces = np.argwhere(board.grid == BLACK)
    for x, y in black_pieces:
        print(f"  Queen at ({x}, {y})")
    
    print("\n" + "="*60)
    print("Checking White's legal moves in detail:")
    
    legal_moves = list(board.get_legal_moves(WHITE))
    print(f"Total legal moves for White: {len(legal_moves)}")
    
    # Group moves by queen
    moves_by_queen = {}
    for move in legal_moves:
        x0, y0, x1, y1, x2, y2 = move
        queen_pos = (x0, y0)
        if queen_pos not in moves_by_queen:
            moves_by_queen[queen_pos] = []
        moves_by_queen[queen_pos].append(move)
    
    for queen_pos in moves_by_queen:
        print(f"\nQueen at {queen_pos} has {len(moves_by_queen[queen_pos])} moves:")
        for i, move in enumerate(moves_by_queen[queen_pos][:5]):  # Show first 5
            print(f"  {i+1}: {move[0]},{move[1]} -> {move[2]},{move[3]} arrow to {move[4]},{move[5]}")
        if len(moves_by_queen[queen_pos]) > 5:
            print(f"  ... and {len(moves_by_queen[queen_pos]) - 5} more")
    
    # Check if any moves seem obviously invalid
    print("\n" + "="*60)
    print("Validating a few moves:")
    
    if legal_moves:
        # Test the first move
        test_move = legal_moves[0]
        x0, y0, x1, y1, x2, y2 = test_move
        print(f"\nTesting move: {test_move}")
        
        # Check if start has White queen
        if board.grid[x0, y0] != WHITE:
            print(f"  ERROR: Start position ({x0},{y0}) doesn't have White queen")
        else:
            print(f"  OK: Start position has White queen")
        
        # Check if destination is empty
        if board.grid[x1, y1] != EMPTY:
            print(f"  ERROR: Destination ({x1},{y1}) is not empty")
        else:
            print(f"  OK: Destination is empty")
        
        # Check if arrow target is valid
        if board.grid[x2, y2] != EMPTY:
            print(f"  WARNING: Arrow target ({x2},{y2}) is not empty")
        else:
            print(f"  OK: Arrow target is empty")
        
        # Check path from start to destination
        print(f"  Checking queen move path...")
        dx = x1 - x0
        dy = y1 - y0
        if dx == 0 or dy == 0 or abs(dx) == abs(dy):
            # Valid direction
            step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
            step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
            
            x, y = x0 + step_x, y0 + step_y
            path_clear = True
            while (x, y) != (x1, y1):
                if board.grid[x, y] != EMPTY:
                    path_clear = False
                    print(f"    Blocked at ({x},{y})")
                    break
                x += step_x
                y += step_y
            
            if path_clear:
                print(f"  OK: Queen path is clear")
            else:
                print(f"  ERROR: Queen path is blocked")
        else:
            print(f"  ERROR: Not a valid queen move direction")
    
    print("\n" + "="*60)
    print("Checking if board is full:")
    empty_count = np.sum(board.grid == EMPTY)
    total_cells = 8 * 8
    print(f"Empty cells: {empty_count}/{total_cells}")
    print(f"Obstacles (X): {np.sum(board.grid == OBSTACLE)}")
    print(f"Black queens (B): {np.sum(board.grid == BLACK)}")
    print(f"White queens (W): {np.sum(board.grid == WHITE)}")


if __name__ == "__main__":
    main()
