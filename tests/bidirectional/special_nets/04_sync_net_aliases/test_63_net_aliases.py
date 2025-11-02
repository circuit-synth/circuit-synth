#!/usr/bin/env python3
"""Test special: Net Aliases"""
import pytest, subprocess, shutil
from pathlib import Path

def test_special_63_net_aliases(request):
    test_dir, output_dir = Path(__file__).parent, Path(__file__).parent / "comprehensive_root"
    cleanup = not request.config.getoption("--keep-output", default=False)
    try:
        result = subprocess.run(["uv", "run", str(test_dir / "comprehensive_root.py")], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0
        print(f"\n✅ Test special PASSED: Net Aliases")
    finally:
        if cleanup and output_dir.exists(): shutil.rmtree(output_dir)

if __name__ == "__main__": pytest.main([__file__, "-v", "--keep-output"])
