import sys
import time
import math
import random
import collections
import numpy as np

# --- GAME CONSTANTS & BOARD ---
GRID_SIZE = 8
EMPTY = 0
BLACK = 1
WHITE = -1
OBSTACLE = 2

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
        moves = []
        pieces = np.argwhere(self.grid == color)
        
        for px, py in pieces:
            for dx, dy in DIRECTIONS:
                nx, ny = px + dx, py + dy
                while self.is_valid(nx, ny) and self.grid[nx, ny] == EMPTY:
                    for adx, ady in DIRECTIONS:
                        ax, ay = nx + adx, ny + ady
                        while self.is_valid(ax, ay):
                            is_blocked = False
                            if self.grid[ax, ay] != EMPTY:
                                if ax == px and ay == py:
                                    pass
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
        x0, y0, x1, y1, x2, y2 = move
        piece = self.grid[x0, y0]
        self.grid[x0, y0] = EMPTY
        self.grid[x1, y1] = piece
        self.grid[x2, y2] = OBSTACLE

    def copy(self):
        new_board = Board()
        new_board.grid = self.grid.copy()
        return new_board


# --- AI MODULE ---

class MCTSNode:
    def __init__(self, parent=None, move=None, player_just_moved=None):
        self.parent = parent
        self.move = move
        self.children = []
        self.wins = 0.0
        self.visits = 0
        self.untried_moves = None
        self.player_just_moved = player_just_moved

    def uct_select_child(self, C):
        log_visits = math.log(self.visits)
        best_score = -float('inf')
        best_child = None
        
        for c in self.children:
            score = (c.wins / c.visits) + C * math.sqrt(log_visits / c.visits)
            if score > best_score:
                best_score = score
                best_child = c
        return best_child

# Game phase weights (simplified from opponent03's 28 sets to 3)
EARLY_WEIGHTS = [0.08, 0.06, 0.60, 0.68, 0.02]  # turns 1-10
MID_WEIGHTS = [0.13, 0.15, 0.45, 0.51, 0.07]    # turns 11-20  
LATE_WEIGHTS = [0.11, 0.15, 0.38, 0.45, 0.10]   # turns 21+

class MCTS:
    def __init__(self, time_limit=5.0):
        self.time_limit = time_limit
        self.root = None
        self.turn_number = 0

    def get_phase_weights(self, turn):
        """Get evaluation weights based on game phase"""
        if turn <= 10:
            return EARLY_WEIGHTS
        elif turn <= 20:
            return MID_WEIGHTS
        else:
            return LATE_WEIGHTS

    def get_ucb_constant(self, turn):
        """Dynamic UCB constant from opponent03"""
        return 0.177 * math.exp(-0.008 * (turn - 1.41))

    def bfs_territory(self, grid, pieces):
        """BFS-based territory calculation"""
        dist = np.full((GRID_SIZE, GRID_SIZE), 99, dtype=np.int8)
        q = collections.deque()
        
        for px, py in pieces:
            dist[px, py] = 0
            q.append((px, py, 0))
        
        territory_by_dist = collections.defaultdict(int)
        
        while q:
            x, y, d = q.popleft()
            nd = d + 1
            
            for dx, dy in DIRECTIONS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 8 and 0 <= ny < 8:
                    if grid[nx, ny] == EMPTY and dist[nx, ny] > nd:
                        dist[nx, ny] = nd
                        territory_by_dist[nd] += 1
                        q.append((nx, ny, nd))
        
        return territory_by_dist, dist

    def calc_position_score(self, pieces, dist_map):
        """Position score with exponential decay (2^-d)"""
        score = 0.0
        for i in range(1, 8):
            count = np.sum(dist_map == i)
            score += count * (2.0 ** (-i))
        return score

    def calc_mobility(self, grid, pieces):
        """Calculate mobility (available moves)"""
        mobility = 0
        for px, py in pieces:
            for dx, dy in DIRECTIONS:
                nx, ny = px + dx, py + dy
                steps = 0
                while 0 <= nx < 8 and 0 <= ny < 8 and grid[nx, ny] == EMPTY and steps < 7:
                    mobility += 1
                    nx += dx
                    ny += dy
                    steps += 1
        return mobility

    def evaluate_multi_component(self, grid, root_player):
        """
        Multi-component evaluation inspired by opponent03:
        - Queen territory (BFS)
        - King territory (BFS with king moves)
        - Queen position (exponential decay)
        - King position (weighted distance)
        - Mobility
        """
        my_pieces = np.argwhere(grid == root_player)
        opp_pieces = np.argwhere(grid == -root_player)
        
        # Component 1: Queen territory (use full BFS like v1)
        my_q_terr, my_q_dist = self.bfs_territory(grid, my_pieces)
        opp_q_terr, opp_q_dist = self.bfs_territory(grid, opp_pieces)
        
        queen_territory = sum(my_q_terr.values()) - sum(opp_q_terr.values())
        
        # Component 2: King territory (similar but conceptually separate)
        # For simplicity, use same BFS but weight close squares more
        king_territory = 0
        for d in range(1, 4):  # King-like distance (close matters more)
            king_territory += (my_q_terr.get(d, 0) - opp_q_terr.get(d, 0)) * (4 - d)
        
        # Component 3: Queen position (exponential decay by distance)
        queen_position = self.calc_position_score(my_pieces, my_q_dist) - \
                        self.calc_position_score(opp_pieces, opp_q_dist)
        
        # Component 4: King position (distance-weighted, simplified)
        king_position = 0
        for d in range(1, 7):
            my_count = np.sum(my_q_dist == d)
            opp_count = np.sum(opp_q_dist == d)
            king_position += (my_count - opp_count) / (d + 1.0)
        
        # Component 5: Mobility
        my_mobility = self.calc_mobility(grid, my_pieces)
        opp_mobility = self.calc_mobility(grid, opp_pieces)
        mobility = my_mobility - opp_mobility
        
        # Get phase-specific weights
        weights = self.get_phase_weights(self.turn_number)
        
        # Weighted combination
        score = (
            weights[0] * queen_territory +
            weights[1] * king_territory +
            weights[2] * queen_position +
            weights[3] * king_position +
            weights[4] * mobility
        ) * 0.20
        
        # Sigmoid normalization (from opponent03)
        return 1.0 / (1.0 + math.exp(-score))

    def search(self, root_state, root_player):
        if self.root is None:
            self.root = MCTSNode(parent=None, move=None, player_just_moved=-root_player)
            self.root.untried_moves = root_state.get_legal_moves(root_player)

        start_time = time.time()
        iterations = 0
        
        # Dynamic UCB constant
        C = self.get_ucb_constant(self.turn_number)
        
        while time.time() - start_time < self.time_limit:
            node = self.root
            state = root_state.copy()
            current_player = root_player

            # Selection
            while node.untried_moves == [] and node.children:
                node = node.uct_select_child(C)
                state.apply_move(node.move)
                current_player = -current_player

            # Expansion
            if node.untried_moves:
                m = random.choice(node.untried_moves) 
                state.apply_move(m)
                current_player = -current_player
                
                new_node = MCTSNode(parent=node, move=m, player_just_moved=-current_player)
                new_node.untried_moves = state.get_legal_moves(current_player)
                
                node.untried_moves.remove(m)
                node.children.append(new_node)
                node = new_node
            
            # Evaluation (Multi-component)
            win_prob = self.evaluate_multi_component(state.grid, root_player)
            
            # Backpropagation
            while node is not None:
                node.visits += 1
                if node.player_just_moved == root_player:
                    node.wins += win_prob
                else:
                    node.wins += (1.0 - win_prob)
                node = node.parent
            
            iterations += 1

        if not self.root.children:
            return None
        
        best_node = sorted(self.root.children, key=lambda c: c.visits)[-1]
        return best_node.move

    def advance_root(self, move):
        if self.root is None:
            return
        
        for child in self.root.children:
            if child.move == move:
                self.root = child
                self.root.parent = None
                return
        
        self.root = None


