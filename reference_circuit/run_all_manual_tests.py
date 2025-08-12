#!/usr/bin/env python3
"""
Run all manual tests in sequence
"""

import subprocess
import sys
from pathlib import Path

def run_test(script_name):
    """Run a test script and capture output."""
    print(f"\n{'='*60}")
    print(f"🧪 Running {script_name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([
            sys.executable, script_name
        ], capture_output=True, text=True, timeout=30)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"❌ {script_name} timed out")
        return False
    except Exception as e:
        print(f"❌ {script_name} failed: {e}")
        return False

def main():
    print("🚀 Running All Manual Tests")
    print("="*60)
    
    tests = [
        "manual_test_1_blank.py",
        "manual_test_2_add_resistor.py", 
        "manual_test_3_add_second_resistor.py",
        "manual_test_4_remove_resistor.py",
        "manual_test_5_compare_reference.py"
    ]
    
    results = []
    
    for test in tests:
        if Path(test).exists():
            success = run_test(test)
            results.append((test, success))
        else:
            print(f"❌ Test file not found: {test}")
            results.append((test, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 ALL TESTS SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    for test, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test}")
        if success:
            passed += 1
    
    print(f"\n📈 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All manual tests passed!")
    else:
        print("⚠️  Some tests failed - check output above")

if __name__ == "__main__":
    main()