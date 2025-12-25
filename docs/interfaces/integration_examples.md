# Integration Examples and Code Patterns

## Overview

This document provides practical code examples and integration patterns for incorporating Amazing Amazons AI bots into GUI applications. Examples are provided in multiple languages with language-agnostic pseudocode where appropriate.

## Core Integration Patterns

### Pattern 1: Subprocess Execution (Recommended)

The most robust and flexible approach is to execute bots as subprocesses, following the Botzone protocol.

#### Python Implementation

```python
import subprocess
import select
import time
from typing import Optional, List, Tuple

class BotProcess:
    """Manages bot process lifecycle and communication"""
    
    def __init__(self, bot_path: str, time_limit: float = 5.0):
        self.bot_path = bot_path
        self.time_limit = time_limit
        self.process = None
        self.is_keep_running = False
        
    def start(self):
        """Start the bot process"""
        self.process = subprocess.Popen(
            [self.bot_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        self.is_keep_running = False
        
    def stop(self):
        """Stop the bot process"""
        if self.process:
            try:
                self.process.kill()
                self.process.wait(timeout=1)
            except:
                pass
            self.process = None
            
    def read_line_with_timeout(self, timeout: float) -> Optional[str]:
        """Read a line from stdout with timeout"""
        if not self.process:
            return None
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            ready, _, _ = select.select([self.process.stdout], [], [], 0.1)
            if ready:
                line = self.process.stdout.readline()
                if line:
                    return line.strip()
        return None
        
    def play_first_turn(self, is_black: bool, move_history: List[str]) -> Optional[str]:
        """Play first turn with complete move history"""
        if not self.process:
            self.start()
            
        try:
            # Send turn ID = 1
            self.process.stdin.write("1\n")
            
            # Send move history
            for move in move_history:
                self.process.stdin.write(f"{move}\n")
                
            self.process.stdin.flush()
            
            # Read move with timeout
            move = self.read_line_with_timeout(self.time_limit)
            if not move:
                return None
                
            # Read keep-running signal
            keep = self.read_line_with_timeout(0.5)
            if keep == ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<":
                self.is_keep_running = True
                
            return move
            
        except Exception as e:
            print(f"Error in first turn: {e}")
            return None
            
    def play_turn(self, opponent_move: str) -> Optional[str]:
        """Play a turn in keep-running mode"""
        if not self.process or not self.is_keep_running:
            return None
            
        try:
            # Send opponent's move
            self.process.stdin.write(f"{opponent_move}\n")
            self.process.stdin.flush()
            
            # Read move with timeout
            move = self.read_line_with_timeout(self.time_limit)
            if not move:
                return None
                
            # Read keep-running signal
            keep = self.read_line_with_timeout(0.5)
            if keep != ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<":
                print(f"Warning: keep-running mismatch: {keep}")
                
            return move
            
        except Exception as e:
            print(f"Error in turn: {e}")
            return None

# Usage example
def play_game_with_bot():
    """Example of playing a complete game with a bot"""
    bot = BotProcess("bots/bot001_cpp", time_limit=3.0)
    
    # Game state
    moves = []
    current_player = "black"
    
    # First turn (Black)
    print("Turn 1: Black's move...")
    move = bot.play_first_turn(is_black=True, move_history=["-1 -1 -1 -1 -1 -1"])
    if move:
        print(f"  Bot move: {move}")
        moves.append(move)
        current_player = "white"
    else:
        print("  Bot failed first turn")
        return
        
    # Game loop
    turn = 2
    while True:
        # In real GUI, here you would:
        # 1. Display board
        # 2. Get human move
        # 3. Validate move
        # 4. Apply move to game state
        
        # For this example, we'll simulate human move
        if current_player == "white":
            # Human's turn (simulated)
            # In real GUI, wait for human input
            human_move = get_human_move_from_gui()  # Placeholder
            moves.append(human_move)
            current_player = "black"
            
            # Bot's turn
            print(f"Turn {turn}: Black's move...")
            move = bot.play_turn(human_move)
            if move:
                print(f"  Bot move: {move}")
                moves.append(move)
                current_player = "white"
            else:
                print("  Bot failed")
                break
                
        turn += 1
        
    bot.stop()
```

