#include <iostream>
#include <vector>
#include <array>
#include <cmath>
#include <random>
#include <chrono>
#include <algorithm>
#include <sstream>
#include <fstream>
#include <iomanip>
#include <ctime>

using namespace std;

// --- LOGGING MODULE ---

// Global log file streams
static ofstream log_stream;           // For search iterations
static ofstream turn_log_stream;      // For turn cycle phases
static bool log_initialized = false;
static bool turn_log_initialized = false;
static string log_filename;
static string turn_log_filename;

// Initialize search logging with timestamp
void init_logging() {
    if (log_initialized) return;
    
    // Generate timestamp for filename
    auto now = chrono::system_clock::now();
    auto now_time_t = chrono::system_clock::to_time_t(now);
    auto now_ms = chrono::duration_cast<chrono::milliseconds>(
        now.time_since_epoch()
    ) % 1000;
    
    stringstream ss;
    ss << "logs/bot010_time_log_";
    ss << put_time(localtime(&now_time_t), "%Y%m%d_%H%M%S");
    ss << "_" << setfill('0') << setw(3) << now_ms.count();
    ss << ".txt";
    
    log_filename = ss.str();
    
    // Open log file
    log_stream.open(log_filename, ios::out | ios::app);
    if (!log_stream.is_open()) {
        // Try to create logs directory if it doesn't exist
        system("mkdir -p logs 2>/dev/null");
        log_stream.open(log_filename, ios::out | ios::app);
    }
    
    if (log_stream.is_open()) {
        log_initialized = true;
        // Write header
        log_stream << "# Bot010 Time Cost Log" << endl;
        log_stream << "# Format: timestamp,turn_number,iterations_so_far,elapsed_time_seconds,cumulative_iterations" << endl;
        log_stream << "# Created: " << put_time(localtime(&now_time_t), "%Y-%m-%d %H:%M:%S") << endl;
        log_stream.flush();
    }
}

// Initialize turn cycle logging with timestamp
void init_turn_logging() {
    if (turn_log_initialized) return;
    
    // Generate timestamp for filename
    auto now = chrono::system_clock::now();
    auto now_time_t = chrono::system_clock::to_time_t(now);
    auto now_ms = chrono::duration_cast<chrono::milliseconds>(
        now.time_since_epoch()
    ) % 1000;
    
    stringstream ss;
    ss << "logs/bot010_turn_cycle_log_";
    ss << put_time(localtime(&now_time_t), "%Y%m%d_%H%M%S");
    ss << "_" << setfill('0') << setw(3) << now_ms.count();
    ss << ".txt";
    
    turn_log_filename = ss.str();
    
    // Open log file
    turn_log_stream.open(turn_log_filename, ios::out | ios::app);
    if (!turn_log_stream.is_open()) {
        // Try to create logs directory if it doesn't exist
        system("mkdir -p logs 2>/dev/null");
        turn_log_stream.open(turn_log_filename, ios::out | ios::app);
    }
    
    if (turn_log_stream.is_open()) {
        turn_log_initialized = true;
        // Write header
        turn_log_stream << "# Bot010 Turn Cycle Log" << endl;
        turn_log_stream << "# Format: timestamp,turn_number,phase,phase_time_seconds,cumulative_time_seconds,notes" << endl;
        turn_log_stream << "# Created: " << put_time(localtime(&now_time_t), "%Y-%m-%d %H:%M:%S") << endl;
        turn_log_stream.flush();
    }
}

// Log time cost for current iteration
void log_time_cost(int turn_number, int iterations, double elapsed_time, int cumulative_iterations) {
    if (!log_initialized) init_logging();
    if (!log_stream.is_open()) return;
    
    auto now = chrono::system_clock::now();
    auto now_time_t = chrono::system_clock::to_time_t(now);
    auto now_ms = chrono::duration_cast<chrono::milliseconds>(
        now.time_since_epoch()
    ) % 1000;
    
    log_stream << put_time(localtime(&now_time_t), "%Y-%m-%dT%H:%M:%S");
    log_stream << "." << setfill('0') << setw(3) << now_ms.count();
    log_stream << "," << turn_number;
    log_stream << "," << iterations;
    log_stream << "," << fixed << setprecision(6) << elapsed_time;
    log_stream << "," << cumulative_iterations;
    log_stream << endl;
    log_stream.flush();
}

