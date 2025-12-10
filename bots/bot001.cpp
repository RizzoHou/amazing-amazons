#include <iostream>
#include <vector>
#include <array>
#include <cmath>
#include <random>
#include <chrono>
#include <deque>
#include <unordered_map>
#include <algorithm>
#include <sstream>

using namespace std;

// --- GAME CONSTANTS & BOARD ---
const int GRID_SIZE = 8;
const int EMPTY = 0;
const int BLACK = 1;
const int WHITE = -1;
const int OBSTACLE = 2;

const int DIRECTIONS[8][2] = {
    {-1, -1}, {-1, 0}, {-1, 1},
    {0, -1},           {0, 1},
    {1, -1},  {1, 0},  {1, 1}
};

struct Move {
    int x0, y0, x1, y1, x2, y2;
    
    Move() : x0(0), y0(0), x1(0), y1(0), x2(0), y2(0) {}
    Move(int a, int b, int c, int d, int e, int f) 
        : x0(a), y0(b), x1(c), y1(d), x2(e), y2(f) {}
    
    bool operator==(const Move& other) const {
        return x0 == other.x0 && y0 == other.y0 &&
               x1 == other.x1 && y1 == other.y1 &&
               x2 == other.x2 && y2 == other.y2;
    }
};

class Board {
public:
    array<array<int, GRID_SIZE>, GRID_SIZE> grid;
    
    Board() {
        for (int i = 0; i < GRID_SIZE; i++) {
            for (int j = 0; j < GRID_SIZE; j++) {
                grid[i][j] = EMPTY;
            }
        }
        init_board();
    }
    
    void init_board() {
        // Black
        grid[0][2] = BLACK;
        grid[2][0] = BLACK;
        grid[5][0] = BLACK;
        grid[7][2] = BLACK;
        // White
        grid[0][5] = WHITE;
        grid[2][7] = WHITE;
        grid[5][7] = WHITE;
        grid[7][5] = WHITE;
    }
    
    bool is_valid(int x, int y) const {
        return x >= 0 && x < GRID_SIZE && y >= 0 && y < GRID_SIZE;
    }
    
    vector<Move> get_legal_moves(int color) const {
        vector<Move> moves;
        
        // Find all pieces of the given color
        for (int px = 0; px < GRID_SIZE; px++) {
            for (int py = 0; py < GRID_SIZE; py++) {
                if (grid[px][py] != color) continue;
                
                // Try all 8 directions for piece movement
                for (int d = 0; d < 8; d++) {
                    int dx = DIRECTIONS[d][0];
                    int dy = DIRECTIONS[d][1];
                    int nx = px + dx;
                    int ny = py + dy;
                    
                    while (is_valid(nx, ny) && grid[nx][ny] == EMPTY) {
                        // From each landing position, try shooting in all 8 directions
                        for (int ad = 0; ad < 8; ad++) {
                            int adx = DIRECTIONS[ad][0];
                            int ady = DIRECTIONS[ad][1];
                            int ax = nx + adx;
                            int ay = ny + ady;
                            
                            while (is_valid(ax, ay)) {
                                bool is_blocked = false;
                                if (grid[ax][ay] != EMPTY) {
                                    if (ax == px && ay == py) {
                                        // Arrow hits original position (valid)
                                    } else {
                                        is_blocked = true;
                                    }
                                }
                                if (is_blocked) break;
                                
                                moves.push_back(Move(px, py, nx, ny, ax, ay));
                                ax += adx;
                                ay += ady;
                            }
                        }
                        nx += dx;
                        ny += dy;
                    }
                }
            }
        }
        return moves;
    }
    
    void apply_move(const Move& move) {
        int piece = grid[move.x0][move.y0];
        grid[move.x0][move.y0] = EMPTY;
        grid[move.x1][move.y1] = piece;
        grid[move.x2][move.y2] = OBSTACLE;
    }
    
    Board copy() const {
        Board new_board;
        new_board.grid = this->grid;
        return new_board;
    }
};

// --- AI MODULE ---

class MCTSNode {
public:
    MCTSNode* parent;
    Move move;
    vector<MCTSNode*> children;
    double wins;
    int visits;
    vector<Move> untried_moves;
    int player_just_moved;
    
    MCTSNode(MCTSNode* p = nullptr, Move m = Move(), int pjm = 0)
        : parent(p), move(m), wins(0.0), visits(0), player_just_moved(pjm) {}
    
