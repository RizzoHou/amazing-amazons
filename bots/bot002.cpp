// bot002.cpp - Optimized Amazons Bot with Bitboard Representation
// Optimizations: Bitboards, Fast BFS, Node Pool, Move Ordering, Xorshift PRNG
// Target: 50-100% more MCTS iterations vs bot001

#include <iostream>
#include <vector>
#include <array>
#include <cmath>
#include <chrono>
#include <algorithm>
#include <cstring>
#include <sstream>

using namespace std;

// --- BITBOARD CONSTANTS ---
const int GRID_SIZE = 8;
const int BLACK = 0;
const int WHITE = 1;

// Edge masks to prevent wrapping
const uint64_t NOT_A_FILE = 0xfefefefefefefefeULL;  // ~column 0
const uint64_t NOT_H_FILE = 0x7f7f7f7f7f7f7f7fULL;  // ~column 7
const uint64_t NOT_AB_FILE = 0xfcfcfcfcfcfcfcfcULL; // ~columns 0-1
const uint64_t NOT_GH_FILE = 0x3f3f3f3f3f3f3f3fULL; // ~columns 6-7

// Direction offsets for array-based iteration
const int DX[8] = {-1, -1, -1,  0,  0,  1,  1,  1};
const int DY[8] = {-1,  0,  1, -1,  1, -1,  0,  1};

// --- FAST PRNG (Xorshift64) ---
static uint64_t xorshift_seed = 123456789ULL;

inline void init_xorshift(uint64_t seed) {
    xorshift_seed = seed;
}

inline uint64_t xorshift64() {
    xorshift_seed ^= xorshift_seed << 13;
    xorshift_seed ^= xorshift_seed >> 7;
    xorshift_seed ^= xorshift_seed << 17;
    return xorshift_seed;
}

// --- BITBOARD UTILITY FUNCTIONS ---

// Convert (x, y) to bit index (0-63)
inline int coord_to_idx(int x, int y) {
    return x * 8 + y;
}

// Convert bit index to (x, y)
inline void idx_to_coord(int idx, int& x, int& y) {
    x = idx >> 3;  // idx / 8
    y = idx & 7;   // idx % 8
}

// Count set bits (population count)
inline int popcount(uint64_t b) {
    return __builtin_popcountll(b);
}

// Get index of least significant bit
inline int lsb_index(uint64_t b) {
    return __builtin_ctzll(b);
}

// Clear least significant bit
inline uint64_t clear_lsb(uint64_t b) {
    return b & (b - 1);
}

// Bitboard shift functions for move generation
inline uint64_t shift_N(uint64_t b)  { return b << 8; }
inline uint64_t shift_S(uint64_t b)  { return b >> 8; }
inline uint64_t shift_E(uint64_t b)  { return (b << 1) & NOT_A_FILE; }
inline uint64_t shift_W(uint64_t b)  { return (b >> 1) & NOT_H_FILE; }
inline uint64_t shift_NE(uint64_t b) { return (b << 9) & NOT_A_FILE; }
inline uint64_t shift_NW(uint64_t b) { return (b << 7) & NOT_H_FILE; }
inline uint64_t shift_SE(uint64_t b) { return (b >> 7) & NOT_A_FILE; }
inline uint64_t shift_SW(uint64_t b) { return (b >> 9) & NOT_H_FILE; }

// Array of shift functions for iteration
typedef uint64_t (*ShiftFunc)(uint64_t);
const ShiftFunc SHIFTS[8] = {
    shift_NW, shift_N, shift_NE,
    shift_W,           shift_E,
    shift_SW, shift_S, shift_SE
};

// --- BOARD STRUCTURE ---
struct Board {
    uint64_t queens[2];  // BLACK=0, WHITE=1
    uint64_t arrows;     // All obstacles
    
    Board() : arrows(0) {
        queens[0] = 0;
        queens[1] = 0;
        init_board();
    }
    
    void init_board() {
        // Black queens (color=0)
        queens[BLACK] |= (1ULL << coord_to_idx(0, 2));
        queens[BLACK] |= (1ULL << coord_to_idx(2, 0));
        queens[BLACK] |= (1ULL << coord_to_idx(5, 0));
        queens[BLACK] |= (1ULL << coord_to_idx(7, 2));
        
        // White queens (color=1)
        queens[WHITE] |= (1ULL << coord_to_idx(0, 5));
        queens[WHITE] |= (1ULL << coord_to_idx(2, 7));
        queens[WHITE] |= (1ULL << coord_to_idx(5, 7));
        queens[WHITE] |= (1ULL << coord_to_idx(7, 5));
    }
    
