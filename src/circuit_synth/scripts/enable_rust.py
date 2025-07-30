#!/usr/bin/env python3
"""
Entry point for enabling Rust acceleration.
This is a wrapper around the main acceleration script.
"""

import sys
from pathlib import Path


def main():
    """Main entry point for enable-rust-acceleration command."""
    # Import and run the main acceleration script
    script_path = (
        Path(__file__).parent.parent.parent.parent / "enable_rust_acceleration.py"
    )

    if not script_path.exists():
        print("❌ Rust acceleration script not found")
        return 1

    # Execute the acceleration script
    import subprocess

    result = subprocess.run([sys.executable, str(script_path)], cwd=script_path.parent)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
