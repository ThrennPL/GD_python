#!/usr/bin/env python3
"""
Main entry point for GD_python application.
Reorganized project structure - main application code is in src/ folder.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main application
if __name__ == "__main__":
    from main import main
    main()