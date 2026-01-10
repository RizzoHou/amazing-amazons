// bot020.cpp - Improved MCTS with pool exhaustion handling
// Key improvements over bot019:
// 1. Replace break on pool limits with "disable expansion" mode
// 2. Cap per-node move generation (300 moves max)
// 3. Remove heap allocations in evaluate() - use fixed arrays
// 4. Add static_assert for Move size
// 5. Fix search timing - parse input before starting timer
// 6. Clean up dead code

#include <iostream>
#include <vector>
#include <array>
#include <cmath>
#include <chrono>
#include <algorithm>
#include <sstream>
#include <cstring>
#include <cstdint>

using namespace std;

// --- CONSTANTS ---
const int GRID_SIZE = 8;
const int NUM_SQUARES = 64;
const int EMPTY = 0;
const int BLACK = 1;
const int WHITE = -1;
const int OBSTACLE = 2;

// Maximum moves to generate per node (prevents pool exhaustion)
const int MAX_MOVES_PER_NODE = 300;
const int MAX_MOVES_FOR_ROOT_NODE = 1000;

// 2D Directions for row,col movement
// N, S, W, E, NW, NE, SW, SE
const int DIRECTIONS[8][2] = {
    {-1, 0},  // N
    {1, 0},   // S
    {0, -1},  // W
    {0, 1},   // E
    {-1, -1}, // NW
    {-1, 1},  // NE
    {1, -1},  // SW
    {1, 1}    // SE
};

struct Move {
    int8_t x0, y0, x1, y1, x2, y2;
    Move() = default; 
    Move(int a, int b, int c, int d, int e, int f) 
        : x0((int8_t)a), y0((int8_t)b), x1((int8_t)c), y1((int8_t)d), x2((int8_t)e), y2((int8_t)f) {}
};

// Verify Move struct is packed correctly (6 bytes)
static_assert(sizeof(Move) == 6, "Move struct got padded; adjust pool size or pack it");

// --- FAST RNG ---
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

// --- MEMORY POOLS ---
const int MAX_NODES = 250000;
const int MAX_MOVES_POOL = 1800000;

class MCTSNode;

// Global storage
Move move_pool[MAX_MOVES_POOL];
int move_pool_ptr = 0;

MCTSNode* node_pool = nullptr;
int node_pool_ptr = 0;

// --- BOARD (1D Optimized) ---
class Board {
public:
    int8_t grid[NUM_SQUARES]; // 64 bytes - fits in one cache line
    
    Board() {
        memset(grid, EMPTY, sizeof(grid));
        init_board();
    }
    
    Board(const Board& other) {
        memcpy(grid, other.grid, sizeof(grid));
    }
    
    void init_board() {
        // Coords: y * 8 + x -> actually row * 8 + col
        grid[0*8 + 2] = BLACK; grid[2*8 + 0] = BLACK; 
        grid[5*8 + 0] = BLACK; grid[7*8 + 2] = BLACK;
        grid[0*8 + 5] = WHITE; grid[2*8 + 7] = WHITE; 
        grid[5*8 + 7] = WHITE; grid[7*8 + 5] = WHITE;
    }
    
