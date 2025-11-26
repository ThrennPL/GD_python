#!/usr/bin/env python3
"""
Streamlit entry point for GD_python application.
This file serves as a proper entry point that redirects to src/streamlit_app.py
"""

import sys
import os

# Add src directory to Python path
current_dir = os.path.dirname(__file__)
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Execute the src/streamlit_app.py content directly
src_app_path = os.path.join(src_dir, 'streamlit_app.py')

# Read and execute the source file in the current namespace
with open(src_app_path, 'r', encoding='utf-8') as f:
    exec(f.read())