    Board copy() const {
        Board b;
        b.queens[0] = queens[0];
        b.queens[1] = queens[1];
        b.arrows = arrows;
        return b;
    }
};

// --- MOVE STRUCTURE ---
struct Move {
    int src, dest, arrow;  // Bit indices
    int score;             // For move ordering
    
    Move() : src(0), dest(0), arrow(0), score(0) {}
    Move(int s, int d, int a) : src(s), dest(d), arrow(a), score(0) {}
    
    bool operator==(const Move& other) const {
        return src == other.src && dest == other.dest && arrow == other.arrow;
    }
};

// --- MOVE GENERATION ---

// Slide a bitboard in a direction until blocked
inline uint64_t slide_direction(uint64_t pos, uint64_t occupied, ShiftFunc shift) {
    uint64_t moves = 0;
    uint64_t next = shift(pos);
    while (next && !(next & occupied)) {
        moves |= next;
        next = shift(next);
    }
    return moves;
}

// Generate all legal moves for a player (optimized bitboard version)
void generate_moves(const Board& board, int color, vector<Move>& moves) {
    moves.clear();
    moves.reserve(800);  // Pre-allocate to avoid reallocations
    
    uint64_t my_queens = board.queens[color];
    uint64_t occupied = board.queens[0] | board.queens[1] | board.arrows;
    
    // Iterate over each queen
    uint64_t queens_copy = my_queens;
    while (queens_copy) {
        int src_idx = lsb_index(queens_copy);
        uint64_t src_bit = 1ULL << src_idx;
        queens_copy = clear_lsb(queens_copy);
        
        // Occupied without this source queen
        uint64_t occ_without_src = occupied ^ src_bit;
        
        // Generate all destinations for this queen
        uint64_t destinations = 0;
        for (int d = 0; d < 8; d++) {
            destinations |= slide_direction(src_bit, occ_without_src, SHIFTS[d]);
        }
        
        // For each destination
        uint64_t dests_copy = destinations;
        while (dests_copy) {
            int dest_idx = lsb_index(dests_copy);
            uint64_t dest_bit = 1ULL << dest_idx;
            dests_copy = clear_lsb(dests_copy);
            
            // Occupied with queen at destination (without source)
            uint64_t occ_at_dest = occ_without_src | dest_bit;
            
            // Generate all arrow positions
            uint64_t arrow_positions = 0;
            for (int d = 0; d < 8; d++) {
                arrow_positions |= slide_direction(dest_bit, occ_at_dest, SHIFTS[d]);
            }
            
            // For each arrow position
            uint64_t arrows_copy = arrow_positions;
            while (arrows_copy) {
                int arrow_idx = lsb_index(arrows_copy);
                arrows_copy = clear_lsb(arrows_copy);
                
                moves.push_back(Move(src_idx, dest_idx, arrow_idx));
            }
        }
    }
}

// Apply a move to the board
inline void apply_move(Board& board, const Move& move, int color) {
    uint64_t src_bit = 1ULL << move.src;
    uint64_t dest_bit = 1ULL << move.dest;
    uint64_t arrow_bit = 1ULL << move.arrow;
    
    board.queens[color] ^= src_bit;   // Remove from source
    board.queens[color] |= dest_bit;  // Add to destination
    board.arrows |= arrow_bit;        // Place arrow
}

// --- OPTIMIZED EVALUATION ---