#### C++ Implementation

```cpp
#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <cstdio>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/select.h>

class BotProcess {
private:
    std::string botPath;
    double timeLimit;
    pid_t pid;
    int stdinPipe[2];
    int stdoutPipe[2];
    bool isKeepRunning;
    
public:
    BotProcess(const std::string& path, double limit = 5.0) 
        : botPath(path), timeLimit(limit), pid(-1), isKeepRunning(false) {
        pipe(stdinPipe);
        pipe(stdoutPipe);
    }
    
    ~BotProcess() {
        stop();
    }
    
    bool start() {
        pid = fork();
        if (pid == 0) {
            // Child process
            close(stdinPipe[1]);  // Close write end of stdin
            close(stdoutPipe[0]); // Close read end of stdout
            
            dup2(stdinPipe[0], STDIN_FILENO);
            dup2(stdoutPipe[1], STDOUT_FILENO);
            
            execl(botPath.c_str(), botPath.c_str(), nullptr);
            exit(1);  // exec failed
        } else if (pid > 0) {
            // Parent process
            close(stdinPipe[0]);  // Close read end of stdin
            close(stdoutPipe[1]); // Close write end of stdout
            return true;
        }
        return false;
    }
    
    void stop() {
        if (pid > 0) {
            kill(pid, SIGTERM);
            waitpid(pid, nullptr, 0);
            pid = -1;
        }
    }
    
    std::string readLineWithTimeout(double timeout) {
        fd_set readfds;
        struct timeval tv;
        
        FD_ZERO(&readfds);
        FD_SET(stdoutPipe[0], &readfds);
        
        tv.tv_sec = static_cast<int>(timeout);
        tv.tv_usec = static_cast<int>((timeout - tv.tv_sec) * 1000000);
        
        int ret = select(stdoutPipe[0] + 1, &readfds, nullptr, nullptr, &tv);
        if (ret > 0) {
            std::string line;
            char ch;
            while (read(stdoutPipe[0], &ch, 1) > 0 && ch != '\n') {
                line += ch;
            }
            return line;
        }
        return "";  // Timeout
    }
    
    bool writeLine(const std::string& line) {
        std::string data = line + "\n";
        return write(stdinPipe[1], data.c_str(), data.size()) == data.size();
    }
    
    std::string playFirstTurn(bool isBlack, const std::vector<std::string>& moveHistory) {
        if (pid <= 0 && !start()) {
            return "";
        }
        
        // Send turn ID
        writeLine("1");
        
        // Send move history
        for (const auto& move : moveHistory) {
            writeLine(move);
        }
        
        // Read move
        std::string move = readLineWithTimeout(timeLimit);
        if (move.empty()) {
            return "";
        }
        
        // Read keep-running signal
        std::string keep = readLineWithTimeout(0.5);
        if (keep == ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<") {
            isKeepRunning = true;
        }
        
        return move;
    }
    
    std::string playTurn(const std::string& opponentMove) {
        if (pid <= 0 || !isKeepRunning) {
            return "";
        }
        
        // Send opponent's move
        writeLine(opponentMove);
        
        // Read move
        std::string move = readLineWithTimeout(timeLimit);
        if (move.empty()) {
            return "";
        }
        
        // Read keep-running signal
        std::string keep = readLineWithTimeout(0.5);
        if (keep != ">>>BOTZONE_REQUEST_KEEP_RUNNING<<<") {
            std::cerr << "Warning: keep-running mismatch: " << keep << std::endl;
        }
        
        return move;
    }
};

// Usage example
int main() {
    BotProcess bot("bots/bot001_cpp", 3.0);
    
    // First turn
    std::vector<std::string> history = {"-1 -1 -1 -1 -1 -1"};
    std::string move = bot.playFirstTurn(true, history);
    
    if (!move.empty()) {
        std::cout << "Bot move: " << move << std::endl;
        
        // Game loop would continue here
        // In GUI, you would:
        // 1. Display board with bot's move
        // 2. Get human move from GUI
        // 3. Send to bot: bot.playTurn(humanMove)
        // 4. Repeat
    }
    
    return 0;
}
```

