#!/usr/bin/env python3
"""
End-to-End Project Creation Test

This test specifically validates the complete cs-new-project workflow
to catch issues like workspace configuration errors that prevent new
projects from running properly.

This test should have caught the 0.8.22 template bug where:
- cs-new-project creates project with workspace configuration
- User runs 'uv run python circuit-synth/main.py'
- Fails with "circuit-synth references a workspace but is not a workspace member"
"""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


def test_cs_new_project_end_to_end():
    """
    Test the complete cs-new-project workflow including execution.
    
    This test validates:
    1. cs-new-project creates a working project
    2. Generated pyproject.toml is valid
    3. 'uv run python circuit-synth/main.py' works
    4. Circuit generation completes successfully
    """
    print("🧪 Testing cs-new-project end-to-end workflow...")
    
    # Create temporary directory for test project
    with tempfile.TemporaryDirectory() as temp_dir:
        test_project_dir = Path(temp_dir) / "test_cs_project"
        
        print(f"📁 Creating test project in: {test_project_dir}")
        
        # Step 1: Initialize project
        try:
            result = subprocess.run([
                "uv", "init", "test_cs_project"
            ], cwd=temp_dir, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise Exception(f"uv init failed: {result.stderr}")
                
            print("✅ Project initialized with uv")
        except Exception as e:
            print(f"❌ Failed to initialize project: {e}")
            return False
            
        # Step 2: Add circuit-synth dependency
        try:
            result = subprocess.run([
                "uv", "add", "circuit-synth"
            ], cwd=test_project_dir, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise Exception(f"uv add circuit-synth failed: {result.stderr}")
                
            print("✅ circuit-synth dependency added")
        except Exception as e:
            print(f"❌ Failed to add circuit-synth: {e}")
            return False
            
        # Step 3: Run cs-new-project
        try:
            result = subprocess.run([
                "uv", "run", "cs-new-project"
            ], cwd=test_project_dir, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise Exception(f"cs-new-project failed: {result.stderr}")
                
            print("✅ cs-new-project completed successfully")
        except Exception as e:
            print(f"❌ cs-new-project failed: {e}")
            return False
            
        # Step 4: Validate generated pyproject.toml
        try:
            pyproject_path = test_project_dir / "pyproject.toml"
            if not pyproject_path.exists():
                raise Exception("pyproject.toml not generated")
                
            content = pyproject_path.read_text()
            
            # Check for problematic workspace configuration
            if "workspace = true" in content:
                raise Exception("❌ CRITICAL: Template still contains workspace = true configuration!")
                
            # Check for required dependencies
            if "circuit-synth" not in content:
                raise Exception("circuit-synth dependency missing")
                
            print("✅ Generated pyproject.toml is valid")
        except Exception as e:
            print(f"❌ pyproject.toml validation failed: {e}")
            return False
            
        # Step 5: Test circuit execution - THE CRITICAL TEST
        try:
            circuit_main = test_project_dir / "circuit-synth" / "main.py"
            if not circuit_main.exists():
                raise Exception("circuit-synth/main.py not generated")
                
            print("🔬 Testing circuit execution (CRITICAL TEST)...")
            result = subprocess.run([
                "uv", "run", "python", "circuit-synth/main.py"
            ], cwd=test_project_dir, capture_output=True, text=True, timeout=180)
            
            if result.returncode != 0:
                print(f"❌ CRITICAL FAILURE: Circuit execution failed!")
                print(f"   Error: {result.stderr}")
                print(f"   Output: {result.stdout}")
                raise Exception(f"Circuit execution failed: {result.stderr}")
                
            print("✅ Circuit execution completed successfully")
            
            # Verify KiCad files were generated
            kicad_dir = test_project_dir / "ESP32_C6_Dev_Board"
            if not kicad_dir.exists():
                raise Exception("KiCad project directory not created")
                
            required_files = [
                "ESP32_C6_Dev_Board.kicad_pro",
                "ESP32_C6_Dev_Board.kicad_sch", 
                "ESP32_C6_Dev_Board.kicad_pcb"
            ]
            
            for filename in required_files:
                file_path = kicad_dir / filename
                if not file_path.exists():
                    raise Exception(f"Required KiCad file missing: {filename}")
                if file_path.stat().st_size < 100:  # Files should have content
                    raise Exception(f"KiCad file too small (likely empty): {filename}")
                    
            print("✅ All KiCad files generated with content")
            
        except Exception as e:
            print(f"❌ CRITICAL: Circuit execution test failed: {e}")
            return False
            
        # Step 6: Test CLI commands work
        try:
            # Test cs-setup-kicad-plugins
            result = subprocess.run([
                "uv", "run", "cs-setup-kicad-plugins", "--help"
            ], cwd=test_project_dir, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                print(f"⚠️ cs-setup-kicad-plugins help failed: {result.stderr}")
            else:
                print("✅ cs-setup-kicad-plugins accessible")
                
        except Exception as e:
            print(f"⚠️ CLI command test failed: {e}")
            # Don't fail the test for this
            
    print("🎉 End-to-end project creation test PASSED")
    return True


def analyze_testing_gap():
    """
    Analyze why our existing tests didn't catch the workspace configuration bug.
    """
    print("\n🔍 ANALYSIS: Why did our tests miss this bug?")
    print("=" * 60)
    
    gaps = [
        {
            "gap": "No end-to-end cs-new-project testing",
            "impact": "CRITICAL",
            "description": "Regression tests didn't actually run cs-new-project command"
        },
        {
            "gap": "No template validation in CI",
            "impact": "HIGH", 
            "description": "Project templates aren't validated for correct syntax"
        },
        {
            "gap": "No user workflow simulation",
            "impact": "HIGH",
            "description": "Tests don't simulate actual user installation → project creation → execution"
        },
        {
            "gap": "Limited pyproject.toml validation",
            "impact": "MEDIUM",
            "description": "Only basic syntax checking, not semantic validation"
        }
    ]
    
    for i, gap in enumerate(gaps, 1):
        print(f"{i}. {gap['gap']} ({gap['impact']} impact)")
        print(f"   → {gap['description']}")
        
    print("\n🔧 RECOMMENDED FIXES:")
    print("1. Add test_cs_new_project_end_to_end() to regression suite")
    print("2. Add template validation step to release process")
    print("3. Create user simulation tests that mirror real workflows")
    print("4. Add pyproject.toml semantic validation")


def create_enhanced_regression_test():
    """
    Create enhanced test that would catch this type of bug.
    """
    test_additions = """
# ADD TO run_full_regression_tests.py:

def test_cs_new_project_workflow(self) -> TestResult:
    '''Test complete cs-new-project workflow including execution'''
    test = TestResult("cs-new-project workflow", "CLI", "CRITICAL")
    
    try:
        # This test creates a fresh project and tries to run it
        # exactly as users would - catching workspace configuration bugs
        success = test_cs_new_project_end_to_end()
        test.passed = success
        
        if not success:
            test.error = "End-to-end project creation workflow failed"
            
    except Exception as e:
        test.error = str(e)
        
    return test

# ADD TO CLI section of regression tests:
self.results.append(self.test_cs_new_project_workflow())
"""
    
    return test_additions


if __name__ == "__main__":
    print("🚀 End-to-End Project Creation Test")
    print("=" * 50)
    
    # Run the test
    success = test_cs_new_project_end_to_end()
    
    if success:
        print("\n✅ Test PASSED - Project creation workflow works correctly")
    else:
        print("\n❌ Test FAILED - Issues found in project creation")
        
    # Analyze the testing gap
    analyze_testing_gap()
    
    # Show enhanced test code
    print("\n📝 Enhanced regression test code:")
    print(create_enhanced_regression_test())
    
    exit(0 if success else 1)