// Precomputed weight tables for on-the-fly accumulation
const double QUEEN_TERR_WEIGHT[64] = {
    0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625, 0.0078125,
    0.00390625, 0.001953125, 0.0009765625, 0.00048828125, 0.000244140625, 0.0001220703125,
    6.103515625e-05, 3.0517578125e-05, 1.52587890625e-05, 7.62939453125e-06, 3.814697265625e-06,
    1.9073486328125e-06, 9.5367431640625e-07, 4.76837158203125e-07, 2.384185791015625e-07,
    1.1920928955078125e-07, 5.960464477539063e-08, 2.9802322387695312e-08, 1.4901161193847656e-08,
    7.450580596923828e-09, 3.725290298461914e-09, 1.862645149230957e-09, 9.313225746154785e-10,
    4.656612873077393e-10, 2.3283064365386963e-10, 1.1641532182693481e-10, 5.820766091346741e-11,
    2.9103830456733704e-11, 1.4551915228366852e-11, 7.275957614183426e-12, 3.637978807091713e-12,
    1.8189894035458565e-12, 9.094947017729282e-13, 4.547473508864641e-13, 2.2737367544323206e-13,
    1.1368683772161603e-13, 5.684341886080802e-14, 2.842170943040401e-14, 1.4210854715202004e-14,
    7.105427357601002e-15, 3.552713678800501e-15, 1.7763568394002505e-15, 8.881784197001252e-16,
    4.440892098500626e-16, 2.220446049250313e-16, 1.1102230246251565e-16, 5.551115123125783e-17,
    2.7755575615628914e-17, 1.3877787807814457e-17, 6.938893903907228e-18, 3.469446951953614e-18,
    1.734723475976807e-18, 8.673617379884035e-19, 4.3368086899420177e-19, 2.1684043449710089e-19
};

const double KING_TERR_WEIGHT[64] = {
    0, 3.0, 2.0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
};

const double QUEEN_POS_WEIGHT[64] = {
    0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625, 0.0078125,
    0.00390625, 0.001953125, 0.0009765625, 0.00048828125, 0.000244140625, 0.0001220703125,
    6.103515625e-05, 3.0517578125e-05, 1.52587890625e-05, 7.62939453125e-06, 3.814697265625e-06,
    1.9073486328125e-06, 9.5367431640625e-07, 4.76837158203125e-07, 2.384185791015625e-07,
    1.1920928955078125e-07, 5.960464477539063e-08, 2.9802322387695312e-08, 1.4901161193847656e-08,
    7.450580596923828e-09, 3.725290298461914e-09, 1.862645149230957e-09, 9.313225746154785e-10,
    4.656612873077393e-10, 2.3283064365386963e-10, 1.1641532182693481e-10, 5.820766091346741e-11,
    2.9103830456733704e-11, 1.4551915228366852e-11, 7.275957614183426e-12, 3.637978807091713e-12,
    1.8189894035458565e-12, 9.094947017729282e-13, 4.547473508864641e-13, 2.2737367544323206e-13,
    1.1368683772161603e-13, 5.684341886080802e-14, 2.842170943040401e-14, 1.4210854715202004e-14,
    7.105427357601002e-15, 3.552713678800501e-15, 1.7763568394002505e-15, 8.881784197001252e-16,
    4.440892098500626e-16, 2.220446049250313e-16, 1.1102230246251565e-16, 5.551115123125783e-17,
    2.7755575615628914e-17, 1.3877787807814457e-17, 6.938893903907228e-18, 3.469446951953614e-18,
    1.734723475976807e-18, 8.673617379884035e-19, 4.3368086899420177e-19, 2.1684043449710089e-19
};

const double KING_POS_WEIGHT[7] = {
    0, 1.0, 0.5, 0.333333, 0.25, 0.2, 0.166667
};

// Centrality table for move ordering (precomputed)
const int CENTRALITY[64] = {
    0, 1, 2, 3, 3, 2, 1, 0,
    1, 2, 3, 4, 4, 3, 2, 1,
    2, 3, 4, 5, 5, 4, 3, 2,
    3, 4, 5, 6, 6, 5, 4, 3,
    3, 4, 5, 6, 6, 5, 4, 3,
    2, 3, 4, 5, 5, 4, 3, 2,
    1, 2, 3, 4, 4, 3, 2, 1,
    0, 1, 2, 3, 3, 2, 1, 0
};