    // Get legal moves with optional cap to prevent pool exhaustion
    // Returns pointer to start of moves in the global pool and count
    void get_legal_moves(int color, int& out_start_idx, int& out_count, int cap = MAX_MOVES_PER_NODE) const {
        out_start_idx = move_pool_ptr;
        int count = 0;
        
        for (int p = 0; p < NUM_SQUARES && count < cap; p++) {
            if (grid[p] != color) continue;
            
            int px = p / 8;
            int py = p % 8;
            
            for (int d = 0; d < 8 && count < cap; d++) {
                int d_row = DIRECTIONS[d][0];
                int d_col = DIRECTIONS[d][1];
                
                int nx = px, ny = py;
                
                while (count < cap) {
                    nx += d_row;
                    ny += d_col;
                    if (nx < 0 || nx >= 8 || ny < 0 || ny >= 8) break;
                    
                    int n_idx = (nx << 3) | ny; // nx * 8 + ny optimized
                    if (grid[n_idx] != EMPTY) break;
                    
                    // Shot phase
                    for (int ad = 0; ad < 8 && count < cap; ad++) {
                        int ad_row = DIRECTIONS[ad][0];
                        int ad_col = DIRECTIONS[ad][1];
                        
                        int ax = nx, ay = ny;
                        
                        while (count < cap) {
                            ax += ad_row;
                            ay += ad_col;
                            if (ax < 0 || ax >= 8 || ay < 0 || ay >= 8) break;
                            
                            int a_idx = (ax << 3) | ay;
                            if (grid[a_idx] != EMPTY && a_idx != p) break;
                            
                            // Emplace move
                            if (move_pool_ptr < MAX_MOVES_POOL) {
                                move_pool[move_pool_ptr++] = Move(px, py, nx, ny, ax, ay);
                                count++;
                            } else {
                                // Pool full - stop generating
                                out_count = count;
                                return;
                            }
                        }
                    }
                }
            }
        }
        out_count = count;
    }
    
    void apply_move(const Move& m) {
        int p_idx = (m.x0 << 3) | m.y0;
        int t_idx = (m.x1 << 3) | m.y1;
        int s_idx = (m.x2 << 3) | m.y2;
        
        int piece = grid[p_idx];
        grid[p_idx] = EMPTY;
        grid[t_idx] = piece;
        grid[s_idx] = OBSTACLE;
    }
};

// --- OPTIMIZED NODE (NO STL) ---
class MCTSNode {
public:
    MCTSNode* first_child;  // Left-child
    MCTSNode* next_sibling; // Right-sibling
    MCTSNode* parent;
    
    Move move; // The move that got us here
    
    // Pointer to global move pool for untried moves
    int moves_start_idx;    // -1 means moves not yet generated
    int moves_count;
    
    float wins;
    int visits;
    int8_t player_just_moved;
    bool moves_generated;   // NEW: Track if moves were actually generated
    
    void init(MCTSNode* p, Move m, int pjm) {
        parent = p;
        first_child = nullptr;
        next_sibling = nullptr;
        move = m;
        moves_start_idx = -1;
        moves_count = 0;
        wins = 0.0f;
        visits = 0;
        player_just_moved = (int8_t)pjm;
        moves_generated = false;
    }
    
    // Get best child using UCB
    MCTSNode* uct_select_child(float C) {
        MCTSNode* best = nullptr;
        float best_score = -1e9f;
        float log_v = std::log((float)visits + 1.0f);
        
        for (MCTSNode* c = first_child; c != nullptr; c = c->next_sibling) {
            float score = (c->wins / (c->visits + 1e-6f)) + C * std::sqrt(log_v / (c->visits + 1e-6f));
            if (score > best_score) {
                best_score = score;
                best = c;
            }
        }
        return best;
    }
    
    void add_child(MCTSNode* child) {
        child->next_sibling = first_child;
        first_child = child;
    }
    
    // Check if this is a terminal node (moves generated and none available)
    bool is_terminal() const {
        return moves_generated && moves_count == 0 && first_child == nullptr;
    }
    
    // Check if fully expanded (all untried moves consumed)
    bool is_fully_expanded() const {
        return moves_generated && moves_count == 0;
    }
};

// Allocator wrapper
MCTSNode* new_node(MCTSNode* p, Move m, int pjm) {
    if (node_pool_ptr >= MAX_NODES) return nullptr;
    MCTSNode* ptr = &node_pool[node_pool_ptr++];
    ptr->init(p, m, pjm);
    return ptr;
}

// --- EVALUATION HELPERS (NO HEAP ALLOCATIONS) ---
static int dist_my[NUM_SQUARES];
static int dist_op[NUM_SQUARES];
static int bfs_queue[NUM_SQUARES];

