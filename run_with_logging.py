#!/usr/bin/env python3
"""
Script to run the example project with dead code logging enabled.
"""

import logging
import sys
from pathlib import Path

# Setup dead code analysis logging BEFORE importing circuit-synth
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
dead_code_logger = logging.getLogger('dead_code_analysis')
dead_code_logger.setLevel(logging.INFO)

# Create file handler
log_file = Path(__file__).parent / 'function_usage.log'
handler = logging.FileHandler(log_file, mode='w')  # Overwrite existing log
handler.setFormatter(logging.Formatter('%(message)s'))
dead_code_logger.addHandler(handler)

# Make logger globally available
import builtins
builtins.__dead_code_logger = dead_code_logger

print(f"Function usage logging enabled, writing to: {log_file}")

# Add source path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Now run the example project
example_main = Path(__file__).parent / "example_project" / "circuit-synth" / "main.py"
if example_main.exists():
    print(f"Running example project: {example_main}")
    exec(open(example_main).read())
else:
    print(f"Example project not found at: {example_main}")
    sys.exit(1)