// Log final search results
void log_final_results(int turn_number, double total_time, int total_iterations, double time_limit, bool is_first_turn) {
    if (!log_initialized) init_logging();
    if (!log_stream.is_open()) return;
    
    auto now = chrono::system_clock::now();
    auto now_time_t = chrono::system_clock::to_time_t(now);
    auto now_ms = chrono::duration_cast<chrono::milliseconds>(
        now.time_since_epoch()
    ) % 1000;
    
    log_stream << put_time(localtime(&now_time_t), "%Y-%m-%dT%H:%M:%S");
    log_stream << "." << setfill('0') << setw(3) << now_ms.count();
    log_stream << "," << turn_number;
    log_stream << ",FINAL";
    log_stream << "," << fixed << setprecision(6) << total_time;
    log_stream << "," << total_iterations;
    log_stream << "," << time_limit;
    log_stream << "," << (is_first_turn ? "FIRST" : "NORMAL");
    log_stream << endl;
    log_stream.flush();
}

// Log turn cycle phase
void log_turn_phase(int turn_number, const string& phase, double phase_time, double cumulative_time, const string& notes = "") {
    if (!turn_log_initialized) init_turn_logging();
    if (!turn_log_stream.is_open()) return;
    
    auto now = chrono::system_clock::now();
    auto now_time_t = chrono::system_clock::to_time_t(now);
    auto now_ms = chrono::duration_cast<chrono::milliseconds>(
        now.time_since_epoch()
    ) % 1000;
    
    turn_log_stream << put_time(localtime(&now_time_t), "%Y-%m-%dT%H:%M:%S");
    turn_log_stream << "." << setfill('0') << setw(3) << now_ms.count();
    turn_log_stream << "," << turn_number;
    turn_log_stream << "," << phase;
    turn_log_stream << "," << fixed << setprecision(6) << phase_time;
    turn_log_stream << "," << fixed << setprecision(6) << cumulative_time;
    turn_log_stream << "," << notes;
    turn_log_stream << endl;
    turn_log_stream.flush();
}

// Helper class for timing turn phases
class TurnTimer {
private:
    chrono::steady_clock::time_point turn_start;
    chrono::steady_clock::time_point last_checkpoint;
    int turn_number;
    double cumulative_time;
    
public:
    TurnTimer(int turn) : turn_number(turn), cumulative_time(0.0) {
        turn_start = chrono::steady_clock::now();
        last_checkpoint = turn_start;
    }
    
    double checkpoint(const string& phase, const string& notes = "") {
        auto now = chrono::steady_clock::now();
        double phase_time = chrono::duration<double>(now - last_checkpoint).count();
        cumulative_time += phase_time;
        
        log_turn_phase(turn_number, phase, phase_time, cumulative_time, notes);
        
        last_checkpoint = now;
        return phase_time;
    }
    
    double get_total_time() const {
        auto now = chrono::steady_clock::now();
        return chrono::duration<double>(now - turn_start).count();
    }
    
    double get_cumulative_time() const {
        return cumulative_time;
    }
};

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

// --- OPTIMIZATION BUFFERS ---
// Distances for player and opponent (99 represents infinity/unreachable)
static int dist_my[GRID_SIZE][GRID_SIZE];
static int dist_op[GRID_SIZE][GRID_SIZE];

// A lightweight, fixed-size queue to replace std::deque
struct FastQueue {
    int qx[GRID_SIZE * GRID_SIZE];
    int qy[GRID_SIZE * GRID_SIZE];
    int head, tail;
    
    void clear() { head = 0; tail = 0; }
    void push(int x, int y) {
        qx[tail] = x;
        qy[tail] = y;
        tail++;
    }
    bool not_empty() const { return head < tail; }
    void pop(int &x, int &y) {
        x = qx[head];
        y = qy[head];
        head++;
    }
};