#### JavaScript/TypeScript Implementation (Node.js)

```typescript
import { spawn, ChildProcess } from 'child_process';
import { Readable, Writable } from 'stream';

interface BotOptions {
    timeLimit: number;
    workingDirectory?: string;
}

class BotProcess {
    private process: ChildProcess | null = null;
    private isKeepRunning: boolean = false;
    private stdoutBuffer: string = '';
    
    constructor(
        private botPath: string,
        private options: BotOptions = { timeLimit: 5000 }
    ) {}
    
    async start(): Promise<void> {
        return new Promise((resolve, reject) => {
            this.process = spawn(this.botPath, [], {
                cwd: this.options.workingDirectory,
                stdio: ['pipe', 'pipe', 'pipe']
            });
            
            // Buffer stdout data
            this.process.stdout?.on('data', (data: Buffer) => {
                this.stdoutBuffer += data.toString();
            });
            
            this.process.on('error', reject);
            this.process.on('spawn', resolve);
        });
    }
    
    async stop(): Promise<void> {
        if (this.process) {
            this.process.kill();
            this.process = null;
            this.isKeepRunning = false;
        }
    }
    
    private async readLine(timeout: number): Promise<string | null> {
        return new Promise((resolve) => {
            const startTime = Date.now();
            
            const checkBuffer = () => {
                const newlineIndex = this.stdoutBuffer.indexOf('\n');
                if (newlineIndex !== -1) {
                    const line = this.stdoutBuffer.substring(0, newlineIndex).trim();
                    this.stdoutBuffer = this.stdoutBuffer.substring(newlineIndex + 1);
                    resolve(line);
                } else if (Date.now() - startTime > timeout) {
                    resolve(null); // Timeout
                } else {
                    setTimeout(checkBuffer, 10);
                }
            };
            
            checkBuffer();
        });
    }
    
    private writeLine(line: string): void {
        if (this.process?.stdin?.writable) {
            this.process.stdin.write(line + '\n');
        }
    }
    
    async playFirstTurn(isBlack: boolean, moveHistory: string[]): Promise<string | null> {
        if (!this.process) {
            await this.start();
        }
        
        try {
            // Send turn ID
            this.writeLine('1');
            
            // Send move history
            for (const move of moveHistory) {
                this.writeLine(move);
            }
            
            // Read move
            const move = await this.readLine(this.options.timeLimit);
            if (!move) {
                return null;
            }
            
            // Read keep-running signal
            const keep = await this.readLine(500);
            if (keep === '>>>BOTZONE_REQUEST_KEEP_RUNNING<<<') {
                this.isKeepRunning = true;
            }
            
            return move;
        } catch (error) {
            console.error('Error in first turn:', error);
            return null;
        }
    }
    
    async playTurn(opponentMove: string): Promise<string | null> {
        if (!this.process || !this.isKeepRunning) {
            return null;
        }
        
        try {
            // Send opponent's move
            this.writeLine(opponentMove);
            
            // Read move
            const move = await this.readLine(this.options.timeLimit);
            if (!move) {
                return null;
            }
            
            // Read keep-running signal
            const keep = await this.readLine(500);
            if (keep !== '>>>BOTZONE_REQUEST_KEEP_RUNNING<<<') {
                console.warn(`Warning: keep-running mismatch: ${keep}`);
            }
            
            return move;
        } catch (error) {
            console.error('Error in turn:', error);
            return null;
        }
    }
}

// Usage example
async function playGame() {
    const bot = new BotProcess('./bots/bot001_cpp', { timeLimit: 3000 });
    
    try {
        // First turn
        const move = await bot.playFirstTurn(true, ['-1 -1 -1 -1 -1 -1']);
        if (move) {
            console.log(`Bot move: ${move}`);
            
            // Game loop would continue here
            // In Electron/Web GUI, you would:
            // 1. Update UI with bot's move
            // 2. Wait for human move via UI events
            // 3. Send to bot: await bot.playTurn(humanMove)
            // 4. Repeat
        }
    } finally {
        await bot.stop();
    }
}
```

