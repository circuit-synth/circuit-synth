"""
Regression test for Issue #479: Components added during sync get correct instance data.

This test verifies that when a component (R2) is added during bidirectional sync,
it receives correct project name and hierarchical path in its instance block.

Issue #479: Without the fix, R2 would show as "R?" in KiCad because it had
incorrect instance data (wrong project name or missing UUID in path).
"""

import shutil
import subprocess
from pathlib import Path

import pytest


def test_issue_479_sync_component_instance_data(request):
    """
    Regression test for Issue #479.

    Workflow:
    1. Generate schematic with R1, C1 (R2 commented out)
    2. Add R2 by uncommenting and regenerating (triggers sync)
    3. Verify R2 has instance block with project name and UUID path
    """

    # Setup
    test_dir = Path(__file__).parent
    python_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    if output_dir.exists():
        shutil.rmtree(output_dir)

    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # Step 1: Generate with R1, C1 only
        result = subprocess.run(
            ["uv", "run", "comprehensive_root.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        assert schematic_file.exists()

        # Step 2: Add R2 and regenerate (sync)
        modified_code = original_code.replace("# r2 = Component(", "r2 = Component(")
        modified_code = modified_code.replace("#     symbol=", "    symbol=")
        modified_code = modified_code.replace("#     ref=", "    ref=")
        modified_code = modified_code.replace("#     value=", "    value=")
        modified_code = modified_code.replace("#     footprint=", "    footprint=")
        modified_code = modified_code.replace("# )", ")")
        modified_code = modified_code.replace("# r2[1] += data", "r2[1] += data")
        modified_code = modified_code.replace("# r2[2] += gnd", "r2[2] += gnd")

        with open(python_file, "w") as f:
            f.write(modified_code)

        result = subprocess.run(
            ["uv", "run", "comprehensive_root.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Sync failed: {result.stderr}"

        # Step 3: Verify R2 has instance block with correct data
        with open(schematic_file, "r") as f:
            content = f.read()

        # Find R2's instances block
        # R2 symbol should have: (instances (project "comprehensive_root" (path "/UUID" ...)))
        r2_start = content.find('(property "Reference" "R2"')
        assert r2_start != -1, "R2 not found in schematic"

        # Find instances block after R2 reference
        r2_instances_start = content.find("(instances", r2_start)
        r2_end = content.find("(symbol", r2_start + 1)  # Next symbol
        if r2_end == -1:
            r2_end = len(content)

        assert r2_instances_start != -1 and r2_instances_start < r2_end, (
            "R2 missing instances block (Issue #479 regression)\n"
            "Without instances, KiCad displays 'R?' instead of 'R2'"
        )

        # Verify instances block has project name
        instances_block = content[r2_instances_start:r2_end]
        assert '(project "comprehensive_root"' in instances_block, (
            "R2 instances missing project name (Issue #479 regression)"
        )

        # Verify path includes UUID (not just "/")
        assert '(path "/' in instances_block, "R2 instances missing path"
        # Path should be /UUID format, not just /
        import re
        path_match = re.search(r'\(path "(/[^"]+)"', instances_block)
        assert path_match, "Could not parse R2 instance path"
        path_value = path_match.group(1)
        assert len(path_value) > 10, (
            f"R2 path too short (Issue #479): {path_value}\n"
            f"Expected format: /UUID, got: {path_value}"
        )

        print("✅ Issue #479 regression test passed")
        print(f"   R2 has instances block with project='comprehensive_root'")
        print(f"   R2 path includes UUID: {path_value}")

    finally:
        # Cleanup
        with open(python_file, "w") as f:
            f.write(original_code)

        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