// BFS using fixed arrays
void run_bfs(const int8_t* grid, const int* sources, int src_count, int* dist_out) {
    for(int i = 0; i < NUM_SQUARES; ++i) dist_out[i] = 99;
    
    int head = 0, tail = 0;
    
    for (int i = 0; i < src_count; ++i) {
        int s = sources[i];
        dist_out[s] = 0;
        bfs_queue[tail++] = s;
    }
    
    while (head < tail) {
        int curr = bfs_queue[head++];
        int d = dist_out[curr] + 1;
        int cx = curr >> 3;  // curr / 8
        int cy = curr & 7;   // curr % 8
        
        for (int i = 0; i < 8; i++) {
            int nx = cx + DIRECTIONS[i][0];
            int ny = cy + DIRECTIONS[i][1];
            
            if (nx >= 0 && nx < 8 && ny >= 0 && ny < 8) {
                int n_idx = (nx << 3) | ny;
                if (grid[n_idx] == EMPTY && dist_out[n_idx] > d) {
                    dist_out[n_idx] = d;
                    bfs_queue[tail++] = n_idx;
                }
            }
        }
    }
}

inline int calc_mobility(const int8_t* grid, const int* pieces, int piece_count) {
    int mob = 0;
    for (int i = 0; i < piece_count; ++i) {
        int p = pieces[i];
        int px = p >> 3;
        int py = p & 7;
        for (int d = 0; d < 8; d++) {
            int nx = px + DIRECTIONS[d][0];
            int ny = py + DIRECTIONS[d][1];
            while (nx >= 0 && nx < 8 && ny >= 0 && ny < 8) {
                if (grid[(nx << 3) | ny] != EMPTY) break;
                mob++;
                nx += DIRECTIONS[d][0];
                ny += DIRECTIONS[d][1];
            }
        }
    }
    return mob;
}

// Weights table for turn-based evaluation
const double WEIGHTS_TABLE[28][5] = {
    { 0.07747, 0.05755, 0.64627, 0.70431, 0.02438 }, { 0.05093, 0.06276, 0.69898, 0.66192, 0.02362 },
    { 0.06036, 0.06253, 0.60094, 0.67719, 0.01873 }, { 0.07597, 0.06952, 0.69061, 0.67989, 0.02098 },
    { 0.08083, 0.08815, 0.58981, 0.54664, 0.02318 }, { 0.09155, 0.08397, 0.56392, 0.54319, 0.02317 },
    { 0.10653, 0.10479, 0.54840, 0.53023, 0.02084 }, { 0.11534, 0.11515, 0.53325, 0.52423, 0.02237 },
    { 0.12943, 0.12673, 0.50841, 0.52208, 0.02490 }, { 0.12882, 0.13946, 0.49621, 0.51776, 0.03045 },
    { 0.13701, 0.15338, 0.47601, 0.51500, 0.03249 }, { 0.14530, 0.15565, 0.45365, 0.50934, 0.03830 },
    { 0.14521, 0.16388, 0.44531, 0.50517, 0.04864 }, { 0.13750, 0.16326, 0.43619, 0.50328, 0.05912 },
    { 0.13565, 0.15529, 0.42382, 0.50288, 0.07437 }, { 0.12382, 0.10361, 0.50487, 0.55808, 0.02791 },
    { 0.11809, 0.14632, 0.40738, 0.41782, 0.10308 }, { 0.10805, 0.15043, 0.40520, 0.43073, 0.10967 },
    { 0.09668, 0.15666, 0.40215, 0.44165, 0.10906 }, { 0.10585, 0.16319, 0.38220, 0.45465, 0.10062 },
    { 0.11123, 0.15516, 0.36904, 0.46534, 0.09118 }, { 0.12535, 0.10492, 0.35567, 0.48043, 0.08337 },
    { 0.28657, 0.16655, 0.38060, 0.42472, 0.10316 }, { 0.07143, 0.16655, 0.36658, 0.39520, 0.02194 },
    { 0.07143, 0.16655, 0.36658, 0.39520, 0.02194 }, { 0.07143, 0.16655, 0.36658, 0.39520, 0.02194 },
    { 0.07143, 0.16655, 0.36658, 0.39520, 0.02194 }, { 0.07143, 0.14627, 0.36658, 0.39520, 0.02194 }
};