### Pattern 2: Library Integration (C++ Bots Only)

For tighter integration with C++ GUI applications, you can link bots as libraries.

#### C++ Library Interface

```cpp
// bot_interface.h - Common interface for all bots
#ifndef BOT_INTERFACE_H
#define BOT_INTERFACE_H

#include <vector>
#include <string>
#include <memory>

namespace amazons {

// Move representation
struct Move {
    int x0, y0;  // Start position
    int x1, y1;  // End position  
    int x2, y2;  // Arrow position
    
    Move(int x0 = -1, int y0 = -1, int x1 = -1, int y1 = -1, int x2 = -1, int y2 = -1)
        : x0(x0), y0(y0), x1(x1), y1(y1), x2(x2), y2(y2) {}
    
    std::string toString() const {
        return std::to_string(x0) + " " + std::to_string(y0) + " " +
               std::to_string(x1) + " " + std::to_string(y1) + " " +
               std::to_string(x2) + " " + std::to_string(y2);
    }
    
    bool isValid() const {
        return x0 != -1;  // Simple validity check
    }
};

// Game state representation
class GameState {
public:
    virtual ~GameState() = default;
    
    virtual void applyMove(const Move& move) = 0;
    virtual std::vector<Move> getLegalMoves(int color) const = 0;
    virtual bool isGameOver() const = 0;
    virtual int getCurrentPlayer() const = 0;
    virtual std::unique_ptr<GameState> copy() const = 0;
};

// Bot interface
class Bot {
public:
    virtual ~Bot() = default;
    
    virtual Move getMove(const GameState& state, int color, double timeLimit) = 0;
    virtual void reset() = 0;
    virtual std::string getName() const = 0;
    virtual std::string getVersion() const = 0;
};

// Bot factory
std::unique_ptr<Bot> createBot(const std::string& name);

} // namespace amazons

### Pattern 3: Service/DAemon Architecture

For distributed systems or web-based GUIs, run bots as services:

#### REST API Service (Python/Flask)

```python
from flask import Flask, request, jsonify
import subprocess
import threading
import time

app = Flask(__name__)

class BotManager:
    def __init__(self):
        self.bots = {}  # session_id -> bot_process
        
    def create_bot(self, session_id, bot_type="bot001"):
        if session_id in self.bots:
            return False
            
        if bot_type == "bot001":
            bot_path = "bots/bot001_cpp"
        elif bot_type == "bot002":
            bot_path = "bots/bot002_cpp"
        else:
            return False
            
        self.bots[session_id] = {
            'process': None,
            'type': bot_type,
            'last_activity': time.time()
        }
        return True
        
    def get_move(self, session_id, move_history, time_limit=3.0):
        if session_id not in self.bots:
            return None
            
        bot_info = self.bots[session_id]
        
        # Execute bot and get move
        # Implementation similar to BotProcess class above
        # ...
        
        bot_info['last_activity'] = time.time()
        return move
        
    def cleanup_old_sessions(self, timeout=3600):
        current_time = time.time()
        to_remove = []
        for session_id, info in self.bots.items():
            if current_time - info['last_activity'] > timeout:
                to_remove.append(session_id)
                
        for session_id in to_remove:
            self.remove_bot(session_id)

bot_manager = BotManager()

@app.route('/api/bot/create', methods=['POST'])
def create_bot():
    data = request.json
    session_id = data.get('session_id')
    bot_type = data.get('bot_type', 'bot001')
    
    if bot_manager.create_bot(session_id, bot_type):
        return jsonify({'status': 'success', 'session_id': session_id})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to create bot'}), 400