// Optimized BFS with fixed arrays and on-the-fly weight accumulation
void bfs_evaluate(const Board& board, int color, double& queen_terr, double& king_terr,
                  double& queen_pos, double& king_pos) {
    static char dist[64];
    static int queue[64];
    
    memset(dist, -1, 64);
    int head = 0, tail = 0;
    
    queen_terr = 0.0;
    king_terr = 0.0;
    queen_pos = 0.0;
    king_pos = 0.0;
    
    // Initialize with our queens
    uint64_t my_queens = board.queens[color];
    while (my_queens) {
        int idx = lsb_index(my_queens);
        dist[idx] = 0;
        queue[tail++] = idx;
        my_queens = clear_lsb(my_queens);
    }
    
    uint64_t occupied = board.queens[0] | board.queens[1] | board.arrows;
    
    // BFS with on-the-fly accumulation
    while (head < tail) {
        int idx = queue[head++];
        int x, y;
        idx_to_coord(idx, x, y);
        int d = dist[idx] + 1;
        
        for (int dir = 0; dir < 8; dir++) {
            int nx = x + DX[dir];
            int ny = y + DY[dir];
            if (nx < 0 || nx >= 8 || ny < 0 || ny >= 8) continue;
            
            int nidx = coord_to_idx(nx, ny);
            if (dist[nidx] != -1) continue;
            
            // Check if cell is empty
            uint64_t bit = 1ULL << nidx;
            if (occupied & bit) continue;
            
            dist[nidx] = d;
            queue[tail++] = nidx;
            
            // Accumulate scores on-the-fly
            if (d < 64) {
                queen_terr += QUEEN_TERR_WEIGHT[d];
                queen_pos += QUEEN_POS_WEIGHT[d];
                
                if (d <= 3) {
                    king_terr += KING_TERR_WEIGHT[d];
                }
                if (d < 7) {
                    king_pos += KING_POS_WEIGHT[d];
                }
            }
        }
    }
}

// Calculate mobility (for component 5)
int calc_mobility(const Board& board, int color) {
    int mobility = 0;
    uint64_t my_queens = board.queens[color];
    uint64_t occupied = board.queens[0] | board.queens[1] | board.arrows;
    
    while (my_queens) {
        int idx = lsb_index(my_queens);
        uint64_t queen_bit = 1ULL << idx;
        my_queens = clear_lsb(my_queens);
        
        uint64_t occ_without = occupied ^ queen_bit;
        
        for (int d = 0; d < 8; d++) {
            uint64_t moves = slide_direction(queen_bit, occ_without, SHIFTS[d]);
            mobility += popcount(moves);
        }
    }
    return mobility;
}

// Phase weights
const double EARLY_WEIGHTS[5] = {0.08, 0.06, 0.60, 0.68, 0.02};
const double MID_WEIGHTS[5] = {0.13, 0.15, 0.45, 0.51, 0.07};
const double LATE_WEIGHTS[5] = {0.11, 0.15, 0.38, 0.45, 0.10};

inline const double* get_phase_weights(int turn) {
    if (turn <= 10) return EARLY_WEIGHTS;
    else if (turn <= 20) return MID_WEIGHTS;
    else return LATE_WEIGHTS;
}

