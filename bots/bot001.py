import sys
import time
import math
import random
import numpy as np
import zlib
import base64

# Add path for imports
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.game import Board, BLACK, WHITE, GRID_SIZE

# --- Neural Network (Fully Connected, Smaller than v11) ---

def relu(x):
    return np.maximum(0, x)

def tanh(x):
    return np.tanh(x)

def batch_norm_inference(x, gamma, beta, mean, var, eps=1e-5):
    """Batch normalization in inference mode"""
    return gamma * (x - mean) / np.sqrt(var + eps) + beta

class NeuralNetV15:
    def __init__(self):
        self.weights = {}
        self.load_weights()
        
    def load_weights(self):
        """Load weights from npz file"""
        import os
        weights_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'weights_v15.npz')
        data = np.load(weights_path)
        for key in data.files:
            self.weights[key] = data[key]
    
    def predict(self, board_state):
        """
        board_state: (3, 8, 8) numpy array
        Returns: scalar value [-1, 1]
        """
        # Flatten input
        x = board_state.flatten()  # 192 features
        
        # Layer 1: Linear + BN + ReLU + Dropout(inference=no dropout)
        w1 = self.weights['fc1.weight']
        b1 = self.weights['fc1.bias']
        x = np.dot(w1, x) + b1
        
        # Batch norm
        gamma1 = self.weights['bn1.weight']
        beta1 = self.weights['bn1.bias']
        mean1 = self.weights['bn1.running_mean']
        var1 = self.weights['bn1.running_var']
        x = batch_norm_inference(x, gamma1, beta1, mean1, var1)
        x = relu(x)
        
        # Layer 2
        w2 = self.weights['fc2.weight']
        b2 = self.weights['fc2.bias']
        x = np.dot(w2, x) + b2
        
        gamma2 = self.weights['bn2.weight']
        beta2 = self.weights['bn2.bias']
        mean2 = self.weights['bn2.running_mean']
        var2 = self.weights['bn2.running_var']
        x = batch_norm_inference(x, gamma2, beta2, mean2, var2)
        x = relu(x)
        
        # Layer 3
        w3 = self.weights['fc3.weight']
        b3 = self.weights['fc3.bias']
        x = np.dot(w3, x) + b3
        
        gamma3 = self.weights['bn3.weight']
        beta3 = self.weights['bn3.bias']
        mean3 = self.weights['bn3.running_mean']
        var3 = self.weights['bn3.running_var']
        x = batch_norm_inference(x, gamma3, beta3, mean3, var3)
        x = relu(x)
        
        # Output layer
        w4 = self.weights['fc4.weight']
        b4 = self.weights['fc4.bias']
        x = np.dot(w4, x) + b4
        x = tanh(x)
        
        return x[0]

# --- MCTS (Same as v13 with neural evaluation) ---

class MCTSNode:
    def __init__(self, parent=None, move=None, player_just_moved=None):
        self.parent = parent
        self.move = move
        self.children = []
        self.wins = 0.0
        self.visits = 0
        self.untried_moves = None
        self.player_just_moved = player_just_moved

    def uct_select_child(self, C=1.414):
        log_visits = math.log(self.visits)
        best_score = -float('inf')
        best_child = None
        
        for c in self.children:
            score = (c.wins / c.visits) + C * math.sqrt(log_visits / c.visits)
            if score > best_score:
                best_score = score
                best_child = c
        return best_child

class MCTS:
    def __init__(self, network, time_limit=3.8):
        self.network = network
        self.time_limit = time_limit
        self.root = None

    def get_state_tensor(self, b, player):
        state = np.zeros((3, 8, 8), dtype=np.float32)
        grid = b.grid
        my_val = player
        opp_val = -player
        state[0] = (grid == my_val).astype(np.float32)
        state[1] = (grid == opp_val).astype(np.float32)
        state[2] = (grid == 2).astype(np.float32)
        return state

    def search(self, root_state, root_player):
        if self.root is None:
            self.root = MCTSNode(parent=None, move=None, player_just_moved=-root_player)
            self.root.untried_moves = root_state.get_legal_moves(root_player)

        start_time = time.time()
        iterations = 0
        
        while time.time() - start_time < self.time_limit:
            node = self.root
            state = root_state.copy()
            current_player = root_player

            # Selection
            while node.untried_moves == [] and node.children:
                node = node.uct_select_child()
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
            
            # Evaluation with neural network
            nn_input = self.get_state_tensor(state, root_player)
            value = self.network.predict(nn_input)
            
            # Normalize to [0, 1]
            win_prob = (value + 1.0) / 2.0
            
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


# --- MAIN ---

TIME_LIMIT = 3.8  
FIRST_TURN_TIME_LIMIT = 5.8

def main():
    # Load neural network
    try:
        nn_model = NeuralNetV15()
    except Exception as e:
        sys.stderr.write(f"Error loading neural net: {e}\n")
        sys.exit(1)

    # Initialize MCTS with neural network
    ai = MCTS(nn_model, time_limit=TIME_LIMIT)
    board = Board()
    my_color = None
    
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
