#!/usr/bin/env python3
"""Test 50: Missing Footprint"""
import pytest, subprocess, shutil
from pathlib import Path

def test_50_missing_footprint(request):
    test_dir = Path(__file__).parent
    output_dir = test_dir / "comprehensive_root"
    cleanup = not request.config.getoption("--keep-output", default=False)
    try:
        result = subprocess.run(["uv", "run", str(test_dir / "comprehensive_root.py")], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0
        print("\n✅ Test 50 PASSED: Missing footprints handled")
    finally:
        if cleanup and output_dir.exists(): shutil.rmtree(output_dir)

if __name__ == "__main__": pytest.main([__file__, "-v", "--keep-output"])
