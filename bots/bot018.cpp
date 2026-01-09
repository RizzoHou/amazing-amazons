#include <iostream>
#include <vector>
#include <array>
#include <cmath>
#include <chrono>
#include <algorithm>
#include <sstream>
#include <cstring> // for memset

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
    int8_t x0, y0, x1, y1, x2, y2;
    
    Move() : x0(0), y0(0), x1(0), y1(0), x2(0), y2(0) {}
    Move(int a, int b, int c, int d, int e, int f) 
        : x0((int8_t)a), y0((int8_t)b), x1((int8_t)c), y1((int8_t)d), x2((int8_t)e), y2((int8_t)f) {}
};

// --- FAST RNG ---
// Much faster than mt19937 for simple index selection
static uint32_t xorshift_state;
void seed_rng() {
    xorshift_state = (uint32_t)chrono::steady_clock::now().time_since_epoch().count();
    if (xorshift_state == 0) xorshift_state = 0xDEADBEEF;
}
inline uint32_t fast_rand() {
    uint32_t x = xorshift_state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    return xorshift_state = x;
}

class Board {
public:
    array<array<int, GRID_SIZE>, GRID_SIZE> grid;
    
    Board() {
        // Just zero out, init handled manually if needed
        for (auto& row : grid) row.fill(EMPTY);
        init_board();
    }
    
    // Fast constructor for copying: relies on default array copy
    Board(const Board& other) = default;
    
    void init_board() {
        grid[0][2] = BLACK; grid[2][0] = BLACK; grid[5][0] = BLACK; grid[7][2] = BLACK;
        grid[0][5] = WHITE; grid[2][7] = WHITE; grid[5][7] = WHITE; grid[7][5] = WHITE;
    }
    
    bool is_valid(int x, int y) const {
        return x >= 0 && x < GRID_SIZE && y >= 0 && y < GRID_SIZE;
    }
    