inline double fast_sigmoid(double x) {
    return 0.5 * (x / (1.0 + std::abs(x)) + 1.0);
}

// Precomputed powers of 2 for territory calculation
static const double POW2[] = { 0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625, 0.0078125, 0.00390625 };

double evaluate(const Board& board, int root_player, int turn) {
    // Fixed arrays instead of vectors - NO HEAP ALLOCATION
    int my_pieces[4], opp_pieces[4];
    int my_count = 0, opp_count = 0;
    
    for(int i = 0; i < NUM_SQUARES; ++i) {
        if(board.grid[i] == root_player) my_pieces[my_count++] = i;
        else if(board.grid[i] == -root_player) opp_pieces[opp_count++] = i;
    }
    
    run_bfs(board.grid, my_pieces, my_count, dist_my);
    run_bfs(board.grid, opp_pieces, opp_count, dist_op);
    
    double scores[5] = {0, 0, 0, 0, 0}; // qt, kt, qp, kp, mob
    
    for(int i = 0; i < NUM_SQUARES; ++i) {
        if(board.grid[i] != EMPTY) continue;
        int dm = dist_my[i];
        int do_ = dist_op[i];
        if(dm == 99 && do_ == 99) continue;
        
        if(dm < do_) {
            scores[0] += 1.0;
            if(dm < 4) scores[1] += (4 - dm);
        } else if(do_ < dm) {
            scores[0] -= 1.0;
            if(do_ < 4) scores[1] -= (4 - do_);
        }
        
        if(dm < 9) scores[2] += POW2[dm];
        if(do_ < 9) scores[2] -= POW2[do_];
        
        if(dm < 6) scores[3] += 1.0/(dm+1.0);
        if(do_ < 6) scores[3] -= 1.0/(do_+1.0);
    }
    
    scores[4] = (double)(calc_mobility(board.grid, my_pieces, my_count) - 
                         calc_mobility(board.grid, opp_pieces, opp_count));
    
    int idx = (turn >= 28) ? 27 : turn;
    double total = 0;
    for(int i = 0; i < 5; ++i) total += scores[i] * WEIGHTS_TABLE[idx][i];
    
    return fast_sigmoid(total * 0.2);
}

// --- SEARCH (with disable-expansion mode) ---
MCTSNode* best_child_global = nullptr;
int max_visits_global = -1;