    ~MCTSNode() {
        for (auto child : children) {
            delete child;
        }
    }
    
    MCTSNode* uct_select_child(double C) {
        double log_visits = log(visits);
        double best_score = -1e9;
        MCTSNode* best_child = nullptr;
        
        for (auto c : children) {
            double score = (c->wins / c->visits) + C * sqrt(log_visits / c->visits);
            if (score > best_score) {
                best_score = score;
                best_child = c;
            }
        }
        return best_child;
    }
};

// Phase weights
const double EARLY_WEIGHTS[5] = {0.08, 0.06, 0.60, 0.68, 0.02};
const double MID_WEIGHTS[5] = {0.13, 0.15, 0.45, 0.51, 0.07};
const double LATE_WEIGHTS[5] = {0.11, 0.15, 0.38, 0.45, 0.10};

class MCTS {
public:
    double time_limit;
    MCTSNode* root;
    int turn_number;
    mt19937 rng;
    
    MCTS(double tl = 5.0) : time_limit(tl), root(nullptr), turn_number(0) {
        rng.seed(chrono::steady_clock::now().time_since_epoch().count());
    }
    
    ~MCTS() {
        if (root) delete root;
    }
    
    const double* get_phase_weights(int turn) {
        if (turn <= 10) return EARLY_WEIGHTS;
        else if (turn <= 20) return MID_WEIGHTS;
        else return LATE_WEIGHTS;
    }
    
    double get_ucb_constant(int turn) {
        return 0.177 * exp(-0.008 * (turn - 1.41));
    }
    
    pair<unordered_map<int, int>, array<array<int, GRID_SIZE>, GRID_SIZE>> 
    bfs_territory(const array<array<int, GRID_SIZE>, GRID_SIZE>& grid, 
                  const vector<pair<int, int>>& pieces) {
        array<array<int, GRID_SIZE>, GRID_SIZE> dist;
        for (int i = 0; i < GRID_SIZE; i++) {
            for (int j = 0; j < GRID_SIZE; j++) {
                dist[i][j] = 99;
            }
        }
        
        deque<tuple<int, int, int>> q;
        for (auto& p : pieces) {
            dist[p.first][p.second] = 0;
            q.push_back(make_tuple(p.first, p.second, 0));
        }
        
        unordered_map<int, int> territory_by_dist;
        
        while (!q.empty()) {
            int x, y, d;
            tie(x, y, d) = q.front();
            q.pop_front();
            int nd = d + 1;
            
            for (int i = 0; i < 8; i++) {
                int nx = x + DIRECTIONS[i][0];
                int ny = y + DIRECTIONS[i][1];
                
                if (nx >= 0 && nx < GRID_SIZE && ny >= 0 && ny < GRID_SIZE) {
                    if (grid[nx][ny] == EMPTY && dist[nx][ny] > nd) {
                        dist[nx][ny] = nd;
                        territory_by_dist[nd]++;
                        q.push_back(make_tuple(nx, ny, nd));
                    }
                }
            }
        }
        
        return make_pair(territory_by_dist, dist);
    }
    
    double calc_position_score(const array<array<int, GRID_SIZE>, GRID_SIZE>& dist_map) {
        double score = 0.0;
        for (int i = 1; i < 8; i++) {
            int count = 0;
            for (int x = 0; x < GRID_SIZE; x++) {
                for (int y = 0; y < GRID_SIZE; y++) {
                    if (dist_map[x][y] == i) count++;
                }
            }
            score += count * pow(2.0, -i);
        }
        return score;
    }
    
    int calc_mobility(const array<array<int, GRID_SIZE>, GRID_SIZE>& grid,
                     const vector<pair<int, int>>& pieces) {
        int mobility = 0;
        for (auto& p : pieces) {
            int px = p.first, py = p.second;
            for (int d = 0; d < 8; d++) {
                int nx = px + DIRECTIONS[d][0];
                int ny = py + DIRECTIONS[d][1];
                int steps = 0;
                while (nx >= 0 && nx < GRID_SIZE && ny >= 0 && ny < GRID_SIZE &&
                       grid[nx][ny] == EMPTY && steps < 7) {
                    mobility++;
                    nx += DIRECTIONS[d][0];
                    ny += DIRECTIONS[d][1];
                    steps++;
                }
            }
        }
        return mobility;
    }
    
