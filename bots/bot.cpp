#include <iostream>
#include <vector>
#include <array>
#include <cstdlib>
#include <ctime>
#include <sstream>

using namespace std;

// --- GAME CONSTANTS ---
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
};

// --- BOARD CLASS ---
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
        // Black pieces (top side)
        grid[0][2] = BLACK;
        grid[2][0] = BLACK;
        grid[5][0] = BLACK;
        grid[7][2] = BLACK;
        // White pieces (bottom side)
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
};

// --- MAIN FUNCTION ---
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    
    // Seed random number generator
    srand(time(0));
    
    Board board;
    string line;
    
    // Read turn number
    if (!getline(cin, line)) return 0;
    
    int turn_id;
    try {
        turn_id = stoi(line);
    } catch (...) {
        return 0;
    }
    
    // Read all move history (2*turn_id - 1 lines)
    vector<string> lines;
    int count = 2 * turn_id - 1;
    for (int i = 0; i < count; i++) {
        string l;
        if (!getline(cin, l)) return 0;
        lines.push_back(l);
    }
    
    // Determine bot color
    int my_color = 0;
    istringstream iss(lines[0]);
    vector<int> first_req;
    int val;
    while (iss >> val) first_req.push_back(val);
    
    if (first_req[0] == -1) {
        my_color = BLACK;  // Bot is black (first player)
    } else {
        my_color = WHITE;  // Bot is white (second player)
    }
    
    // Replay all moves to reconstruct board state
    for (const string& line_str : lines) {
        istringstream iss2(line_str);
        vector<int> coords;
        int v;
        while (iss2 >> v) coords.push_back(v);
        
        if (coords[0] == -1) continue;  // Skip first move placeholder
        
        Move m(coords[0], coords[1], coords[2], coords[3], coords[4], coords[5]);
        board.apply_move(m);
    }
    
    // Generate all legal moves for current player
    vector<Move> legal_moves = board.get_legal_moves(my_color);
    
    // Select random move
    Move best_move(-1, -1, -1, -1, -1, -1);
    if (!legal_moves.empty()) {
        int random_index = rand() % legal_moves.size();
        best_move = legal_moves[random_index];
    }
    
    // Output the move (or -1 -1 -1 -1 -1 -1 if no moves)
    cout << best_move.x0 << " " << best_move.y0 << " " 
         << best_move.x1 << " " << best_move.y1 << " "
         << best_move.x2 << " " << best_move.y2 << endl;
    
    // Non-long-live mode: exit immediately after output
    return 0;
}