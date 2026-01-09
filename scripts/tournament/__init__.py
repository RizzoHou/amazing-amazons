"""
Tournament system for Amazons bot matches.

This package provides:
- GameEngine: Run games between two bots
- ResourceMonitor: Track time and memory usage
- GameAnalyzer: Analyze game results and generate reports
- Bot runners: Support for both long-live and traditional bots
- CLI: Command-line interface for running matches and tournaments

Usage:
    python -m scripts.tournament match bot1 bot2
    python -m scripts.tournament tournament bot1 bot2 bot3
    python -m scripts.tournament match bot1 bot2 --unlimited --analyze
"""

from .resource_monitor import (
    ResourceMonitor,
    TurnMetrics,
    GameMetrics,
    ViolationType,
    format_time,
    format_bytes,
)

from .bot_runner import (
    BaseBotRunner,
    TraditionalBot,
    LongLiveBot,
    BotType,
    BotResult,
    create_bot_runner,
    detect_bot_type,
)

from .game_engine import (
    GameEngine,
    GameResult,
    GameEndReason,
    FixedGame,  # Legacy compatibility
)

from .game_analyzer import (
    GameAnalyzer,
    TournamentStats,
    print_game_analysis,
)

from .cli import (
    run_match,
    run_tournament,
    run_test,
    main,
)

__all__ = [
    # Resource monitoring
    'ResourceMonitor',
    'TurnMetrics',
    'GameMetrics',
    'ViolationType',
    'format_time',
    'format_bytes',
    
    # Bot runners
    'BaseBotRunner',
    'TraditionalBot',
    'LongLiveBot',
    'BotType',
    'BotResult',
    'create_bot_runner',
    'detect_bot_type',
    
    # Game engine
    'GameEngine',
    'GameResult',
    'GameEndReason',
    'FixedGame',
    
    # Analysis
    'GameAnalyzer',
    'TournamentStats',
    'print_game_analysis',
    
    # CLI
    'run_match',
    'run_tournament',
    'run_test',
    'main',
]
