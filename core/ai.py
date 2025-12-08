import math
import random
import time
import collections
import numpy as np
from bots.archived_version.game import Board, WHITE, BLACK, EMPTY, GRID_SIZE, DIRECTIONS, OBSTACLE

class MCTSNode:
    def __init__(self, parent=None, move=None):
        self.parent = parent
        self.move = move  # The move that led to this state
        self.children = []
        self.wins = 0
        self.visits = 0
        self.untried_moves = None  # Will be populated on expansion
        self.player_just_moved = None # The player who made 'self.move'

    def uct_select_child(self):
        """ Use the UCB1 formula to select a child node. """
        s = sorted(self.children, key=lambda c: c.wins / c.visits + math.sqrt(2 * math.log(self.visits) / c.visits))
        return s[-1]

    def add_child(self, move, state):
        """ Add a new child node for this move. """
        node = MCTSNode(parent=self, move=move)
        node.untried_moves = state.get_legal_moves(-state.grid[move[2], move[3]]) # Next player
        # Note: We need to know whose turn it is. 
        # In get_legal_moves we passed the color.
        # But here we need to track state more carefully.
        # Let's delegate state management to the search loop.
        self.children.append(node)
        return node

class MCTS:
    def __init__(self, time_limit=5.0):
        self.time_limit = time_limit
        self.root = None

    def evaluate_territory(self, state, root_player):
        """
        Evaluate board using King's Move Distance (BFS).
        Returns score: MyTerritory - OpponentTerritory
        """
        # BFS for P1 (Root Player)
        q1 = collections.deque()
        dist1 = np.full((GRID_SIZE, GRID_SIZE), 999)
        
        # BFS for P2 (Opponent)
        q2 = collections.deque()
        dist2 = np.full((GRID_SIZE, GRID_SIZE), 999)
        
        # Init Sources
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                if state.grid[x, y] == root_player:
                    q1.append((x, y, 0))
                    dist1[x, y] = 0
                elif state.grid[x, y] == -root_player:
                    q2.append((x, y, 0))
                    dist2[x, y] = 0

        # Run BFS 1
        while q1:
            x, y, d = q1.popleft()
            nd = d + 1
            for dx, dy in DIRECTIONS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    if state.grid[nx, ny] == EMPTY and dist1[nx, ny] > nd:
                        dist1[nx, ny] = nd
                        q1.append((nx, ny, nd))

        # Run BFS 2
        while q2:
            x, y, d = q2.popleft()
            nd = d + 1
            for dx, dy in DIRECTIONS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    if state.grid[nx, ny] == EMPTY and dist2[nx, ny] > nd:
                        dist2[nx, ny] = nd
                        q2.append((nx, ny, nd))

        # Calculate Score
        # Count squares strictly closer to one player
        score = 0
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                if state.grid[x, y] == EMPTY:
                    d1 = dist1[x, y]
                    d2 = dist2[x, y]
                    if d1 < d2:
                        score += 1
                    elif d2 < d1:
                        score -= 1
                    # Else neutral
        
        # Additionally, add mobility score (number of immediate moves)
        # This helps in the endgame to avoid getting trapped
        # But BFS implicitly handles connectivity.
        
        return score

    def search(self, root_state, root_player):
        """
        Run MCTS.
        root_state: Board object
        root_player: Color of the player who needs to move (The Bot)
        """
        self.root = MCTSNode(parent=None, move=None)
        # Populate untried moves for the root
        self.root.untried_moves = root_state.get_legal_moves(root_player)
        self.root.player_just_moved = -root_player # Opponent moved last

        start_time = time.time()
        
        # Main MCTS Loop
        iterations = 0
        while time.time() - start_time < self.time_limit:
            node = self.root
            state = root_state.copy()
            current_player = root_player

            # 1. Selection
            # Trace down the tree until we find a node that is not fully expanded or is terminal
            while node.untried_moves == [] and node.children:
                node = node.uct_select_child()
                state.apply_move(node.move)
                current_player = -current_player # Switch turn

            # 2. Expansion
            # If we can expand (have untried moves), add one child
            if node.untried_moves:
                m = random.choice(node.untried_moves) 
                state.apply_move(m)
                current_player = -current_player
                
                # Create child
                new_node = MCTSNode(parent=node, move=m)
                new_node.player_just_moved = -current_player # The player who just moved
                new_node.untried_moves = state.get_legal_moves(current_player)
                
                node.untried_moves.remove(m)
                node.children.append(new_node)
                node = new_node
            
            # 3. Simulation (Rollout) & Evaluation
            # Instead of full random rollout, we use a mixed approach:
            # Short random rollout + Territory Heuristic
            
            # Rollout
            depth = 0
            max_depth = 5 # Short rollout
            while depth < max_depth:
                moves = state.get_legal_moves(current_player)
                if not moves:
                    break # Game over
                m = random.choice(moves)
                state.apply_move(m)
                current_player = -current_player
                depth += 1
            
            # Evaluation
            # If game ended naturally (no moves), we know the winner.
            # If max_depth reached, use heuristic.
            
            moves = state.get_legal_moves(current_player)
            if not moves:
                # current_player lost
                winner = -current_player
            else:
                # Heuristic Score
                # Returns value in [-1, 1] from perspective of root_player?
                # Or simply score for 'current_player'?
                # Territory score: (MyTerritory - OppTerritory)
                
                score = self.evaluate_territory(state, root_player)
                # Map score to win/loss probability
                # Score > 0 implies root_player is winning.
                # Sigmoid or simple clamp.
                # Max territory diff is approx 64.
                # normalize: 0.5 + score / 128
                win_prob = 0.5 + score / 64.0
                win_prob = max(0.0, min(1.0, win_prob))
                
                # We treat this as the "result" for root_player
                # But backprop expects discrete wins usually?
                # MCTS can handle continuous values [0, 1].
                pass

            # 4. Backpropagation
            while node is not None:
                node.visits += 1
                
                if not moves: # Game ended
                    if node.player_just_moved == winner:
                        node.wins += 1
                else:
                    # Heuristic result
                    # win_prob is prob that ROOT_PLAYER wins.
                    # We need to add value to the node.
                    # Node stores 'wins' for the player who made the move?
                    # Standard UCB: parent selects child with high value.
                    # If parent is Root (Bot), it wants child with high Bot Win Rate.
                    # If parent is Opponent, it wants child with high Opponent Win Rate (Low Bot Win Rate).
                    # 'wins' usually stores value from perspective of the player who moved to get there?
                    # Or always stores value for the same player?
                    
                    # Implementation detail:
                    # uct_select_child uses "c.wins / c.visits".
                    # If it's my turn, I pick max UCB.
                    # If it's opp turn, they pick max UCB? No, Minimax?
                    # In MCTS, we usually assume the tree nodes alternate or we flip the value?
                    # Or we store "wins" as "wins for the player who just moved".
                    
                    # Let's stick to: "wins" = accumulated value for the player who made the move at 'node'.
                    # So if node.player_just_moved == root_player:
                    #    node.wins += win_prob
                    # else:
                    #    node.wins += (1.0 - win_prob)
                    
                    if node.player_just_moved == root_player:
                        node.wins += win_prob
                    else:
                        node.wins += (1.0 - win_prob)
                
                node = node.parent
            
            iterations += 1

        # Select best move
        # Robust child: most visited
        if not self.root.children:
            return None # No moves possible
        
        best_node = sorted(self.root.children, key=lambda c: c.visits)[-1]
        return best_node.move
