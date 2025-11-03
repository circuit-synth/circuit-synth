#!/usr/bin/env python3
"""
Circuit-Synth Agent Dashboard

Displays real-time status of active autonomous agents.
"""

import sys
import time
from pathlib import Path

# Add adw_modules to path
sys.path.insert(0, str(Path(__file__).parent / "adw_modules"))

from dashboard_data import get_active_agents_table

# Configuration
REPO_ROOT = Path(__file__).parent.parent
TREES_DIR = REPO_ROOT / "trees"


def main():
    """Main dashboard loop"""
    print("Circuit-Synth Agent Dashboard")
    print("Press Ctrl+C to exit\n")

    try:
        while True:
            # Clear screen (works on Unix/Linux/Mac)
            print("\033[2J\033[H", end="")

            # Display header
            print("Circuit-Synth Autonomous Worker Dashboard")
            print(f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()

            # Display active agents table
            table = get_active_agents_table(TREES_DIR)
            print(table)
            print()
            print("Refreshing every 5 seconds... (Ctrl+C to exit)")

            # Wait before refresh
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n\nDashboard stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
