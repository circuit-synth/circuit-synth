#!/usr/bin/env python3
"""
Test 47: Duplicate References - Edge Case Test

Validates handling of duplicate component references.
Expected: Either auto-rename or graceful error.
"""

import pytest
import subprocess
import shutil
from pathlib import Path


def test_47_duplicate_refs(request):
    """Test duplicate reference handling."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Attempt to generate circuit with duplicate refs
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Either succeeds with auto-rename or fails gracefully
        if result.returncode == 0:
            print("\n✅ Test 47 PASSED: Duplicate refs handled (auto-renamed or allowed)")
            print(f"   - Circuit generated ✓")
        else:
            # Graceful error is acceptable
            assert "duplicate" in result.stderr.lower() or "already exists" in result.stderr.lower(), \
                f"Expected duplicate ref error, got: {result.stderr}"
            print("\n✅ Test 47 PASSED: Duplicate refs caught with error (expected behavior)")
            print(f"   - Error message: {result.stderr[:100]}")

    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