// Multi-component evaluation function
inline double evaluate_position(const Board& board, int root_player, int turn_number) {
    double my_qt, my_kt, my_qp, my_kp;
    double opp_qt, opp_kt, opp_qp, opp_kp;
    
    bfs_evaluate(board, root_player, my_qt, my_kt, my_qp, my_kp);
    bfs_evaluate(board, 1 - root_player, opp_qt, opp_kt, opp_qp, opp_kp);
    
    double queen_territory = my_qt - opp_qt;
    double king_territory = my_kt - opp_kt;
    double queen_position = my_qp - opp_qp;
    double king_position = my_kp - opp_kp;
    
    int my_mobility = calc_mobility(board, root_player);
    int opp_mobility = calc_mobility(board, 1 - root_player);
    double mobility = my_mobility - opp_mobility;
    
    const double* weights = get_phase_weights(turn_number);
    
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

// --- MOVE ORDERING ---

// Score a move for ordering (centrality + arrow proximity to opponent)
int score_move(const Move& move, const Board& board, int color) {
    int score = CENTRALITY[move.dest];  // Centrality of destination
    
    // Arrow closeness to opponent queens
    int ax, ay;
    idx_to_coord(move.arrow, ax, ay);
    
    uint64_t opp_queens = board.queens[1 - color];
    int min_dist = 99;
    while (opp_queens) {
        int qidx = lsb_index(opp_queens);
        int qx, qy;
        idx_to_coord(qidx, qx, qy);
        int dist = max(abs(ax - qx), abs(ay - qy));
        if (dist < min_dist) min_dist = dist;
        opp_queens = clear_lsb(opp_queens);
    }
    
    // Favor arrows close to opponent queens
    if (min_dist <= 6) {
        score += (6 - min_dist);
    }
    
    return score;
}

// Sort moves by score (descending)
void order_moves(vector<Move>& moves, const Board& board, int color) {
    for (size_t i = 0; i < moves.size(); i++) {
        moves[i].score = score_move(moves[i], board, color);
    }
    sort(moves.begin(), moves.end(), [](const Move& a, const Move& b) {
        return a.score > b.score;
    });
}

// --- NODE POOL ALLOCATOR ---

class NodePool {
    vector<char> memory;
    size_t offset;
    
public:
    NodePool() : offset(0) {
        memory.reserve(10000000);  // Reserve 10MB (reduced from 50MB)
    }
    
    void* allocate(size_t size) {
        if (offset + size > memory.size()) {
            size_t new_size = max(memory.size() * 2, offset + size);
            memory.resize(new_size);
        }
        void* ptr = &memory[offset];
        offset += size;
        return ptr;
    }
    
    void reset() {
        offset = 0;
    }
    
    size_t get_usage() const {
        return offset;
    }
};

// --- MCTS NODE ---

struct MCTSNode {
    MCTSNode* parent;
    vector<MCTSNode*> children;
    Move move;
    double wins;
    int visits;
    vector<Move> untried_moves;
    int player_just_moved;
    
    MCTSNode(MCTSNode* p, const Move& m, int pjm) 
        : parent(p), move(m), wins(0.0), visits(0), player_just_moved(pjm) {
        children.reserve(50);
    }
    
    MCTSNode* uct_select_child(double C) {
        double log_visits = log(static_cast<double>(visits));
        double best_score = -1e9;
        MCTSNode* best_child = nullptr;
        
        for (size_t i = 0; i < children.size(); i++) {
            MCTSNode* c = children[i];
            double exploit = c->wins / c->visits;
            double explore = C * sqrt(log_visits / c->visits);
            double score = exploit + explore;
            if (score > best_score) {
                best_score = score;
                best_child = c;
            }
        }
        return best_child;
    }
};

// Placement new for pool allocation
template<typename... Args>
MCTSNode* pool_new_node(NodePool& pool, Args&&... args) {
    void* p = pool.allocate(sizeof(MCTSNode));
    return new (p) MCTSNode(forward<Args>(args)...);
}

// --- MCTS ALGORITHM ---

inline double get_ucb_constant(int turn) {
    return 0.177 * exp(-0.008 * (turn - 1.41));
}

class MCTS {
public:
    NodePool pool;
    MCTSNode* root;
    int turn_number;
    double time_limit;
    
    MCTS(double tl = 0.9) : root(nullptr), turn_number(0), time_limit(tl) {}
    
    ~MCTS() {
        // Pool handles memory
    }
    
    Move search(const Board& root_state, int root_player) {
        if (root == nullptr) {
            root = pool_new_node(pool, nullptr, Move(), 1 - root_player);
            generate_moves(root_state, root_player, root->untried_moves);
            order_moves(root->untried_moves, root_state, root_player);
        }
        
        auto start_time = chrono::steady_clock::now();
        double C = get_ucb_constant(turn_number);
        int iterations = 0;
        
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
                apply_move(state, node->move, 1 - node->player_just_moved);
                current_player = 1 - current_player;
            }
            
            // Expansion
            if (!node->untried_moves.empty()) {
                int idx = xorshift64() % node->untried_moves.size();
                Move m = node->untried_moves[idx];
                
                apply_move(state, m, current_player);
                current_player = 1 - current_player;
                
                MCTSNode* new_node = pool_new_node(pool, node, m, 1 - current_player);
                generate_moves(state, current_player, new_node->untried_moves);
                // Skip move ordering for child nodes (too expensive)
                
                node->untried_moves.erase(node->untried_moves.begin() + idx);
                node->children.push_back(new_node);
                node = new_node;
            }
            
            // Evaluation
            double win_prob = evaluate_position(state, root_player, turn_number);
            
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
            return Move(-1, -1, -1);
        }
        
        // Select best move by visit count
        MCTSNode* best_node = nullptr;
        int max_visits = -1;
        for (size_t i = 0; i < root->children.size(); i++) {
            if (root->children[i]->visits > max_visits) {
                max_visits = root->children[i]->visits;
                best_node = root->children[i];
            }
        }
        
        return best_node->move;
    }
    
    void advance_root(const Move& move) {
        if (root == nullptr) return;
        
        MCTSNode* new_root = nullptr;
        
        // Defensive: Check children vector is valid
        if (!root->children.empty()) {
            for (size_t i = 0; i < root->children.size(); i++) {
                // Defensive: Null check each child
                if (root->children[i] != nullptr && root->children[i]->move == move) {
                    new_root = root->children[i];
                    break;
                }
            }
        }
        
        if (new_root != nullptr) {
            new_root->parent = nullptr;
            root = new_root;
            // Keep old tree in pool (can't reset without destroying kept subtree)
        } else {
            root = nullptr;
            // Start fresh if move not found
            pool.reset();
        }
    }
};