@app.route('/api/bot/move', methods=['POST'])
def get_bot_move():
    data = request.json
    session_id = data.get('session_id')
    move_history = data.get('move_history', [])
    time_limit = data.get('time_limit', 3.0)
    
    move = bot_manager.get_move(session_id, move_history, time_limit)
    if move:
        return jsonify({'status': 'success', 'move': move})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to get move'}), 400

@app.route('/api/bot/cleanup', methods=['POST'])
def cleanup():
    bot_manager.cleanup_old_sessions()
    return jsonify({'status': 'success', 'cleaned': True})

if __name__ == '__main__':
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()
    
    app.run(host='0.0.0.0', port=5000)
```

#### WebSocket Service (Real-time)

```python
import asyncio
import websockets
import json
from bot_manager import BotManager

bot_manager = BotManager()

async def handle_connection(websocket, path):
    session_id = None
    
    try:
        async for message in websockets:
            data = json.loads(message)
            command = data.get('command')
            
            if command == 'create':
                session_id = data['session_id']
                bot_type = data.get('bot_type', 'bot001')
                success = bot_manager.create_bot(session_id, bot_type)
                await websocket.send(json.dumps({
                    'type': 'create_response',
                    'success': success,
                    'session_id': session_id
                }))
                
            elif command == 'get_move':
                if not session_id:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'No active session'
                    }))
                    continue
                    
                move_history = data['move_history']
                time_limit = data.get('time_limit', 3.0)
                
                move = bot_manager.get_move(session_id, move_history, time_limit)
                await websocket.send(json.dumps({
                    'type': 'move_response',
                    'move': move,
                    'session_id': session_id
                }))
                
            elif command == 'close':
                if session_id:
                    bot_manager.remove_bot(session_id)
                break
                
    except websockets.exceptions.ConnectionClosed:
        if session_id:
            bot_manager.remove_bot(session_id)

