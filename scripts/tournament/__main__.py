#!/usr/bin/env python
"""
Entry point for running the tournament system as a module.

Usage:
    python -m scripts.tournament match bot1 bot2
    python -m scripts.tournament tournament bot1 bot2 bot3
    python -m scripts.tournament match bot1 bot2 --unlimited --analyze
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