    double evaluate_multi_component(const array<array<int, GRID_SIZE>, GRID_SIZE>& grid, 
                                    int root_player) {
        vector<pair<int, int>> my_pieces, opp_pieces;
        for (int i = 0; i < GRID_SIZE; i++) {
            for (int j = 0; j < GRID_SIZE; j++) {
                if (grid[i][j] == root_player) {
                    my_pieces.push_back(make_pair(i, j));
                } else if (grid[i][j] == -root_player) {
                    opp_pieces.push_back(make_pair(i, j));
                }
            }
        }
        
        // Component 1: Queen territory
        auto my_q = bfs_territory(grid, my_pieces);
        auto opp_q = bfs_territory(grid, opp_pieces);
        
        int queen_territory = 0;
        for (auto& kv : my_q.first) queen_territory += kv.second;
        for (auto& kv : opp_q.first) queen_territory -= kv.second;
        
        // Component 2: King territory
        int king_territory = 0;
        for (int d = 1; d < 4; d++) {
            int my_count = my_q.first.count(d) ? my_q.first[d] : 0;
            int opp_count = opp_q.first.count(d) ? opp_q.first[d] : 0;
            king_territory += (my_count - opp_count) * (4 - d);
        }
        
        // Component 3: Queen position
        double queen_position = calc_position_score(my_q.second) - 
                               calc_position_score(opp_q.second);
        
        // Component 4: King position
        double king_position = 0;
        for (int d = 1; d < 7; d++) {
            int my_count = 0, opp_count = 0;
            for (int x = 0; x < GRID_SIZE; x++) {
                for (int y = 0; y < GRID_SIZE; y++) {
                    if (my_q.second[x][y] == d) my_count++;
                    if (opp_q.second[x][y] == d) opp_count++;
                }
            }
            king_position += (my_count - opp_count) / (d + 1.0);
        }
        
        // Component 5: Mobility
        int my_mobility = calc_mobility(grid, my_pieces);
        int opp_mobility = calc_mobility(grid, opp_pieces);
        int mobility = my_mobility - opp_mobility;
        
        // Get phase-specific weights
        const double* weights = get_phase_weights(turn_number);
        
        // Weighted combination
        double score = (
            weights[0] * queen_territory +
            weights[1] * king_territory +
            weights[2] * queen_position +
            weights[3] * king_position +
            weights[4] * mobility
        ) * 0.20;
        
        // Sigmoid normalization
        return 1.0 / (1.0 + exp(-score));
    }
    
    Move search(const Board& root_state, int root_player) {
        if (root == nullptr) {
            root = new MCTSNode(nullptr, Move(), -root_player);
            root->untried_moves = root_state.get_legal_moves(root_player);
        }
        
        auto start_time = chrono::steady_clock::now();
        int iterations = 0;
        
        double C = get_ucb_constant(turn_number);
        
        while (true) {
            auto current_time = chrono::steady_clock::now();
            double elapsed = chrono::duration<double>(current_time - start_time).count();
            if (elapsed >= time_limit) break;
            
            MCTSNode* node = root;
            Board state = root_state.copy();
            int current_player = root_player;
            
            // Selection
            while (node->untried_moves.empty() && !node->children.empty()) {
                node = node->uct_select_child(C);
                state.apply_move(node->move);
                current_player = -current_player;
            }
            
            // Expansion
            if (!node->untried_moves.empty()) {
                uniform_int_distribution<int> dist(0, node->untried_moves.size() - 1);
                int idx = dist(rng);
                Move m = node->untried_moves[idx];
                
                state.apply_move(m);
                current_player = -current_player;
                
                MCTSNode* new_node = new MCTSNode(node, m, -current_player);
                new_node->untried_moves = state.get_legal_moves(current_player);
                
                node->untried_moves.erase(node->untried_moves.begin() + idx);
                node->children.push_back(new_node);
                node = new_node;
            }
            
            // Evaluation
            double win_prob = evaluate_multi_component(state.grid, root_player);
            
            // Backpropagation
            while (node != nullptr) {
                node->visits++;
                if (node->player_just_moved == root_player) {
                    node->wins += win_prob;
                } else {
                    node->wins += (1.0 - win_prob);
                }
                node = node->parent;
            }
            
            iterations++;
        }
        
        if (root->children.empty()) {
            return Move(-1, -1, -1, -1, -1, -1);
        }
        
        // Select best move by visit count
        MCTSNode* best_node = nullptr;
        int max_visits = -1;
        for (auto child : root->children) {
            if (child->visits > max_visits) {
                max_visits = child->visits;
                best_node = child;
            }
        }
        
        return best_node->move;
    }
    