async def main():
    async with websockets.serve(handle_connection, "localhost", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
```

## Error Handling Patterns

### Robust Bot Wrapper

```python
class RobustBot:
    """Bot wrapper with comprehensive error handling"""
    
    def __init__(self, bot_path, max_retries=3, fallback_bot=None):
        self.bot_path = bot_path
        self.max_retries = max_retries
        self.fallback_bot = fallback_bot
        self.stats = {
            'successes': 0,
            'failures': 0,
            'retries': 0,
            'timeouts': 0
        }
        
    def get_move_with_retry(self, move_history, time_limit):
        """Get move with automatic retry on failure"""
        
        for attempt in range(self.max_retries):
            try:
                move = self._get_move_single(move_history, time_limit)
                if move:
                    self.stats['successes'] += 1
                    return move
                    
            except TimeoutError:
                self.stats['timeouts'] += 1
                if attempt == self.max_retries - 1:
                    break
                    
            except Exception as e:
                self.stats['failures'] += 1
                log_error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    break
                    
            self.stats['retries'] += 1
            
        # All retries failed, use fallback
        if self.fallback_bot:
            return self.fallback_bot.get_move(move_history, time_limit)
            
        return None  # Or return random legal move
        
    def _get_move_single(self, move_history, time_limit):
        """Single attempt to get move"""
        # Implementation using BotProcess
        pass
```

### State Synchronization

```python
class StateSynchronizedBot:
    """Bot that maintains synchronized game state"""
    
    def __init__(self, bot_path):
        self.bot = BotProcess(bot_path)
        self.expected_state = None
        self.move_history = []
        
    def get_move(self, current_state, color, time_limit):
        """Get move with state synchronization"""
        
        # Check if state matches expected state
        if self.expected_state and not states_equal(current_state, self.expected_state):
            # State mismatch - resynchronize
            self._resynchronize(current_state)
            
        # Get move from bot
        move = self.bot.play_turn(self.move_history)
        if not move:
            return None
            
        # Update expected state
        self.expected_state = apply_move_to_state(current_state, move)
        self.move_history.append(move)
        
        return move
        
    def _resynchronize(self, current_state):
        """Resynchronize bot with current game state"""
        self.bot.stop()
        self.bot.start()
        
        # Replay all moves to current state
        # This requires tracking full game history
        for move in self.move_history:
            # Send move to bot to rebuild its internal state
            pass
            
        self.expected_state = current_state
```

## Performance Optimization

### Bot Pool for High Concurrency

```python
class BotPool:
    """Pool of bot processes for handling multiple games"""
    
    def __init__(self, bot_path, pool_size=5):
        self.bot_path = bot_path
        self.pool_size = pool_size
        self.available = []  # Available bot processes
        self.in_use = {}     # session_id -> bot process
        self.lock = threading.Lock()
        
        # Initialize pool
        for _ in range(pool_size):
            bot = BotProcess(bot_path)
            bot.start()
            self.available.append(bot)
            
    def acquire(self, session_id):
        """Acquire a bot for a session"""
        with self.lock:
            if not self.available:
                return None
                
            bot = self.available.pop()
            self.in_use[session_id] = bot
            return bot
            
    def release(self, session_id):
        """Release bot back to pool"""
        with self.lock:
            if session_id in self.in_use:
                bot = self.in_use.pop(session_id)
                bot.reset()  # Reset bot state
                self.available.append(bot)
                
    def get_move(self, session_id, move_history, time_limit):
        """Get move using pooled bot"""
        bot = self.acquire(session_id)
        if not bot:
            return None
            
        try:
            move = bot.get_move(move_history, time_limit)
            return move
        finally:
            self.release(session_id)
```

### Caching Frequently Used Positions

```python
class CachingBot:
    """Bot with move caching for common positions"""
    
    def __init__(self, bot_path, cache_size=1000):
        self.bot = BotProcess(bot_path)
        self.cache = {}  # position_hash -> move
        self.cache_size = cache_size
        self.access_order = []  # LRU tracking
        
    def get_move(self, game_state, color, time_limit):
        """Get move with caching"""
        
        # Generate position hash
        position_hash = self._hash_position(game_state, color)
        
        # Check cache
        if position_hash in self.cache:
            # Update LRU
            self.access_order.remove(position_hash)
            self.access_order.append(position_hash)
            return self.cache[position_hash]
            
        # Get move from bot
        move = self.bot.get_move(game_state, color, time_limit)
        if not move:
            return None
            
        # Cache result
        if len(self.cache) >= self.cache_size:
            # Remove least recently used
            lru = self.access_order.pop(0)
            del self.cache[lru]
            
        self.cache[position_hash] = move
        self.access_order.append(position_hash)
        
        return move
        
    def _hash_position(self, game_state, color):
        """Generate hash for game position"""
        # Simple hash implementation
        # In practice, use Zobrist hashing or similar
        return hash(str(game_state) + str(color))
```

## Testing and Validation

### Integration Test Suite

```python
import unittest

class BotIntegrationTests(unittest.TestCase):
    
    def setUp(self):
        self.bot = BotProcess("bots/bot001_cpp")
        
    def test_first_turn_black(self):
        """Test Black's first turn"""
        move = self.bot.play_first_turn(
            is_black=True,
            move_history=["-1 -1 -1 -1 -1 -1"]
        )
        self.assertIsNotNone(move)
        self.assertTrue(self._is_valid_move_format(move))
        
    def test_first_turn_white(self):
        """Test White's first turn after Black move"""
        move = self.bot.play_first_turn(
            is_black=False,
            move_history=["2 0 3 1 4 2"]  # Example Black move
        )
        self.assertIsNotNone(move)
        self.assertTrue(self._is_valid_move_format(move))
        
    def test_subsequent_turn(self):
        """Test subsequent turn in keep-running mode"""
        # First turn
        self.bot.play_first_turn(
            is_black=True,
            move_history=["-1 -1 -1 -1 -1 -1"]
        )
        
        # Subsequent turn
        move = self.bot.play_turn("0 5 1 4 2 3")  # Example White move
        self.assertIsNotNone(move)
        self.assertTrue(self._is_valid_move_format(move))
        
    def test_timeout_handling(self):
        """Test timeout handling"""
        bot = BotProcess("bots/bot001_cpp", time_limit=0.01)  # Very short timeout
        move = bot.play_first_turn(
            is_black=True,
            move_history=["-1 -1 -1 -1 -1 -1"]
        )
        self.assertIsNone(move)  # Should timeout
        
    def _is_valid_move_format(self, move_str):
        """Validate move format"""
        parts = move_str.split()
        if len(parts) != 6:
            return False
            
        try:
            coords = list(map(int, parts))
            # Check bounds
            for coord in coords:
                if coord < -1 or coord > 7:
                    return False
            return True
        except ValueError:
            return False

if __name__ == '__main__':
    unittest.main()
```

## Best Practices Summary

### For All Integrations
1. **Always validate bot moves** against game rules
2. **Implement timeouts** at multiple levels
3. **Monitor bot process health**
4. **Log all interactions** for debugging
5. **Handle failures gracefully** with fallbacks
6. **Test thoroughly** with the tournament system

### For Performance-Critical Applications
1. **Use C++ bots** for maximum speed
2. **Implement connection pooling** for multiple games
3. **Cache frequently used positions**
4. **Monitor resource usage** (CPU, memory)
5. **Consider pre-warming** bot processes

### For Web/Network Applications
1. **Use service architecture** for scalability
2. **Implement session management**
3. **Add rate limiting** to prevent abuse
4. **Use secure communication** (HTTPS, WSS)
5. **Implement proper error responses**

## References

- [Bot Integration Interface](bot_integration_interface.md) - Protocol specification
- [Bot Selection Guide](bot_selection_guide.md) - Bot characteristics and selection
- [Tournament System](../manuals/tournament_system_manual.md) - Testing framework
- [Bot Implementations](../bots/) - Source code and documentation

---

*Last Updated: 2025-12-25*

#endif // BOT_INTERFACE_H
```

#### Bot001 Implementation Wrapper

```cpp
// bot001_wrapper.cpp - Wrapper for bot001.cpp
#include "bot_interface.h"
#include <vector>
#include <sstream>
#include <cstring>

// Forward declaration of bot001 internal functions
extern "C" {
    void* bot001_create();
    void bot001_destroy(void* bot);
    const char* bot001_get_move(void* bot, const char* input);
    void bot001_reset(void* bot);
}

namespace amazons {

class Bot001 : public Bot {
private:
    void* botImpl;
    
public:
    Bot001() : botImpl(bot001_create()) {}
    
    ~Bot001() override {
        if (botImpl) {
            bot001_destroy(botImpl);
        }
    }
    
    Move getMove(const GameState& state, int color, double timeLimit) override {
        // Convert game state to Botzone input format
        std::stringstream input;
        
        // Build move history from game state
        // This is simplified - actual implementation would track move history
        input << "1\n";  // turn_id
        
        if (color == 1) {  // Black
            input << "-1 -1 -1 -1 -1 -1\n";
        } else {  // White
            // For White's first turn, we need Black's move
            // This is simplified - actual implementation would need game history
            input << "2 0 3 1 4 2\n";  // Example Black move
        }
        
        // Call bot001 internal function
        const char* output = bot001_get_move(botImpl, input.str().c_str());
        if (!output) {
            return Move();  // Invalid move
        }
        
        // Parse output
        std::stringstream ss(output);
        Move move;
        ss >> move.x0 >> move.y0 >> move.x1 >> move.y1 >> move.x2 >> move.y2;
        
        return move;
    }
    
    void reset() override {
        bot001_reset(botImpl);
    }
    
    std::string getName() const override {
        return "bot001";
    }
    
    std::string getVersion() const override {
        return "1.0";
    }
};

// Bot factory implementation
std::unique_ptr<Bot> createBot(const std::string& name) {
    if (name == "bot001") {
        return std::make_unique<Bot001>();
    }
    // Add other bots here
    return nullptr;
}

} // namespace amazons