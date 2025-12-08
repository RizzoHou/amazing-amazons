import numpy as np

# Board constants
GRID_SIZE = 8
EMPTY = 0
BLACK = 1
WHITE = -1
OBSTACLE = 2

# Directions for Queen moves (and arrows)
# (dx, dy)
DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
]

class Board:
    def __init__(self):
        self.grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
        self.init_board()

    def init_board(self):
        # Initial positions for Amazons
        # Black
        self.grid[0, 2] = BLACK
        self.grid[2, 0] = BLACK
        self.grid[5, 0] = BLACK
        self.grid[7, 2] = BLACK
        
        # White
        self.grid[0, 5] = WHITE
        self.grid[2, 7] = WHITE
        self.grid[5, 7] = WHITE
        self.grid[7, 5] = WHITE

    def is_valid(self, x, y):
        return 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE

    def get_legal_moves(self, color):
        """
        Generator for legal moves.
        Yields: (x0, y0, x1, y1, x2, y2)
        """
        moves = []
        # Find all pieces of the given color
        pieces = np.argwhere(self.grid == color)
        
        for px, py in pieces:
            # 1. Move the piece
            for dx, dy in DIRECTIONS:
                nx, ny = px + dx, py + dy
                while self.is_valid(nx, ny) and self.grid[nx, ny] == EMPTY:
                    # Piece moves from (px, py) to (nx, ny)
                    
                    # Temporarily move piece to check for arrow shots
                    # Note: The starting square (px, py) becomes empty and is a valid target for the arrow!
                    # BUT the arrow originates from (nx, ny).
                    
                    # Optimization: We don't modify the grid here to avoid copying cost in the loop.
                    # We just need to know that (px, py) is treated as empty for the arrow shot,
                    # and (nx, ny) is occupied (by the piece).
                    
                    # 2. Shoot arrow from (nx, ny)
                    for adx, ady in DIRECTIONS:
                        ax, ay = nx + adx, ny + ady
                        while self.is_valid(ax, ay):
                            # Check if blocked. 
                            # If (ax, ay) is (px, py), it's empty (valid).
                            # If (ax, ay) is anything else non-empty, it's blocked.
                            is_blocked = False
                            if self.grid[ax, ay] != EMPTY:
                                if ax == px and ay == py:
                                    pass # Valid, this is the old position
                                else:
                                    is_blocked = True
                            
                            if is_blocked:
                                break
                                
                            moves.append((px, py, nx, ny, ax, ay))
                            ax += adx
                            ay += ady
                    
                    nx += dx
                    ny += dy
        return moves

    def apply_move(self, move):
        """
        Apply a move tuple (x0, y0, x1, y1, x2, y2) to the board.
        Does NOT check validity. Assumes move is valid.
        """
        x0, y0, x1, y1, x2, y2 = move
        piece = self.grid[x0, y0]
        self.grid[x0, y0] = EMPTY
        self.grid[x1, y1] = piece
        self.grid[x2, y2] = OBSTACLE

    def copy(self):
        new_board = Board()
        new_board.grid = self.grid.copy()
        return new_board