Move search(const Board& root_state, int root_player, int turn, 
            chrono::steady_clock::time_point start, double timeout) {
    node_pool_ptr = 0;
    move_pool_ptr = 0;
    
    MCTSNode* root = new_node(nullptr, Move(), -root_player);
    // Generate moves for root (with higher cap for root node)
    root_state.get_legal_moves(root_player, root->moves_start_idx, root->moves_count, MAX_MOVES_FOR_ROOT_NODE);
    root->moves_generated = true;
    
    best_child_global = nullptr;
    max_visits_global = -1;
    
    int iterations = 0;
    float C = 0.177f * std::exp(-0.008f * (turn - 1.41f));
    
    auto deadline = start + chrono::duration<double>(timeout);
    
    // NEW: allow_expand flag - when false, we only do selection+eval+backprop
    bool allow_expand = true;
    
    while(true) {
        // Check time and pool limits every 256 iterations
        if ((iterations & 0xFF) == 0) {
            if (chrono::steady_clock::now() >= deadline) break;
            
            // NEW: Instead of breaking, just disable expansion
            if (node_pool_ptr > MAX_NODES - 500 || move_pool_ptr > MAX_MOVES_POOL - 5000) {
                allow_expand = false;
            }
        }
        
        MCTSNode* node = root;
        Board state = root_state;
        int current_player = root_player;
        
        // Selection: traverse down to a node that can be expanded or is terminal
        while (node->is_fully_expanded() && node->first_child != nullptr) {
            node = node->uct_select_child(C);
            state.apply_move(node->move);
            current_player = -current_player;
        }
        
        float win_prob = 0.0f;
        bool terminal = false;
        
        // Check if we reached a terminal state
        if (node->is_terminal()) {
            // Terminal: current player has no moves, so player_just_moved wins
            win_prob = (node->player_just_moved == root_player) ? 1.0f : 0.0f;
            terminal = true;
        }
        // Expansion (only if allowed and node has untried moves)
        else if (allow_expand && node->moves_count > 0) {
            // Pick random untried move
            int offset = fast_rand() % node->moves_count;
            int idx = node->moves_start_idx + offset;
            Move m = move_pool[idx];
            
            // Swap with last untried move
            int last_idx = node->moves_start_idx + node->moves_count - 1;
            std::swap(move_pool[idx], move_pool[last_idx]);
            node->moves_count--;
            
            state.apply_move(m);
            current_player = -current_player;
            
            MCTSNode* new_n = new_node(node, m, -current_player);
            if (new_n) {
                // Generate moves for new node
                state.get_legal_moves(current_player, new_n->moves_start_idx, new_n->moves_count);
                new_n->moves_generated = true;
                
                // Terminal check: no moves available
                if (new_n->moves_count == 0) {
                    // Current player stuck -> player who just moved wins
                    win_prob = (current_player == root_player) ? 0.0f : 1.0f;
                    terminal = true;
                }
                
                node->add_child(new_n);
                node = new_n;
            }
            // If new_node failed (OOM), just evaluate current state
        }
        
        // Evaluate the state - this handles:
        // - Expanded nodes that need evaluation
        // - Nodes that couldn't be expanded due to pool exhaustion (allow_expand=false)
        if (!terminal) {
            win_prob = (float)evaluate(state, root_player, turn);
        }
        
        // Backpropagation
        while (node) {
            node->visits++;
            if (node->parent == root && node->visits > max_visits_global) {
                max_visits_global = node->visits;
                best_child_global = node;
            }
            
            // Accumulate wins based on perspective
            if (node->player_just_moved == root_player) {
                node->wins += win_prob;
            } else {
                node->wins += (1.0f - win_prob);
            }
            node = node->parent;
        }
        
        iterations++;
    }
    
    if (best_child_global) return best_child_global->move;
    if (root->first_child) return root->first_child->move;
    return Move(-1,-1,-1,-1,-1,-1);
}

// --- MAIN (with fixed timing - parse input before starting search timer) ---
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    
    // Allocate node pool on heap
    node_pool = new MCTSNode[MAX_NODES];
    
    // PARSE INPUT FIRST (before starting search timer)
    Board board;
    string line;
    if (!getline(cin, line)) return 0;
    int turn = stoi(line);
    
    vector<string> lines;
    int count = 2 * turn - 1;
    for(int i = 0; i < count; ++i) {
        string l; 
        getline(cin, l); 
        lines.push_back(l);
    }
    
    int my_color = -1;
    {
        stringstream ss(lines[0]);
        int v; ss >> v;
        if(v == -1) my_color = BLACK; 
        else my_color = WHITE;
    }
    
    for(const auto& l : lines) {
        stringstream ss(l);
        int c[6];
        ss >> c[0];
        if(c[0] == -1) continue;
        for(int k = 1; k < 6; ++k) ss >> c[k];
        board.apply_move(Move(c[0], c[1], c[2], c[3], c[4], c[5]));
    }
    
    seed_rng();
    
    // NOW start the search timer (after parsing is complete)
    auto search_start = chrono::steady_clock::now();
    double budget = (turn == 1) ? 1.90 : 0.93;  // Safety margin
    
    Move best = search(board, my_color, turn, search_start, budget);
    
    if(best.x0 != -1) {
        cout << (int)best.x0 << " " << (int)best.y0 << " " 
             << (int)best.x1 << " " << (int)best.y1 << " " 
             << (int)best.x2 << " " << (int)best.y2 << endl;
    } else {
        cout << "-1 -1 -1 -1 -1 -1" << endl;
    }
    
    // delete[] node_pool; // OS cleans up on exit
    return 0;
}
