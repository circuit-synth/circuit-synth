#!/usr/bin/env python3
"""
Master test runner for all functional tests
Runs automated tests and provides instructions for manual tests
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

class FunctionalTestRunner:
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.automated_tests = []
        self.manual_tests = []
        self.results = []
        
    def discover_tests(self):
        """Discover all test directories"""
        for test_path in sorted(self.test_dir.glob("test_*")):
            if test_path.is_dir():
                # Check if it has an automated test script
                test_script = test_path / "test_script.py"
                manual_steps = test_path / "MANUAL_STEPS.md"
                
                if test_script.exists():
                    self.automated_tests.append((test_path.name, test_script))
                elif manual_steps.exists():
                    self.manual_tests.append((test_path.name, manual_steps))
                    
    def run_automated_test(self, test_name: str, test_script: Path) -> bool:
        """Run a single automated test"""
        print(f"\n{'='*60}")
        print(f"Running {test_name}")
        print('='*60)
        
        try:
            result = subprocess.run(
                [sys.executable, str(test_script)],
                capture_output=True,
                text=True,
                cwd=test_script.parent
            )
            
            if result.returncode == 0:
                print(f"✅ {test_name} PASSED")
                self.results.append((test_name, "PASSED", None))
                return True
            else:
                print(f"❌ {test_name} FAILED")
                print(f"Error output:\n{result.stderr}")
                self.results.append((test_name, "FAILED", result.stderr))
                return False
                
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            self.results.append((test_name, "ERROR", str(e)))
            return False
            
    def show_manual_test_info(self, test_name: str, manual_steps: Path):
        """Display information about manual test"""
        print(f"\n📋 {test_name} - Manual Test")
        print(f"   Instructions: {manual_steps}")
        
    def run_all_tests(self):
        """Run all discovered tests"""
        print("Circuit Synth Functional Test Suite")
        print("="*60)
        
        self.discover_tests()
        
        print(f"\nDiscovered {len(self.automated_tests)} automated tests")
        print(f"Discovered {len(self.manual_tests)} manual tests")
        
        # Run automated tests
        if self.automated_tests:
            print("\n" + "="*60)
            print("AUTOMATED TESTS")
            print("="*60)
            
            passed = 0
            for test_name, test_script in self.automated_tests:
                if self.run_automated_test(test_name, test_script):
                    passed += 1
                    
            print(f"\n{'='*60}")
            print(f"Automated Tests Summary: {passed}/{len(self.automated_tests)} passed")
            
        # Show manual tests
        if self.manual_tests:
            print("\n" + "="*60)
            print("MANUAL TESTS")
            print("="*60)
            print("\nThe following tests require manual interaction with KiCad:")
            
            for test_name, manual_steps in self.manual_tests:
                self.show_manual_test_info(test_name, manual_steps)
                
        # Final summary
        self.print_summary()
        
    def print_summary(self):
        """Print final test summary"""
        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)
        
        if self.results:
            print("\nAutomated Test Results:")
            for test_name, status, error in self.results:
                status_symbol = "✅" if status == "PASSED" else "❌"
                print(f"  {status_symbol} {test_name}: {status}")
                
        print(f"\nManual Tests: {len(self.manual_tests)} tests require manual execution")
        
        # List manual test directories
        if self.manual_tests:
            print("\nTo run manual tests, navigate to each directory and follow MANUAL_STEPS.md:")
            for test_name, _ in self.manual_tests:
                print(f"  - {test_name}/")
                
        print("\n" + "="*60)
        
        # Return exit code based on automated test results
        if self.results:
            failed = sum(1 for _, status, _ in self.results if status != "PASSED")
            return 1 if failed > 0 else 0
        return 0

def main():
    """Main entry point"""
    runner = FunctionalTestRunner()
    exit_code = runner.run_all_tests()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()