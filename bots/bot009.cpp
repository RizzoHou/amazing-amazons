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

// Opponent.cpp weight array (28 turns, 6 components - using first 5)
const double ARGS[28][6] = {
    { 0.07747249543793637 ,0.05755603330699520 ,0.64627749023334498 ,0.70431267004292740 ,0.02438131097879579 , 0.00 },
    { 0.05093047840251742 ,0.06276538622537013 ,0.69898059004821581 ,0.66192728970497727 ,0.02362598306372760 , 0.00 },
    { 0.06036622274224539 ,0.06253298199478051 ,0.60094570235521628 ,0.67719126081076242 ,0.01873142786640421 , 0.00 },
    { 0.07597341130849308 ,0.06952095866594065 ,0.69061184234845333 ,0.67989394578528273 ,0.02098781856298665 , 0.00 },
    { 0.08083391263897154 ,0.08815144960484271 ,0.58981849824874917 ,0.54664183543259470 ,0.02318479501373763 , 0.00 },
    { 0.09155731347030857 ,0.08397548702353251 ,0.56392480085083986 ,0.54319242129550227 ,0.02317401477849946 , 0.00 },
    { 0.10653095458609237 ,0.10479793630859575 ,0.54840938009286515 ,0.53023658889860381 ,0.02084758939889652 , 0.00 },
    { 0.11534143744086589 ,0.11515706838023705 ,0.53325566869906469 ,0.52423368303553451 ,0.02237127451593010 , 0.00 },
    { 0.12943854523554690 ,0.12673742164114844 ,0.50841519367287034 ,0.52208373964502879 ,0.02490545306630711 , 0.00 },
    { 0.12882484162931859 ,0.13946973532382280 ,0.49621839819987758 ,0.51776460089353364 ,0.03045473763611049 , 0.00 },
    { 0.13701233819832731 ,0.15338865590616042 ,0.47601466399954588 ,0.51500429509193190 ,0.03249896738636078 , 0.00 },
    { 0.14530543898518938 ,0.15565237403332051 ,0.45365475320199057 ,0.50934623406618500 ,0.03830491784046246 , 0.00 },
    { 0.14521045986025419 ,0.16388365022083374 ,0.44531995327608060 ,0.50517597255948953 ,0.04864124027084386 , 0.00 },
    { 0.13750613208150655 ,0.16326621164859418 ,0.43619350878439399 ,0.50328876650721398 ,0.05912794240603884 , 0.00 },
    { 0.13565263325548560 ,0.15529175902376631 ,0.42382223063419649 ,0.50288212924827379 ,0.07437679521343679 , 0.00 },
    { 0.12382760525087406 ,0.10361944098637088 ,0.50487335391408680 ,0.55808747967333505 ,0.02791980213792046 , 0.00 },
    { 0.11809487853625075 ,0.14632850080535232 ,0.40738388113193924 ,0.41782129616811122 ,0.10308050317730764 , 0.00 },
    { 0.10805473551960752 ,0.15043981450391137 ,0.40520488356004784 ,0.43073574707030956 ,0.10967613304465569 , 0.00 },
    { 0.09668240983912251 ,0.15666221434557865 ,0.40215634987047013 ,0.44165716517577754 ,0.10906426061069142 , 0.00 },
    { 0.10585263971502025 ,0.16319090506614549 ,0.38220029690800922 ,0.45465487463858675 ,0.10062997439277618 , 0.00 },
    { 0.11123671989551248 ,0.15516074827095279 ,0.36904588744714037 ,0.46534418781939937 ,0.09118229977179015 , 0.00 },
    { 0.12535649823409767 ,0.10492555251930048 ,0.35567115915540981 ,0.48043579160677637 ,0.08337580273275977 , 0.00 },
    { 0.28657326967317970 ,0.16655279311197080 ,0.38060545469477008 ,0.42472577515072628 ,0.10316994796202342 , 0.00 },
    { 0.07143084940040888 ,0.16655279311197080 ,0.36658063304313299 ,0.39520049916162908 ,0.02194263694320541 , 0.00 },
    { 0.07143084940040888 ,0.16655279311197080 ,0.36658063304313299 ,0.39520049916162908 ,0.02194263694320541 , 0.00 },
    { 0.07143084940040888 ,0.16655279311197080 ,0.36658063304313299 ,0.39520049916162908 ,0.02194263694320541 , 0.00 },
    { 0.07143084940040888 ,0.16655279311197080 ,0.36658063304313299 ,0.39520049916162908 ,0.02194263694320541 , 0.00 },
    { 0.07143084940040888 ,0.14627749023334498 ,0.36658063304313299 ,0.39520049916162908 ,0.02194263694320541 , 0.00 }
};

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
        // Use opponent.cpp's weight array
        // For turns 0-27: use corresponding row
        // For turns >= 28: use last row (27)
        int index = turn;
        if (index >= 28) {
            index = 27;  // Use last row for turns >= 28
        }
        return ARGS[index];  // Returns pointer to 6-element array, we'll use first 5
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

const double TIME_LIMIT = 0.88;
const double FIRST_TURN_TIME_LIMIT = 1.88;

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