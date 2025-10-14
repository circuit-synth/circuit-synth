#!/usr/bin/env python3
"""
Comprehensive Regression Test Suite for Circuit-Synth
======================================================

This script performs FULL environment reconstruction and testing:
- Reinstalls all Python dependencies from scratch
- Runs comprehensive test suite
- Validates generated outputs

CRITICAL: Run this before ANY PyPI release to ensure code integrity.

Usage:
    ./tools/testing/run_full_regression_tests.py [options]

Options:
    --skip-install     Skip reinstallation (for debugging)
    --keep-outputs     Don't delete generated test files
    --verbose         Show detailed output
    --quick           Skip slow tests (NOT for releases)
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ANSI color codes for terminal output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class TestResult:
    """Container for individual test results"""

    def __init__(self, name: str, category: str, severity: str = "MEDIUM"):
        self.name = name
        self.category = category
        self.severity = severity  # CRITICAL, HIGH, MEDIUM, LOW
        self.passed = False
        self.error = None
        self.output = ""
        self.duration = 0.0
        self.details = {}


class ComprehensiveRegressionSuite:
    """Full regression test suite with complete environment rebuild"""

    def __init__(self, project_root: Path, args: argparse.Namespace):
        self.project_root = project_root
        self.args = args
        self.example_dir = project_root / "example_project" / "circuit-synth"
        self.results: List[TestResult] = []
        self.start_time = None
        self.environment_info = {}

        # Test output directory
        self.test_output_dir = project_root / "test_outputs"
        if self.test_output_dir.exists() and not args.keep_outputs:
            shutil.rmtree(self.test_output_dir)
        self.test_output_dir.mkdir(exist_ok=True)

    def log(self, message: str, level: str = "INFO", indent: int = 0):
        """Enhanced logging with colors and indentation"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        indent_str = "  " * indent

        # Color mapping
        color_map = {
            "HEADER": Colors.HEADER + Colors.BOLD,
            "INFO": Colors.CYAN,
            "SUCCESS": Colors.GREEN,
            "WARNING": Colors.WARNING,
            "ERROR": Colors.FAIL,
            "DETAIL": Colors.BLUE,
        }

        color = color_map.get(level, "")

        # Emoji mapping
        emoji_map = {
            "HEADER": "🚀",
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "WARNING": "⚠️ ",
            "ERROR": "❌",
            "DETAIL": "📝",
        }

        emoji = emoji_map.get(level, "")

        print(f"{color}[{timestamp}] {emoji} {indent_str}{message}{Colors.ENDC}")

        # Also log to file
        log_file = self.test_output_dir / "regression_test.log"
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] [{level}] {indent_str}{message}\n")

    def run_command(
        self,
        cmd: List[str],
        description: str,
        cwd: Optional[Path] = None,
        timeout: int = 300,
        check: bool = True,
    ) -> Tuple[bool, str, str]:
        """Run a shell command and return success, stdout, stderr"""
        if self.args.verbose:
            self.log(f"Running: {' '.join(cmd)}", "DETAIL", 1)

        try:
            process = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=check,
            )

            if self.args.verbose and process.stdout:
                self.log("Output:", "DETAIL", 2)
                for line in process.stdout.split("\n")[:10]:  # First 10 lines
                    if line.strip():
                        self.log(line.strip(), "DETAIL", 3)

            return process.returncode == 0, process.stdout, process.stderr

        except subprocess.TimeoutExpired:
            self.log(f"Command timed out after {timeout}s: {description}", "ERROR")
            return False, "", f"Timeout after {timeout} seconds"

        except subprocess.CalledProcessError as e:
            if self.args.verbose:
                self.log(f"Command failed: {e.stderr}", "ERROR", 2)
            return False, e.stdout or "", e.stderr or str(e)

        except Exception as e:
            self.log(f"Unexpected error: {str(e)}", "ERROR")
            return False, "", str(e)

    # ========== PART 2: Environment Management ==========

    def capture_environment(self):
        """Capture current environment state for debugging"""
        self.log("Capturing environment information...", "INFO")

        env_info = {
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "platform": sys.platform,
            "cwd": os.getcwd(),
            "project_root": str(self.project_root),
        }

        # Check Python version
        success, stdout, _ = self.run_command(
            ["python3", "--version"], "Python version", check=False
        )
        if success:
            env_info["python3_version"] = stdout.strip()

        # Check uv version
        success, stdout, _ = self.run_command(
            ["uv", "--version"], "uv version", check=False
        )
        if success:
            env_info["uv_version"] = stdout.strip()
        else:
            self.log("uv not found - will try to install", "WARNING")

        # Cargo no longer needed - pure Python project

        # Check KiCad installation
        success, stdout, _ = self.run_command(
            ["kicad-cli", "version"], "KiCad version", check=False
        )
        if success:
            env_info["kicad_version"] = stdout.strip()
        else:
            self.log("KiCad not found - some tests may fail", "WARNING")

        self.environment_info = env_info

        # Save to file
        env_file = self.test_output_dir / "environment.json"
        with open(env_file, "w") as f:
            json.dump(env_info, f, indent=2)

        self.log(f"Environment info saved to {env_file}", "SUCCESS")

    def clear_all_caches(self) -> bool:
        self.log("=" * 60, "HEADER")
        self.log("CLEARING ALL CACHES", "HEADER")
        self.log("=" * 60, "HEADER")

        caches_cleared = []
        caches_failed = []

        # 1. Python caches
        python_caches = [
            Path.home() / ".cache" / "circuit_synth",
            Path.home() / ".circuit-synth",
            Path.home() / ".cache" / "pip",
            Path.home() / ".cache" / "uv",
            self.project_root / ".venv",
            self.project_root / "build",
            self.project_root / "dist",
            self.project_root / "*.egg-info",
        ]

        for cache_path in python_caches:
            if "*" in str(cache_path):
                # Handle glob patterns
                for path in self.project_root.glob(cache_path.name):
                    if path.exists():
                        try:
                            shutil.rmtree(path)
                            caches_cleared.append(str(path))
                            self.log(f"Cleared: {path}", "SUCCESS", 1)
                        except Exception as e:
                            caches_failed.append((str(path), str(e)))
                            self.log(f"Failed to clear {path}: {e}", "WARNING", 1)
            elif cache_path.exists():
                try:
                    if cache_path.is_dir():
                        shutil.rmtree(cache_path)
                    else:
                        cache_path.unlink()
                    caches_cleared.append(str(cache_path))
                    self.log(f"Cleared: {cache_path}", "SUCCESS", 1)
                except Exception as e:
                    caches_failed.append((str(cache_path), str(e)))
                    self.log(f"Failed to clear {cache_path}: {e}", "WARNING", 1)

        # 2. Python bytecode
        self.log("Clearing Python bytecode...", "INFO")
        pycache_count = 0
        for pycache in self.project_root.rglob("__pycache__"):
            if pycache.is_dir():
                try:
                    shutil.rmtree(pycache)
                    pycache_count += 1
                except:
                    pass

        for pyc in self.project_root.rglob("*.pyc"):
            if pyc.is_file():
                try:
                    pyc.unlink()
                    pycache_count += 1
                except:
                    pass

        if pycache_count > 0:
            self.log(
                f"Cleared {pycache_count} bytecode files/directories", "SUCCESS", 1
            )

        # 4. Test outputs from previous runs
        test_artifacts = [
            self.example_dir / "ESP32_C6_Dev_Board",
            self.example_dir / "*.json",
            self.example_dir / "*.net",
            self.example_dir / "round_trip_generated.py",
            self.project_root / "test_*.py",
            self.project_root / "*_test.py",
            self.project_root / "*_generated",
            self.project_root / "*_Dev_Board",
        ]

        self.log("Clearing test artifacts...", "INFO")
        for artifact_pattern in test_artifacts:
            if "*" in str(artifact_pattern):
                parent = artifact_pattern.parent
                pattern = artifact_pattern.name
                for artifact in parent.glob(pattern):
                    if artifact.exists():
                        try:
                            if artifact.is_dir():
                                shutil.rmtree(artifact)
                            else:
                                artifact.unlink()
                            caches_cleared.append(str(artifact))
                            self.log(f"Cleared: {artifact}", "SUCCESS", 1)
                        except Exception as e:
                            caches_failed.append((str(artifact), str(e)))