#!/usr/bin/env python3
"""
Quick launcher script for the Vitruvian Cipher CLI.
Can be run directly without installation.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent_cli.main import main

if __name__ == "__main__":
    main()
