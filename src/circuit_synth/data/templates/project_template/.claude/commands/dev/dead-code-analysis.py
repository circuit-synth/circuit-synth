#!/usr/bin/env python3
"""
Claude Code Command Handler for /dead-code-analysis

This module handles the /dead-code-analysis command in Claude Code.
"""

import subprocess
import sys
from pathlib import Path


def handle_dead_code_analysis_command(args: str = ""):
    """
    Handle the /dead-code-analysis command.
    
    Args:
        args: Command arguments (target script path, optional)
    """
    # Get the repository root and find the scripts directory
    repo_root = Path(__file__).parent.parent.parent  # Go up from .claude/commands/ to repo root
    shell_script = repo_root / "scripts" / "dead-code-analysis.sh"
    
    if not shell_script.exists():
        print(f"❌ Dead code analysis script not found: {shell_script}")
        return False
        
    # Parse arguments
    target_script = args.strip() if args.strip() else "main.py"
    
    try:
        # Run the dead code analysis
        print(f"🔍 Starting dead code analysis with target: {target_script}")
        result = subprocess.run(
            [str(shell_script), target_script],
            check=True,
            text=True
        )
        
        print("✅ Dead code analysis completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Dead code analysis failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Script not found or not executable: {shell_script}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during dead code analysis: {e}")
        return False


if __name__ == "__main__":
    # Allow direct execution for testing
    args = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    handle_dead_code_analysis_command(args)