    vector<Move> get_legal_moves(int color) const {
        vector<Move> moves;
        moves.reserve(128); // Pre-allocate to avoid resizing
        
        for (int px = 0; px < GRID_SIZE; px++) {
            for (int py = 0; py < GRID_SIZE; py++) {
                if (grid[px][py] != color) continue;
                
                for (int d = 0; d < 8; d++) {
                    int dx = DIRECTIONS[d][0];
                    int dy = DIRECTIONS[d][1];
                    int nx = px + dx;
                    int ny = py + dy;
                    
                    while (nx >= 0 && nx < GRID_SIZE && ny >= 0 && ny < GRID_SIZE && grid[nx][ny] == EMPTY) {
                        for (int ad = 0; ad < 8; ad++) {
                            int adx = DIRECTIONS[ad][0];
                            int ady = DIRECTIONS[ad][1];
                            int ax = nx + adx;
                            int ay = ny + ady;
                            
                            while (ax >= 0 && ax < GRID_SIZE && ay >= 0 && ay < GRID_SIZE) {
                                if (grid[ax][ay] != EMPTY) {
                                    if (ax != px || ay != py) break; // Blocked
                                }
                                
                                moves.emplace_back(px, py, nx, ny, ax, ay);
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
};

// --- MEMORY POOL FOR MCTS NODES ---
// Fits easily within 256MB. 150k nodes is usually plenty for 1s.
const int MAX_NODES = 200000;

class MCTSNode {
public:
    MCTSNode* parent;
    Move move;
    vector<MCTSNode*> children;
    vector<Move> untried_moves;
    double wins;
    int visits;
    int player_just_moved;
    
    // Minimal initialization
    void init(MCTSNode* p, Move m, int pjm) {
        parent = p;
        move = m;
        children.clear();
        untried_moves.clear();
        wins = 0.0;
        visits = 0;
        player_just_moved = pjm;
    }

    // No destructor needed - we trust OS to clean up the pool at exit
    
    MCTSNode* uct_select_child(double C) {
        // Fast log approximation or just standard log (log is cached usually)
        double log_visits = log((double)visits);
        double best_score = -1e9;
        MCTSNode* best_child = nullptr;
        
        for (auto c : children) {
            // UCB1
            double score = (c->wins / (c->visits + 1e-6)) + C * sqrt(log_visits / (c->visits + 1e-6));
            if (score > best_score) {
                best_score = score;
                best_child = c;
            }
        }
        return best_child;
    }
};

// Global pool to avoid reallocation overhead
MCTSNode node_pool[MAX_NODES];
int pool_ptr = 0;

MCTSNode* new_node(MCTSNode* p, Move m, int pjm) {
    if (pool_ptr >= MAX_NODES) return nullptr;
    MCTSNode* ptr = &node_pool[pool_ptr++];
    ptr->init(p, m, pjm);
    return ptr;
}

// --- OPTIMIZATION BUFFERS ---
static int dist_my[GRID_SIZE][GRID_SIZE];
static int dist_op[GRID_SIZE][GRID_SIZE];

struct FastQueue {
    int qx[GRID_SIZE * GRID_SIZE];
    int qy[GRID_SIZE * GRID_SIZE];
    int head, tail;
    void clear() { head = 0; tail = 0; }
    void push(int x, int y) { qx[tail] = x; qy[tail] = y; tail++; }
    bool not_empty() const { return head < tail; }
    void pop(int &x, int &y) { x = qx[head]; y = qy[head]; head++; }
};
static FastQueue bfs_q;

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
    MCTSNode* best_child;
    int max_visits;
    
    MCTS(double tl) : time_limit(tl), root(nullptr), turn_number(0), best_child(nullptr), max_visits(-1) {
        seed_rng();
    }
    
    // No destructor needed, pool handles it
    
    const double* get_phase_weights(int turn) {
        int index = turn;
        if (index >= 28) index = 27;
        return ARGS[index];
    }
    
    double get_ucb_constant(int turn) {
        return 0.177 * exp(-0.008 * (turn - 1.41));
    }
    
    void perform_fast_bfs(const array<array<int, GRID_SIZE>, GRID_SIZE>& grid, 
                          const vector<pair<int, int>>& pieces, 
                          int dist_out[GRID_SIZE][GRID_SIZE]) {
        for (int i = 0; i < GRID_SIZE; i++) {
             // 99 is sufficient infinity for 8x8
            fill(begin(dist_out[i]), end(dist_out[i]), 99);
        }
        bfs_q.clear();
        for (const auto& p : pieces) {
            dist_out[p.first][p.second] = 0;
            bfs_q.push(p.first, p.second);
        }
        int cx, cy;
        while (bfs_q.not_empty()) {
            bfs_q.pop(cx, cy);
            int next_dist = dist_out[cx][cy] + 1;
            for (int i = 0; i < 8; i++) {
                int nx = cx + DIRECTIONS[i][0];
                int ny = cy + DIRECTIONS[i][1];
                if (nx >= 0 && nx < GRID_SIZE && ny >= 0 && ny < GRID_SIZE) {
                    if (grid[nx][ny] == EMPTY && dist_out[nx][ny] > next_dist) {
                        dist_out[nx][ny] = next_dist;
                        bfs_q.push(nx, ny);
                    }
                }
            }
        }
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
    
    // FAST SIGMOID: Approximates 1/(1+exp(-x))
    // Much faster than std::exp
    inline double fast_sigmoid(double x) {
        // Range mapping: score is roughly -10 to +10.
        // x / (1 + |x|) maps (-inf, inf) to (-1, 1).
        // 0.5 * (...) + 0.5 maps it to (0, 1).
        return 0.5 * (x / (1.0 + std::abs(x)) + 1.0);
    }
    
    double evaluate_optimized(const array<array<int, GRID_SIZE>, GRID_SIZE>& grid, int root_player) {
        vector<pair<int, int>> my_pieces; my_pieces.reserve(4);
        vector<pair<int, int>> opp_pieces; opp_pieces.reserve(4);
        
        for (int i = 0; i < GRID_SIZE; i++) {
            for (int j = 0; j < GRID_SIZE; j++) {
                if (grid[i][j] == root_player) my_pieces.push_back({i, j});
                else if (grid[i][j] == -root_player) opp_pieces.push_back({i, j});
            }
        }
        
        perform_fast_bfs(grid, my_pieces, dist_my);
        perform_fast_bfs(grid, opp_pieces, dist_op);
        
        double queen_territory = 0, king_territory = 0, queen_position = 0, king_position = 0;
        
        static const double POW2[] = { 0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625, 0.0078125, 0.00390625, 0.001953125, 0.0009765625 }; 
        
        for (int i = 0; i < GRID_SIZE; i++) {
            for (int j = 0; j < GRID_SIZE; j++) {
                if (grid[i][j] != EMPTY) continue;
                int dm = dist_my[i][j];
                int dopp = dist_op[i][j];
                if (dm == 99 && dopp == 99) continue;
                
                if (dm < dopp) {
                    queen_territory += 1.0;
                    if (dm < 4) king_territory += (4 - dm);
                } else if (dopp < dm) {
                    queen_territory -= 1.0;
                    if (dopp < 4) king_territory -= (4 - dopp);
                }
                
                if (dm < 10) queen_position += POW2[dm];
                if (dopp < 10) queen_position -= POW2[dopp];
                
                if (dm < 6) king_position += 1.0 / (dm + 1.0);
                if (dopp < 6) king_position -= 1.0 / (dopp + 1.0);
            }
        }
        
        double mobility = (double)(calc_mobility(grid, my_pieces) - calc_mobility(grid, opp_pieces));
        const double* weights = get_phase_weights(turn_number);
        
        double score = (
            weights[0] * queen_territory +
            weights[1] * king_territory +
            weights[2] * queen_position +
            weights[3] * king_position +
            weights[4] * mobility
        ) * 0.20;
        
        return fast_sigmoid(score);
    }
    
    Move search(const Board& root_state, int root_player, const chrono::steady_clock::time_point& program_start_time, double original_time_limit, double safety_margin) {
        auto search_start_time = chrono::steady_clock::now();
        double elapsed_time = chrono::duration<double>(search_start_time - program_start_time).count();
        double adjusted_time_limit = original_time_limit - elapsed_time - safety_margin;
        if (adjusted_time_limit < 0.05) adjusted_time_limit = 0.05;
        
        // Reset pool pointer at start of search (since process restarts every turn, this is effectively 0)
        pool_ptr = 0;
        
        // Init root in the pool
        root = new_node(nullptr, Move(), -root_player);
        root->untried_moves = root_state.get_legal_moves(root_player);
        
        best_child = nullptr;
        max_visits = -1;
        
        int iterations = 0;
        double C = get_ucb_constant(turn_number);
        auto deadline = search_start_time + chrono::duration<double>(adjusted_time_limit);
        
        while (true) {
            if ((iterations & 0xFF) == 0) {
                if (chrono::steady_clock::now() >= deadline) break;
                if (pool_ptr > MAX_NODES - 500) break; // Memory safety break
            }
            
            MCTSNode* node = root;
            Board state = root_state;
            int current_player = root_player;
            
            // Selection
            while (node->untried_moves.empty() && !node->children.empty()) {
                node = node->uct_select_child(C);
                state.apply_move(node->move);
                current_player = -current_player;
            }
            
            // Expansion
            double win_prob = 0.0;
            bool terminal = false;

            if (!node->untried_moves.empty()) {
                // Fast random index
                int idx = fast_rand() % node->untried_moves.size();
                Move m = node->untried_moves[idx];
                
                state.apply_move(m);
                current_player = -current_player;
                
                // Get moves for the NEXT player
                vector<Move> next_moves = state.get_legal_moves(current_player);
                
                // CRITICAL OPTIMIZATION: Check for terminal state immediately
                if (next_moves.empty()) {
                    // Next player has no moves -> Previous player (who just moved) wins
                    // If current_player == root_player, it means root_player is stuck (Loss -> 0.0)
                    // If current_player != root_player, opponent is stuck (Win -> 1.0)
                    // But wait: current_player is the one TO MOVE.
                    // If current_player (to move) has no moves, they LOSE.
                    // If current_player == root_player, root loses (0.0).
                    // If current_player != root_player, root wins (1.0).
                    win_prob = (current_player == root_player) ? 0.0 : 1.0;
                    terminal = true;
                }
                
                MCTSNode* new_node_ptr = new_node(node, m, -current_player);
                if (new_node_ptr) { // Check OOM
                    new_node_ptr->untried_moves = std::move(next_moves);
                    
                    // Swap-pop from parent
                    node->untried_moves[idx] = node->untried_moves.back();
                    node->untried_moves.pop_back();
                    
                    node->children.push_back(new_node_ptr);
                    node = new_node_ptr;
                } else {
                    // OOM recovery: just evaluate current state and don't expand
                    terminal = false; // Fallback to eval
                }
            } else {
                // No moves to expand and no children -> Node is terminal or fully explored
                // Re-evaluate terminal condition based on who's turn it is
                vector<Move> check_moves = state.get_legal_moves(current_player);
                if (check_moves.empty()) {
                    win_prob = (current_player == root_player) ? 0.0 : 1.0;
                    terminal = true;
                }
            }
            
            // Evaluation (Only if not terminal)
            if (!terminal) {
                win_prob = evaluate_optimized(state.grid, root_player);
            }
            
            // Backpropagation
            while (node != nullptr) {
                node->visits++;
                if (node->parent == root && node->visits > max_visits) {
                    max_visits = node->visits;
                    best_child = node;
                }
                // If the player who just moved matches root, this node represents a state AFTER root moved.
                if (node->player_just_moved == root_player) {
                    node->wins += win_prob;
                } else {
                    node->wins += (1.0 - win_prob);
                }
                node = node->parent;
            }
            iterations++;
        }
        
        if (!best_child && !root->children.empty()) return root->children[0]->move;
        return best_child ? best_child->move : Move(-1,-1,-1,-1,-1,-1);
    }
};

// --- MAIN MODULE ---
const double TIME_LIMIT = 0.98; // Slightly under 1.0s to be safe
const double FIRST_TURN_TIME_LIMIT = 1.95;
const double SAFETY_MARGIN = 0.05;

int main() {
    auto program_start_time = chrono::steady_clock::now();
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    
    Board board;
    string line;
    if (!getline(cin, line)) return 0;
    
    int turn_id;
    try { turn_id = stoi(line); } catch (...) { return 0; }
    
    vector<string> lines;
    int count = 2 * turn_id - 1;
    for (int i = 0; i < count; i++) {
        string l; getline(cin, l); lines.push_back(l);
    }
    
    istringstream iss(lines[0]);
    int val; iss >> val;
    int my_color = (val == -1) ? BLACK : WHITE;
    
    for (const string& line_str : lines) {
        istringstream iss2(line_str);
        vector<int> c; int v;
        while (iss2 >> v) c.push_back(v);
        if (c[0] == -1) continue;
        board.apply_move(Move(c[0], c[1], c[2], c[3], c[4], c[5]));
    }
    
    double original_limit = (turn_id == 1) ? FIRST_TURN_TIME_LIMIT : TIME_LIMIT;
    
    MCTS ai(original_limit); // seed generated in constructor
    ai.turn_number = turn_id;
    
    Move best_move = ai.search(board, my_color, program_start_time, original_limit, SAFETY_MARGIN);
    
    if (best_move.x0 != -1) {
        cout << (int)best_move.x0 << " " << (int)best_move.y0 << " " 
             << (int)best_move.x1 << " " << (int)best_move.y1 << " "
             << (int)best_move.x2 << " " << (int)best_move.y2 << endl;
    } else {
        cout << "-1 -1 -1 -1 -1 -1" << endl;
    }
    return 0;
}