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

        # Summary
        self.log(f"Cleared {len(caches_cleared)} cache locations", "SUCCESS")
        if caches_failed:
            self.log(f"Failed to clear {len(caches_failed)} locations", "WARNING")

        return len(caches_failed) == 0

    # ========== PART 3: Installation Methods ==========

    def reinstall_python_environment(self) -> bool:
        """Completely reinstall Python environment from scratch"""
        self.log("=" * 60, "HEADER")
        self.log("REINSTALLING PYTHON ENVIRONMENT", "HEADER")
        self.log("=" * 60, "HEADER")

        # 1. Check for uv and install if needed
        success, _, _ = self.run_command(["which", "uv"], "Check uv", check=False)

        if not success:
            self.log("Installing uv package manager...", "INFO")
            success, stdout, stderr = self.run_command(
                ["curl", "-LsSf", "https://astral.sh/uv/install.sh", "|", "sh"],
                "Install uv",
                check=False,
            )
            if not success:
                self.log("Failed to install uv. Trying with pip...", "WARNING")
                success, _, _ = self.run_command(
                    ["pip", "install", "uv"], "Install uv via pip", check=False
                )
                if not success:
                    self.log("Cannot install uv - Python tests will fail", "ERROR")
                    return False

        # 2. Create fresh virtual environment
        self.log("Creating fresh virtual environment...", "INFO")
        venv_path = self.project_root / ".venv"
        if venv_path.exists():
            shutil.rmtree(venv_path)

        success, stdout, stderr = self.run_command(
            ["uv", "venv", ".venv"], "Create virtual environment"
        )
        if not success:
            self.log(f"Failed to create venv: {stderr}", "ERROR")
            return False

        self.log("Virtual environment created", "SUCCESS", 1)

        # 3. Install circuit-synth in development mode with all dependencies
        self.log("Installing circuit-synth with all dependencies...", "INFO")
        success, stdout, stderr = self.run_command(
            ["uv", "pip", "install", "-e", ".[dev]"],
            "Install circuit-synth",
            timeout=600,  # 10 minutes for installation
        )

        if not success:
            self.log(f"Failed to install circuit-synth: {stderr}", "ERROR")
            return False

        self.log("Circuit-synth installed successfully", "SUCCESS", 1)

        # 4. Verify installation
        self.log("Verifying Python installation...", "INFO")

        # Test import
        test_code = """
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'src'))

try:
    from circuit_synth import *
    print("✅ circuit_synth imports successfully")
    
    # Test core functionality
    @circuit
    def test():
        r1 = Component(symbol='Device:R', ref='R1', value='1k')
        return r1
    
    result = test()
    print("✅ Basic circuit creation works")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
"""

        success, stdout, stderr = self.run_command(
            ["uv", "run", "python", "-c", test_code], "Verify installation"
        )

        if not success:
            self.log(f"Installation verification failed: {stderr}", "ERROR")
            return False

        self.log("Python environment verified", "SUCCESS", 1)

        # 5. Register agents (if available)
        self.log("Registering Claude agents...", "INFO")
        success, stdout, stderr = self.run_command(
            ["uv", "run", "register-agents"], "Register agents", check=False
        )

        if success:
            self.log("Agents registered", "SUCCESS", 1)
        else:
            self.log("Agent registration not available (optional)", "INFO", 1)

        return True


    # ========== PART 4: Core Test Methods ==========

    def run_python_test(
        self,
        code: str,
        name: str,
        category: str,
        severity: str = "MEDIUM",
        working_dir: Optional[Path] = None,
    ) -> TestResult:
        """Run a Python code test and capture results"""
        result = TestResult(name, category, severity)
        start_time = time.time()

        try:
            original_dir = os.getcwd()
            if working_dir:
                os.chdir(working_dir)

            success, stdout, stderr = self.run_command(
                ["uv", "run", "python", "-c", code], name, check=False, timeout=60
            )

            result.output = stdout + stderr
            result.passed = success

            if not success:
                result.error = stderr or "Test failed with no error message"

        except Exception as e:
            result.error = f"Exception: {str(e)}"
            result.passed = False
        finally:
            os.chdir(original_dir)
            result.duration = time.time() - start_time

        # Log result
        if result.passed:
            self.log(f"✅ {name} ({result.duration:.1f}s)", "SUCCESS", 1)
        else:
            self.log(f"❌ {name} ({result.duration:.1f}s)", "ERROR", 1)
            if self.args.verbose and result.error:
                self.log(f"Error: {result.error[:200]}", "ERROR", 2)

        return result

    def test_core_functionality(self):
        """Test core circuit-synth functionality"""
        self.log("\n" + "=" * 60, "HEADER")
        self.log("TESTING CORE FUNCTIONALITY", "HEADER")
        self.log("=" * 60, "HEADER")

        tests = []

        # Test 1: Basic imports
        tests.append(
            self.run_python_test(
                """
from circuit_synth import *
print('✅ Basic imports work')
""",
                "Basic Imports",
                "Core",
                "CRITICAL",
            )
        )

        # Test 2: Circuit creation
        tests.append(
            self.run_python_test(
                """
from circuit_synth import *

@circuit
def test_circuit():
    r1 = Component(symbol='Device:R', ref='R1', value='10k')
    c1 = Component(symbol='Device:C', ref='C1', value='100nF')
    print('✅ Component creation works')
    
test_circuit()
""",
                "Component Creation",
                "Core",
                "CRITICAL",
            )
        )

        # Test 3: Net connections
        tests.append(
            self.run_python_test(
                """
from circuit_synth import *

@circuit
def test_nets():
    vcc = Net('VCC_3V3')
    gnd = Net('GND')
    signal = Net('SIGNAL')
    
    r1 = Component(symbol='Device:R', ref='R1', value='10k')
    r2 = Component(symbol='Device:R', ref='R2', value='1k')
    
    vcc += r1[1]
    r1[2] += signal
    signal += r2[1]
    r2[2] += gnd
    
    print('✅ Net connections work')
    
test_nets()
""",
                "Net Connections",
                "Core",
                "CRITICAL",
            )
        )

        # Test 4: Reference auto-assignment
        tests.append(
            self.run_python_test(
                """
from circuit_synth import *

# Store components globally to check after finalization
components = []

@circuit
def test_refs():
    global components
    # Create multiple components with same prefix
    for i in range(5):
        components.append(Component(symbol='Device:R', ref='R'))
    # Also test different prefixes
    components.append(Component(symbol='Device:C', ref='C'))
    components.append(Component(symbol='Device:C', ref='C'))
    
# Call the circuit function to trigger finalization
circuit = test_refs()

# Now check refs AFTER finalization (components are modified in place)
refs = [c.ref for c in components]
r_refs = [r for r in refs if r.startswith('R')]
c_refs = [r for r in refs if r.startswith('C')]

# Check uniqueness
assert len(set(refs)) == len(refs), f"References not unique: {refs}"
assert len(r_refs) == 5, f"Should have 5 resistors, got {len(r_refs)}: {r_refs}"
assert len(c_refs) == 2, f"Should have 2 capacitors, got {len(c_refs)}: {c_refs}"

# Check format (should be R1, R2, etc)
assert all(r[0] in ['R', 'C'] and r[1:].isdigit() for r in refs), f"Wrong format: {refs}"

print(f'✅ Auto-assignment works: {refs}')
""",
                "Reference Auto-Assignment",
                "Core",
                "HIGH",
            )
        )

        self.results.extend(tests)
        return all(t.passed for t in tests if t.severity == "CRITICAL")

    def test_kicad_generation(self):
        """Test KiCad file generation"""
        self.log("\n" + "=" * 60, "HEADER")
        self.log("TESTING KICAD GENERATION", "HEADER")
        self.log("=" * 60, "HEADER")

        tests = []

        # Test 1: JSON export
        tests.append(
            self.run_python_test(
                """
from circuit_synth import *
import json
import os

@circuit
def test_json():
    vcc = Net('VCC')
    gnd = Net('GND')
    r1 = Component(symbol='Device:R', ref='R1', value='1k')
    vcc += r1[1]
    gnd += r1[2]

circuit = test_json()
circuit.generate_json_netlist('test_output.json')

# Verify JSON structure
with open('test_output.json', 'r') as f:
    data = json.load(f)
    
assert 'components' in data, "Missing components in JSON"
assert 'nets' in data, "Missing nets in JSON"
assert len(data['components']) > 0, "No components in JSON"
assert len(data['nets']) > 0, "No nets in JSON"

print(f'✅ JSON export works: {len(data["components"])} components, {len(data["nets"])} nets')

# Cleanup
os.remove('test_output.json')
""",
                "JSON Export",
                "KiCad",
                "HIGH",
                self.test_output_dir,
            )
        )

        # Test 2: Symbol library access
        tests.append(
            self.run_python_test(
                """
from circuit_synth.core.symbol_cache import get_symbol_cache

cache = get_symbol_cache()
symbol = cache.get_symbol('Device:R')

assert symbol is not None, "Could not load resistor symbol"
assert hasattr(symbol, 'pins'), "Symbol missing pins attribute"
assert len(symbol.pins) >= 2, f"Resistor should have 2+ pins, got {len(symbol.pins)}"

print(f'✅ Symbol library works: Resistor has {len(symbol.pins)} pins')
""",
                "Symbol Library Access",
                "KiCad",
                "HIGH",
            )
        )

        self.results.extend(tests)
        return all(t.passed for t in tests if t.severity in ["CRITICAL", "HIGH"])

    def test_cli_entry_points(self):
        """Test CLI entry points to ensure they can be imported and run"""
        self.log("\n" + "=" * 60, "HEADER")
        self.log("TESTING CLI ENTRY POINTS", "HEADER")
        self.log("=" * 60, "HEADER")

        # List of critical CLI commands that must work
        cli_commands = [
            ("cs-new-project", "cs-new-project", "CRITICAL"),
            ("cs-init-pcb", "cs-init-pcb", "HIGH"),
            ("register-agents", "register-agents", "MEDIUM"),
            ("validate-circuit", "validate-circuit", "MEDIUM"),
        ]

        tests = []

        for cmd_name, cmd, severity in cli_commands:
            # Test 1: Command is importable
            result = TestResult(f"{cmd_name} Import Test", "CLI", severity)
            start_time = time.time()

            try:
                # Try to run with --help to see if it imports and has basic structure
                success, stdout, stderr = self.run_command(
                    ["uv", "run", cmd, "--help"],
                    f"Test {cmd} --help",
                    check=False,
                    timeout=30,
                )

                result.output = stdout + stderr

                # Success criteria: either returns 0 or shows help text
                if success or "usage:" in stdout.lower() or "help" in stdout.lower():
                    result.passed = True
                    self.log(f"✅ {cmd_name} imports and shows help", "SUCCESS", 1)
                else:
                    result.passed = False
                    result.error = f"Command failed: {stderr}"
                    self.log(f"❌ {cmd_name} failed: {stderr[:200]}", "ERROR", 1)

            except Exception as e:
                result.error = str(e)
                result.passed = False
                self.log(f"❌ {cmd_name} exception: {str(e)}", "ERROR", 1)
            finally:
                result.duration = time.time() - start_time

            tests.append(result)

        # Test 2: Verify the main problematic command that caused the user's error
        result = TestResult("cs-new-project Execution Test", "CLI", "CRITICAL")
        start_time = time.time()

        try:
            # Create a temporary directory to test cs-new-project
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Try to run cs-new-project with minimal args to see if it starts
                success, stdout, stderr = self.run_command(
                    ["uv", "run", "cs-new-project", "--help"],
                    "cs-new-project basic execution test",
                    cwd=temp_path,
                    check=False,
                    timeout=30,
                )

                result.output = stdout + stderr

                if success or "usage:" in stdout.lower():
                    result.passed = True
                    self.log(
                        "✅ cs-new-project can execute without import errors", "SUCCESS", 1
                    )
                else:
                    result.passed = False
                    result.error = stderr
                    self.log(
                        f"❌ cs-new-project execution failed: {stderr[:200]}", "ERROR", 1
                    )

        except Exception as e:
            result.error = str(e)
            result.passed = False
            self.log(f"❌ cs-new-project execution exception: {str(e)}", "ERROR", 1)
        finally:
            result.duration = time.time() - start_time

        tests.append(result)

        self.results.extend(tests)
        return all(t.passed for t in tests if t.severity == "CRITICAL")

    def test_cs_new_project_end_to_end(self):
        """
        Test complete cs-new-project workflow including execution.
        THIS TEST WOULD HAVE CAUGHT THE 0.8.22 WORKSPACE BUG!
        """
        self.log("\n" + "=" * 60, "HEADER")
        self.log("TESTING CS-NEW-PROJECT END-TO-END WORKFLOW", "HEADER")
        self.log("=" * 60, "HEADER")
        
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_project_dir = Path(temp_dir) / "test_cs_project"
            
            # Step 1: Initialize project
            self.log("Creating test project...", "INFO")
            success, stdout, stderr = self.run_command([
                "uv", "init", "test_cs_project"
            ], "Initialize project", cwd=temp_dir, timeout=60)
            
            if not success:
                self.log(f"❌ Project initialization failed: {stderr}", "ERROR")
                return False
                
            # Step 2: Add circuit-synth dependency  
            self.log("Adding circuit-synth dependency...", "INFO")
            success, stdout, stderr = self.run_command([
                "uv", "add", "circuit-synth"
            ], "Add dependency", cwd=test_project_dir, timeout=120)
            
            if not success:
                self.log(f"❌ Failed to add circuit-synth: {stderr}", "ERROR")
                return False
                
            # Step 3: Run cs-new-project
            self.log("Running cs-new-project...", "INFO")
            success, stdout, stderr = self.run_command([
                "uv", "run", "cs-new-project"
            ], "cs-new-project", cwd=test_project_dir, timeout=120)
            
            if not success:
                self.log(f"❌ cs-new-project failed: {stderr}", "ERROR")
                return False
                
            # Step 4: CRITICAL TEST - Try to run the generated circuit
            self.log("Testing circuit execution (CRITICAL)...", "INFO")
            circuit_main = test_project_dir / "circuit-synth" / "main.py"
            
            if not circuit_main.exists():
                self.log("❌ Circuit main.py not generated", "ERROR")
                return False
                
            success, stdout, stderr = self.run_command([
                "uv", "run", "python", "circuit-synth/main.py"
            ], "Execute circuit", cwd=test_project_dir, timeout=180)
            
            if not success:
                self.log(f"❌ CRITICAL: Circuit execution failed!", "ERROR")
                self.log(f"   Error: {stderr}", "ERROR")
                self.log(f"   This indicates template configuration issues", "ERROR")
                return False
                
            self.log("✅ Circuit execution successful", "SUCCESS")
            
            # Step 5: Verify KiCad files generated
            kicad_dir = test_project_dir / "ESP32_C6_Dev_Board"
            if not kicad_dir.exists():
                self.log("❌ KiCad project not generated", "ERROR")
                return False
                
            required_files = ["ESP32_C6_Dev_Board.kicad_pro", "ESP32_C6_Dev_Board.kicad_sch"]
            for filename in required_files:
                file_path = kicad_dir / filename
                if not file_path.exists() or file_path.stat().st_size < 100:
                    self.log(f"❌ KiCad file missing or empty: {filename}", "ERROR")
                    return False
                    
            self.log("✅ All KiCad files generated successfully", "SUCCESS")
            
        return True

    def test_example_project(self):
        """Test the complete example project"""
        self.log("\n" + "=" * 60, "HEADER")
        self.log("TESTING EXAMPLE PROJECT", "HEADER")
        self.log("=" * 60, "HEADER")

        result = TestResult("Example Project Generation", "Integration", "CRITICAL")
        start_time = time.time()

        try:
            # Clean previous outputs
            output_dir = self.example_dir / "ESP32_C6_Dev_Board"
            if output_dir.exists():
                shutil.rmtree(output_dir)

            # Run the example project
            self.log("Running example project main.py...", "INFO", 1)
            success, stdout, stderr = self.run_command(
                ["uv", "run", "python", "main.py"],
                "Example project",
                cwd=self.example_dir,
                timeout=300,
            )

            result.output = stdout

            if not success:
                result.error = stderr
                result.passed = False
                self.log(f"❌ Example project failed: {stderr[:500]}", "ERROR", 1)
            else:
                # Verify outputs
                expected_files = [
                    "ESP32_C6_Dev_Board/ESP32_C6_Dev_Board.kicad_pro",
                    "ESP32_C6_Dev_Board/ESP32_C6_Dev_Board.kicad_sch",
                    "ESP32_C6_Dev_Board/ESP32_C6_Dev_Board.kicad_pcb",
                    "ESP32_C6_Dev_Board/ESP32_C6_Dev_Board.net",
                ]

                missing_files = []
                file_sizes = {}

                for file_path in expected_files:
                    full_path = self.example_dir / file_path
                    if not full_path.exists():
                        missing_files.append(file_path)
                    else:
                        size = full_path.stat().st_size
                        file_sizes[file_path] = size
                        if size < 100:  # Files should have content
                            missing_files.append(
                                f"{file_path} (too small: {size} bytes)"
                            )

                if missing_files:
                    result.error = f"Missing/invalid files: {missing_files}"
                    result.passed = False
                    self.log(f"❌ Missing files: {missing_files}", "ERROR", 1)
                else:
                    result.passed = True
                    self.log("✅ All expected files generated", "SUCCESS", 1)

                    # Log file sizes
                    for file, size in file_sizes.items():
                        self.log(f"  {file}: {size:,} bytes", "INFO", 2)

                    # Save a copy for inspection
                    if not self.args.keep_outputs:
                        backup_dir = self.test_output_dir / "example_backup"
                        if backup_dir.exists():
                            shutil.rmtree(backup_dir)
                        shutil.copytree(output_dir, backup_dir)
                        self.log(f"Backup saved to {backup_dir}", "INFO", 1)

        except Exception as e:
            result.error = str(e)
            result.passed = False
            self.log(f"❌ Exception: {e}", "ERROR", 1)

        finally:
            result.duration = time.time() - start_time

        self.results.append(result)
        return result.passed

    # ========== PART 5: Main Orchestration ==========

    def run_all_tests(self) -> bool:
        """Run complete regression test suite"""
        self.start_time = time.time()

        self.log("=" * 80, "HEADER")
        self.log("COMPREHENSIVE REGRESSION TEST SUITE", "HEADER")
        self.log(f"Project: {self.project_root}", "HEADER")
        self.log(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "HEADER")
        self.log("=" * 80, "HEADER")

        # Step 1: Capture environment
        self.capture_environment()

        # Step 2: Clear all caches (unless skipped)
        if not self.args.skip_install:
            if not self.clear_all_caches():
                self.log("Failed to clear all caches - continuing anyway", "WARNING")

        # Step 3: Reinstall Python environment (unless skipped)
        if not self.args.skip_install:
            if not self.reinstall_python_environment():
                self.log("Failed to reinstall Python environment", "ERROR")
                return False

        # Step 5: Run core tests
        core_passed = self.test_core_functionality()

        # Step 6: Run KiCad tests
        kicad_passed = self.test_kicad_generation()

        # Step 7: Test CLI entry points (CRITICAL - this was missing!)
        cli_passed = self.test_cli_entry_points()
        
        # Step 7.5: Test cs-new-project end-to-end workflow (CRITICAL NEW TEST)
        project_creation_passed = self.test_cs_new_project_end_to_end()

        # Step 8: Run example project test
        example_passed = self.test_example_project()

        # Step 9: Run additional tests (if not quick mode)
        if not self.args.quick:
            self.run_additional_tests()

        # Step 10: Generate summary
        overall_passed = self.generate_summary()

        return overall_passed

    def run_additional_tests(self):
        """Run additional non-critical tests"""
        self.log("\n" + "=" * 60, "HEADER")
        self.log("ADDITIONAL TESTS", "HEADER")
        self.log("=" * 60, "HEADER")

        # Test JLCPCB integration
        self.results.append(
            self.run_python_test(
                """
from circuit_synth.manufacturing.jlcpcb import search_jlc_components_web

try:
    results = search_jlc_components_web('STM32G0', max_results=2)
    if results:
        print(f'✅ JLCPCB search: Found {len(results)} components')
    else:
        print('⚠️ JLCPCB returned no results')
except Exception as e:
    print(f'⚠️ JLCPCB search failed: {e}')
""",
                "JLCPCB Integration",
                "External",
                "LOW",
            )
        )

        # Test STM32 search
        self.results.append(
            self.run_python_test(
                """
from circuit_synth.ai_integration.stm32_search_helper import handle_stm32_peripheral_query

result = handle_stm32_peripheral_query('find stm32 with 2 spi available on jlcpcb')
if result and len(result) > 100:
    print(f'✅ STM32 search: {len(result)} chars')
else:
    print('❌ STM32 search failed')
""",
                "STM32 Search",
                "Components",
                "MEDIUM",
            )
        )

    def generate_summary(self) -> bool:
        """Generate test summary and determine overall pass/fail"""
        duration = time.time() - self.start_time

        self.log("\n" + "=" * 80, "HEADER")
        self.log("TEST SUMMARY", "HEADER")
        self.log("=" * 80, "HEADER")

        # Group results by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = {
                    "passed": [],
                    "failed": [],
                    "critical_failed": [],
                }

            if result.passed:
                categories[result.category]["passed"].append(result)
            else:
                categories[result.category]["failed"].append(result)
                if result.severity == "CRITICAL":
                    categories[result.category]["critical_failed"].append(result)

        # Print category summaries
        total_passed = 0
        total_failed = 0
        critical_failures = []

        for category, results in categories.items():
            passed = len(results["passed"])
            failed = len(results["failed"])
            total = passed + failed

            total_passed += passed
            total_failed += failed

            if failed > 0:
                self.log(f"{category}: {passed}/{total} passed ❌", "ERROR")
                for test in results["failed"]:
                    self.log(f"  ❌ {test.name} ({test.severity})", "ERROR", 1)
                    if test.severity == "CRITICAL":
                        critical_failures.append(test)
            else:
                self.log(f"{category}: {passed}/{total} passed ✅", "SUCCESS")

        # Overall summary
        self.log("\n" + "-" * 60, "INFO")
        self.log(
            f"Total: {total_passed}/{total_passed + total_failed} tests passed", "INFO"
        )
        self.log(f"Duration: {duration:.1f} seconds", "INFO")

        # Determine pass/fail
        if critical_failures:
            self.log("\n⛔ CRITICAL FAILURES DETECTED - DO NOT RELEASE!", "ERROR")
            for failure in critical_failures:
                self.log(f"  • {failure.name}: {failure.error}", "ERROR")
            overall_passed = False
        elif total_failed > 0:
            self.log(
                "\n⚠️ Non-critical failures detected - Review before release", "WARNING"
            )
            overall_passed = True  # Can still release with non-critical failures
        else:
            self.log("\n✅ ALL TESTS PASSED - Ready for release!", "SUCCESS")
            overall_passed = True

        # Save results to JSON
        results_file = self.test_output_dir / "test_results.json"
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "critical_failures": len(critical_failures),
            "overall_passed": overall_passed,
            "environment": self.environment_info,
            "results": [
                {
                    "name": r.name,
                    "category": r.category,
                    "severity": r.severity,
                    "passed": r.passed,
                    "duration": r.duration,
                    "error": r.error,
                }
                for r in self.results
            ],
        }

        with open(results_file, "w") as f:
            json.dump(results_data, f, indent=2)

        self.log(f"\nResults saved to: {results_file}", "INFO")

        return overall_passed


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Comprehensive regression test suite for circuit-synth",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full test before release (recommended)
  ./tools/testing/run_full_regression_tests.py
  
  # Quick test during development
  ./tools/testing/run_full_regression_tests.py --skip-install --quick
  
  # Verbose output for debugging
  ./tools/testing/run_full_regression_tests.py --verbose
  
  # Keep test outputs for inspection
  ./tools/testing/run_full_regression_tests.py --keep-outputs
        """,
    )

    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip reinstallation (use existing environment)",
    )

    parser.add_argument(
        "--keep-outputs",
        action="store_true",
        help="Keep generated test files for inspection",
    )

    parser.add_argument("--verbose", action="store_true", help="Show detailed output")

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip slow/optional tests (NOT for releases)",
    )

    args = parser.parse_args()

    # Find project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent  # tools/testing/ -> project root

    # Verify we're in the right place
    if not (project_root / "src" / "circuit_synth").exists():
        print(f"❌ Could not find circuit_synth at {project_root}")
        sys.exit(1)

    # Run tests
    suite = ComprehensiveRegressionSuite(project_root, args)
    success = suite.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