static FastQueue bfs_q;

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
    
    void perform_fast_bfs(const array<array<int, GRID_SIZE>, GRID_SIZE>& grid, 
                          const vector<pair<int, int>>& pieces, 
                          int dist_out[GRID_SIZE][GRID_SIZE]) {
        
        // 1. Reset distances to Infinity (99)
        for (int i = 0; i < GRID_SIZE; i++) {
            // Unrolling inner loop slightly for speed
            dist_out[i][0] = 99; dist_out[i][1] = 99; dist_out[i][2] = 99; dist_out[i][3] = 99;
            dist_out[i][4] = 99; dist_out[i][5] = 99; dist_out[i][6] = 99; dist_out[i][7] = 99;
        }
        
        bfs_q.clear();
        
        // 2. Initialize Queue with starting piece locations
        for (const auto& p : pieces) {
            dist_out[p.first][p.second] = 0;
            bfs_q.push(p.first, p.second);
        }
        
        // 3. Process Queue
        int cx, cy;
        while (bfs_q.not_empty()) {
            bfs_q.pop(cx, cy);
            int current_dist = dist_out[cx][cy];
            int next_dist = current_dist + 1;
            
            for (int i = 0; i < 8; i++) {
                int nx = cx + DIRECTIONS[i][0];
                int ny = cy + DIRECTIONS[i][1];
                
                // Bounds check + Empty check + Better distance check
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
    
    double evaluate_optimized(const array<array<int, GRID_SIZE>, GRID_SIZE>& grid, int root_player) {
        // 1. Identify piece locations
        vector<pair<int, int>> my_pieces;
        vector<pair<int, int>> opp_pieces;
        my_pieces.reserve(4);
        opp_pieces.reserve(4);
        
        for (int i = 0; i < GRID_SIZE; i++) {
            for (int j = 0; j < GRID_SIZE; j++) {
                if (grid[i][j] == root_player) my_pieces.push_back({i, j});
                else if (grid[i][j] == -root_player) opp_pieces.push_back({i, j});
            }
        }
        
        // 2. Run BFS twice (populates static arrays dist_my and dist_op)
        perform_fast_bfs(grid, my_pieces, dist_my);
        perform_fast_bfs(grid, opp_pieces, dist_op);
        
        // 3. Single Pass Scoring
        double queen_territory = 0;
        double king_territory = 0; // Component 2
        double queen_position = 0; // Component 3
        double king_position = 0;  // Component 4
        
        // Pre-calculated powers of 2 for position score (2^-x) to avoid pow() calls
        // index 0 is unused, 1..20
        static const double POW2[] = {
            0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625, 0.0078125,
            0.00390625, 0.001953125, 0.0009765625
        }; 
        
        for (int i = 0; i < GRID_SIZE; i++) {
            for (int j = 0; j < GRID_SIZE; j++) {
                if (grid[i][j] != EMPTY) continue; // Skip non-empty squares
                
                int dm = dist_my[i][j];
                int dopp = dist_op[i][j];
                
                // Skip if unreachable by both
                if (dm == 99 && dopp == 99) continue;
                
                // Component 1: Queen Territory (Who is closer?)
                if (dm < dopp) {
                    queen_territory += 1.0;
                } else if (dopp < dm) {
                    queen_territory -= 1.0;
                }
                
                // Component 2: King Territory (Weight nearby squares)
                // Original logic: weight is (4 - d) for d in [1, 2, 3]
                if (dm < dopp && dm < 4) {
                    king_territory += (4 - dm);
                } else if (dopp < dm && dopp < 4) {
                    king_territory -= (4 - dopp);
                }
                
                // Component 3: Queen Position (Score based on distance decay)
                if (dm < 10) queen_position += POW2[dm];
                if (dopp < 10) queen_position -= POW2[dopp];
                
                // Component 4: King Position (Original logic was: count / (d+1))
                // Simplified efficient version:
                if (dm < 6) king_position += 1.0 / (dm + 1.0);
                if (dopp < 6) king_position -= 1.0 / (dopp + 1.0);
            }
        }
        
        // Component 5: Mobility
        // Use the existing calc_mobility function (it is relatively cheap compared to allocations)
        int my_mobility = calc_mobility(grid, my_pieces);
        int opp_mobility = calc_mobility(grid, opp_pieces);
        double mobility = my_mobility - opp_mobility;
        
        // 4. Weighting
        const double* weights = get_phase_weights(turn_number);
        
        double score = (
            weights[0] * queen_territory +
            weights[1] * king_territory +
            weights[2] * queen_position +
            weights[3] * king_position +
            weights[4] * mobility
        ) * 0.20;
        
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
            
            // Evaluation - OPTIMIZED VERSION
            double win_prob = evaluate_optimized(state.grid, root_player);
            
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
            
            // Log every 1000 iterations
            if (iterations % 1000 == 0) {
                auto log_time = chrono::steady_clock::now();
                double log_elapsed = chrono::duration<double>(log_time - start_time).count();
                log_time_cost(turn_number, iterations, log_elapsed, iterations);
            }
        }
        
        // Log final results
        auto end_time = chrono::steady_clock::now();
        double total_elapsed = chrono::duration<double>(end_time - start_time).count();
        bool is_first_turn = (turn_number == 1);
        log_final_results(turn_number, total_elapsed, iterations, time_limit, is_first_turn);
        
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
    
    // Initialize turn logging for first turn initialization
    init_turn_logging();
    
    // First turn initialization timer
    TurnTimer init_timer(0);  // Turn 0 for initialization
    
    Board board;
    init_timer.checkpoint("BOARD_CREATE");
    
    int my_color = 0;
    MCTS ai(TIME_LIMIT);
    init_timer.checkpoint("MCTS_CREATE");
    
    // First turn
    string line;
    if (!getline(cin, line)) return 0;
    
    int turn_id;
    try {
        turn_id = stoi(line);
    } catch (...) {
        return 0;
    }
    
    init_timer.checkpoint("TURN_ID_PARSE", "turn_id=" + to_string(turn_id));
    
    vector<string> lines;
    int count = 2 * turn_id - 1;
    for (int i = 0; i < count; i++) {
        string l;
        if (!getline(cin, l)) return 0;
        lines.push_back(l);
    }
    
    init_timer.checkpoint("INPUT_READING", "lines=" + to_string(lines.size()));
    
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
    
    init_timer.checkpoint("COLOR_DETERMINATION", "color=" + to_string(my_color));
    
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
    
    init_timer.checkpoint("MOVE_REPLAY", "moves_replayed=" + to_string(lines.size()));
    
    // Set turn number
    ai.turn_number = turn_id;
    
    double limit = (turn_id == 1) ? FIRST_TURN_TIME_LIMIT : TIME_LIMIT;
    ai.time_limit = limit;
    
    init_timer.checkpoint("TURN_SETUP", "time_limit=" + to_string(limit));
    
    // Log initialization complete
    init_timer.checkpoint("INIT_COMPLETE");
    
    // Start turn 1 timer
    TurnTimer turn_timer(turn_id);
    
    Move best_move = ai.search(board, my_color);
    
    turn_timer.checkpoint("SEARCH_COMPLETE");
    
    if (best_move.x0 != -1) {
        cout << best_move.x0 << " " << best_move.y0 << " " 
             << best_move.x1 << " " << best_move.y1 << " "
             << best_move.x2 << " " << best_move.y2 << endl;
        
        turn_timer.checkpoint("OUTPUT_GENERATION");
        
        board.apply_move(best_move);
        turn_timer.checkpoint("BOARD_UPDATE_SELF");
        
        ai.advance_root(best_move);
        turn_timer.checkpoint("ADVANCE_ROOT_SELF");
    } else {
        cout << "-1 -1 -1 -1 -1 -1" << endl;
        turn_timer.checkpoint("NO_MOVE_OUTPUT");
        return 0;
    }
    
    cout << ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<" << endl;
    cout.flush();
    
    turn_timer.checkpoint("KEEP_RUNNING_SENT");
    
    // Subsequent turns
    while (true) {
        try {
            // Start new turn timer
            TurnTimer turn_timer(ai.turn_number + 1);  // +1 because turn_number hasn't been incremented yet
            
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
            
            turn_timer.checkpoint("INPUT_PARSING");
            
            if (found) {
                board.apply_move(opponent_move);
                turn_timer.checkpoint("BOARD_UPDATE_OPP");
                
                ai.advance_root(opponent_move);
                turn_timer.checkpoint("ADVANCE_ROOT_OPP");
            }
            
            ai.turn_number++;
            ai.time_limit = TIME_LIMIT;
            
            turn_timer.checkpoint("TURN_INCREMENT");
            
            best_move = ai.search(board, my_color);
            
            turn_timer.checkpoint("SEARCH_COMPLETE");
            
            if (best_move.x0 != -1) {
                cout << best_move.x0 << " " << best_move.y0 << " " 
                     << best_move.x1 << " " << best_move.y1 << " "
                     << best_move.x2 << " " << best_move.y2 << endl;
                
                turn_timer.checkpoint("OUTPUT_GENERATION");
                
                board.apply_move(best_move);
                turn_timer.checkpoint("BOARD_UPDATE_SELF");
                
                ai.advance_root(best_move);
                turn_timer.checkpoint("ADVANCE_ROOT_SELF");
            } else {
                cout << "-1 -1 -1 -1 -1 -1" << endl;
                turn_timer.checkpoint("NO_MOVE_OUTPUT");
                break;
            }
            
            cout << ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<" << endl;
            cout.flush();
            
            turn_timer.checkpoint("KEEP_RUNNING_SENT");
            
        } catch (...) {
            break;
        }
    }
    
    return 0;
}