// --- MAIN I/O ---

const double TIME_LIMIT = 0.8;  // Conservative: 0.8s (vs 1s limit)
const double FIRST_TURN_TIME_LIMIT = 1.6;  // Conservative: 1.6s (vs 2s limit)

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    
    Board board;
    int my_color = 0;
    MCTS ai(TIME_LIMIT);
    
    // Initialize PRNG
    init_xorshift(chrono::steady_clock::now().time_since_epoch().count());
    
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
    
    // Replay moves with proper color tracking
    int current_color = (first_req[0] == -1) ? BLACK : WHITE;  // First move color
    
    for (size_t i = 0; i < lines.size(); i++) {
        const string& line_str = lines[i];
        istringstream iss2(line_str);
        vector<int> coords;
        int v;
        while (iss2 >> v) coords.push_back(v);
        
        // Skip invalid moves
        if (coords.size() < 6 || coords[0] == -1) {
            current_color = 1 - current_color;  // Still alternate
            continue;
        }
        
        // Convert from (x,y) coordinates to bitboard indices
        int src_idx = coord_to_idx(coords[0], coords[1]);
        int dest_idx = coord_to_idx(coords[2], coords[3]);
        int arrow_idx = coord_to_idx(coords[4], coords[5]);
        Move m(src_idx, dest_idx, arrow_idx);
        
        // Apply move with current color
        apply_move(board, m, current_color);
        ai.advance_root(m);
        
        // Alternate for next move
        current_color = 1 - current_color;
    }
    
    // Set turn number
    ai.turn_number = turn_id;
    
    double limit = (turn_id == 1) ? FIRST_TURN_TIME_LIMIT : TIME_LIMIT;
    ai.time_limit = limit;
    
    Move best_move = ai.search(board, my_color);
    
    if (best_move.src != -1) {
        int sx, sy, dx, dy, ax, ay;
        idx_to_coord(best_move.src, sx, sy);
        idx_to_coord(best_move.dest, dx, dy);
        idx_to_coord(best_move.arrow, ax, ay);
        
        cout << sx << " " << sy << " " << dx << " " << dy << " " << ax << " " << ay << endl;
        apply_move(board, best_move, my_color);
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
                    // Validate coordinates are in bounds
                    bool valid = true;
                    for (int coord : parts) {
                        if (coord < 0 || coord >= 8) {
                            valid = false;
                            break;
                        }
                    }
                    
                    if (valid) {
                        int src_idx = coord_to_idx(parts[0], parts[1]);
                        int dest_idx = coord_to_idx(parts[2], parts[3]);
                        int arrow_idx = coord_to_idx(parts[4], parts[5]);
                        opponent_move = Move(src_idx, dest_idx, arrow_idx);
                        found = true;
                        break;
                    }
                } else if (parts.size() == 1) {
                    continue;
                } else {
                    continue;
                }
            }
            
            if (found) {
                apply_move(board, opponent_move, 1 - my_color);
                ai.advance_root(opponent_move);
            }
            
            ai.turn_number++;
            ai.time_limit = TIME_LIMIT;
            
            best_move = ai.search(board, my_color);
            
            if (best_move.src != -1) {
                int sx, sy, dx, dy, ax, ay;
                idx_to_coord(best_move.src, sx, sy);
                idx_to_coord(best_move.dest, dx, dy);
                idx_to_coord(best_move.arrow, ax, ay);
                
                cout << sx << " " << sy << " " << dx << " " << dy << " " << ax << " " << ay << endl;
                apply_move(board, best_move, my_color);
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
