#!/usr/bin/env python3
"""Test 04: Deep Hierarchy Performance"""
import pytest, subprocess, shutil, time
from pathlib import Path

def test_04_performance(request):
    """Test 10+ hierarchy levels."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "deep_hierarchy.py"
    output_dir = test_dir / "deep_hierarchy"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Measure generation time
        start_time = time.time()
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=60)
        elapsed_time = time.time() - start_time

        # Verify generation succeeded
        assert result.returncode == 0, f"Generation failed: {result.stderr}"

        # Check performance threshold
        max_time = 120.0
        assert elapsed_time < max_time, f"Generation took {elapsed_time:.2f}s, expected < {max_time}s"

        print(f"\n✅ Test 04 PASSED: Deep Hierarchy Performance")
        print(f"   Generation time: {elapsed_time:.2f}s (limit: {max_time}s)")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