# --- MAIN MODULE ---

TIME_LIMIT = 3.8  
FIRST_TURN_TIME_LIMIT = 5.8

def main():
    board = Board()
    my_color = None
    ai = MCTS(time_limit=TIME_LIMIT)
    
    # --- FIRST TURN ---
    line = sys.stdin.readline()
    if not line:
        return
    
    try:
        turn_id = int(line.strip())
    except ValueError:
        return

    lines = []
    count = 2 * turn_id - 1
    for _ in range(count):
        lines.append(sys.stdin.readline().strip())
        
    first_req = list(map(int, lines[0].split()))
    if first_req[0] == -1:
        my_color = BLACK
    else:
        my_color = WHITE
        
    for line_str in lines:
        coords = list(map(int, line_str.split()))
        if coords[0] == -1:
            continue
        board.apply_move(coords)
        ai.advance_root(tuple(coords))
        
    # Set turn number for phase weights
    ai.turn_number = turn_id
    
    limit = FIRST_TURN_TIME_LIMIT if turn_id == 1 else TIME_LIMIT
    ai.time_limit = limit
    
    best_move = ai.search(board, my_color)
    
    if best_move:
        print(f"{best_move[0]} {best_move[1]} {best_move[2]} {best_move[3]} {best_move[4]} {best_move[5]}")
        board.apply_move(best_move)
        ai.advance_root(best_move)
    else:
        print("-1 -1 -1 -1 -1 -1")
        return

    print(">>>BOTZONE_REQUEST_KEEP_RUNNING<<<")
    sys.stdout.flush()
    
    # --- SUBSEQUENT TURNS ---
    while True:
        try:
            opponent_move = None
            while True:
                line = sys.stdin.readline()
                if not line: 
                    sys.exit(0)
                
                parts = list(map(int, line.strip().split()))
                
                if len(parts) == 6:
                    opponent_move = parts
                    break
                elif len(parts) == 1:
                    continue
                else:
                    continue

            if opponent_move:
                board.apply_move(opponent_move)
                ai.advance_root(tuple(opponent_move))

            # Update turn number
            ai.turn_number += 1
            
            ai.time_limit = TIME_LIMIT
            best_move = ai.search(board, my_color)
            
            if best_move:
                print(f"{best_move[0]} {best_move[1]} {best_move[2]} {best_move[3]} {best_move[4]} {best_move[5]}")
                board.apply_move(best_move)
                ai.advance_root(best_move)
            else:
                 print("-1 -1 -1 -1 -1 -1")
                 break
                 
            print(">>>BOTZONE_REQUEST_KEEP_RUNNING<<<")
            sys.stdout.flush()
            
        except Exception:
            break

if __name__ == "__main__":
    main()