    void advance_root(const Move& move) {
        if (root == nullptr) return;
        
        MCTSNode* new_root = nullptr;
        for (auto child : root->children) {
            if (child->move == move) {
                new_root = child;
                break;
            }
        }
        
        if (new_root != nullptr) {
            // Remove new_root from children to prevent deletion
            root->children.erase(
                remove(root->children.begin(), root->children.end(), new_root),
                root->children.end()
            );
            delete root;  // This will delete all other children
            root = new_root;
            root->parent = nullptr;
        } else {
            delete root;
            root = nullptr;
        }
    }
};

// --- MAIN MODULE ---

const double TIME_LIMIT = 0.9;
const double FIRST_TURN_TIME_LIMIT = 1.8;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    
    Board board;
    int my_color = 0;
    MCTS ai(TIME_LIMIT);
    
    // First turn
    string line;
    if (!getline(cin, line)) return 0;
    
    int turn_id;
    try {
        turn_id = stoi(line);
    } catch (...) {
        return 0;
    }
    
    vector<string> lines;
    int count = 2 * turn_id - 1;
    for (int i = 0; i < count; i++) {
        string l;
        if (!getline(cin, l)) return 0;
        lines.push_back(l);
    }
    
    // Determine color
    istringstream iss(lines[0]);
    vector<int> first_req;
    int val;
    while (iss >> val) first_req.push_back(val);
    
    if (first_req[0] == -1) {
        my_color = BLACK;
    } else {
        my_color = WHITE;
    }
    
    // Replay moves
    for (const string& line_str : lines) {
        istringstream iss2(line_str);
        vector<int> coords;
        int v;
        while (iss2 >> v) coords.push_back(v);
        
        if (coords[0] == -1) continue;
        
        Move m(coords[0], coords[1], coords[2], coords[3], coords[4], coords[5]);
        board.apply_move(m);
        ai.advance_root(m);
    }
    
    // Set turn number
    ai.turn_number = turn_id;
    
    double limit = (turn_id == 1) ? FIRST_TURN_TIME_LIMIT : TIME_LIMIT;
    ai.time_limit = limit;
    
    Move best_move = ai.search(board, my_color);
    
    if (best_move.x0 != -1) {
        cout << best_move.x0 << " " << best_move.y0 << " " 
             << best_move.x1 << " " << best_move.y1 << " "
             << best_move.x2 << " " << best_move.y2 << endl;
        board.apply_move(best_move);
        ai.advance_root(best_move);
    } else {
        cout << "-1 -1 -1 -1 -1 -1" << endl;
        return 0;
    }
    
    cout << ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<" << endl;
    cout.flush();
    
    // Subsequent turns
    while (true) {
        try {
            Move opponent_move;
            bool found = false;
            
            while (true) {
                string line;
                if (!getline(cin, line)) return 0;
                
                istringstream iss(line);
                vector<int> parts;
                int v;
                while (iss >> v) parts.push_back(v);
                
                if (parts.size() == 6) {
                    opponent_move = Move(parts[0], parts[1], parts[2], 
                                        parts[3], parts[4], parts[5]);
                    found = true;
                    break;
                } else if (parts.size() == 1) {
                    continue;
                } else {
                    continue;
                }
            }
            
            if (found) {
                board.apply_move(opponent_move);
                ai.advance_root(opponent_move);
            }
            
            ai.turn_number++;
            ai.time_limit = TIME_LIMIT;
            
            best_move = ai.search(board, my_color);
            
            if (best_move.x0 != -1) {
                cout << best_move.x0 << " " << best_move.y0 << " " 
                     << best_move.x1 << " " << best_move.y1 << " "
                     << best_move.x2 << " " << best_move.y2 << endl;
                board.apply_move(best_move);
                ai.advance_root(best_move);
            } else {
                cout << "-1 -1 -1 -1 -1 -1" << endl;
                break;
            }
            
            cout << ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<" << endl;
            cout.flush();
            
        } catch (...) {
            break;
        }
    }
    
    return 0;
}
