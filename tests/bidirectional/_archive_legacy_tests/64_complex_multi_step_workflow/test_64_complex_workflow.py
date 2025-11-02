#!/usr/bin/env python3
"""
Automated test for 64_complex_multi_step_workflow bidirectional test.

Tests THE ULTIMATE SCENARIO: Complex multi-step iterative design workflow with
position preservation throughout multiple Python modifications, KiCad layouts,
and component additions.

Core Question: Does circuit-synth enable TRUE professional EE workflow where
engineers can freely iterate between Python code modifications and KiCad layout
work without losing positions or layout work?

This test simulates 5 steps of real-world iterative design:
1. Initial design in Python (C1, U1, C2) → Generate to KiCad
2. Layout in KiCad → Manually position components (simulated via file edit)
3. Add protection in Python (D1) → Regenerate (preserves previous positions)
4. Refine layout in KiCad → Position new diode (simulated)
5. Add indicators in Python (D2, R1) → Regenerate (preserves ALL previous positions)

Validation uses kicad-sch-api for Level 2 semantic validation.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_64_complex_multi_step_workflow(request):
    """Test complex multi-step iterative design workflow with position preservation.

    THE ULTIMATE TEST:
    Validates that the entire professional EE workflow is viable:
    - Design in Python
    - Layout in KiCad
    - Modify in Python (preserving KiCad positions)
    - Refine in KiCad (preserving component relationships)
    - Repeat indefinitely

    Workflow (5 steps):
    1. Initial design: Create voltage regulator in Python (C1, U1, C2)
    2. KiCad layout: Manually position components (simulated via file edit)
    3. Add protection: Uncomment diode D1 in Python, regenerate (positions preserved)
    4. KiCad refine: Position new diode (simulated)
    5. Add indicators: Uncomment LED D2 + resistor R1 in Python, regenerate (ALL positions preserved)

    Why critical:
    - This is THE workflow for professional electronics design
    - Without position preservation at EVERY step, workflow is broken
    - Tests cumulative complexity: each step builds on previous
    - Validates position preservation across multiple iterations

    Level 2 Semantic Validation:
    - kicad-sch-api for position validation at each step
    - Component count validation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "voltage_regulator.py"
    output_dir = test_dir / "voltage_regulator"
    schematic_file = output_dir / "voltage_regulator.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Initial Design in Python (C1, U1, C2)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Initial Design - Generate voltage regulator to KiCad")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "voltage_regulator.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Initial generation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"

        # Load and validate initial circuit
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 3, f"Expected 3 components (C1, U1, C2), got {len(components)}"

        # Find and store initial positions
        c1 = next((c for c in components if c.reference == "C1"), None)
        u1 = next((c for c in components if c.reference == "U1"), None)
        c2 = next((c for c in components if c.reference == "C2"), None)

        assert c1 and u1 and c2, "Missing expected components C1, U1, C2"

        positions = {
            "C1_step1": (c1.position.x, c1.position.y),
            "U1_step1": (u1.position.x, u1.position.y),
            "C2_step1": (c2.position.x, c2.position.y),
        }

        print(f"✅ Step 1: Initial circuit generated")
        print(f"   - C1 at {positions['C1_step1']}")
        print(f"   - U1 at {positions['U1_step1']}")
        print(f"   - C2 at {positions['C2_step1']}")

        # =====================================================================
        # STEP 2: Simulate KiCad Layout - Manually position components
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: KiCad Layout - Manually position components")
        print("="*70)

        # Move C1 to (50, 50), U1 to (100, 50), C2 to (150, 50)
        # This simulates an engineer laying out components optimally
        target_positions = {
            "C1": (50.0, 50.0),
            "U1": (100.0, 50.0),
            "C2": (150.0, 50.0),
        }

        # Read and modify schematic file
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        # Move each component to target position
        for ref, (x, y) in target_positions.items():
            # Find component's symbol block
            ref_pattern = f'(property "Reference" "{ref}"'
            ref_pos = sch_content.find(ref_pattern)
            assert ref_pos != -1, f"Could not find {ref} in schematic"

            # Find symbol block start
            symbol_start = sch_content.rfind('(symbol', 0, ref_pos)
            assert symbol_start != -1

            # Find matching closing parenthesis
            paren_count = 0
            i = symbol_start
            symbol_end = -1

            while i < len(sch_content):
                if sch_content[i] == '(':
                    paren_count += 1
                elif sch_content[i] == ')':
                    paren_count -= 1
                    if paren_count == 0:
                        symbol_end = i + 1
                        break
                i += 1

            assert symbol_end != -1, f"Could not find closing parenthesis for {ref}"

            # Extract and modify component block
            component_block = sch_content[symbol_start:symbol_end]
            component_block_moved = re.sub(
                r'\(at\s+[\d.]+\s+[\d.]+\s+[\d.]+\)',
                f'(at {x} {y} 0)',
                component_block,
                count=1
            )

            # Replace in schematic
            sch_content = (
                sch_content[:symbol_start] +
                component_block_moved +
                sch_content[symbol_end:]
            )

        # Write modified schematic
        with open(schematic_file, 'w') as f:
            f.write(sch_content)

        # Verify positions
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        for ref, (target_x, target_y) in target_positions.items():
            comp = next((c for c in components if c.reference == ref), None)
            assert comp, f"{ref} not found after manual positioning"
            assert comp.position.x == target_x and comp.position.y == target_y, (
                f"{ref} not at target position ({target_x}, {target_y}), got ({comp.position.x}, {comp.position.y})"
            )
            positions[f"{ref}_step2"] = (comp.position.x, comp.position.y)

        print(f"✅ Step 2: Components manually positioned")
        print(f"   - C1 moved to {positions['C1_step2']}")
        print(f"   - U1 moved to {positions['U1_step2']}")
        print(f"   - C2 moved to {positions['C2_step2']}")

        # =====================================================================
        # STEP 3: Add Protection Diode in Python (D1)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Add Protection - Uncomment diode D1 in Python")
        print("="*70)

        # Uncomment D1 component - replace entire commented block
        d1_commented = '''    # STEP 3: Protection diode (uncommented by test)
    # d1 = Component(
    #     symbol="Device:D",
    #     ref="D1",
    #     value="1N4007",
    #     footprint="Diode_SMD:D_SOD-123",
    # )'''

        d1_uncommented = '''    # STEP 3: Protection diode (uncommented by test)
    d1 = Component(
        symbol="Device:D",
        ref="D1",
        value="1N4007",
        footprint="Diode_SMD:D_SOD-123",
    )'''

        modified_code = original_code.replace(d1_commented, d1_uncommented)

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        # Regenerate
        result = subprocess.run(
            ["uv", "run", "voltage_regulator.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 3 failed: Regeneration with D1\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Validate: C1, U1, C2 positions PRESERVED, D1 added
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 4, f"Expected 4 components (C1, U1, C2, D1), got {len(components)}"

        # Verify POSITION PRESERVATION (critical!)
        c1 = next((c for c in components if c.reference == "C1"), None)
        u1 = next((c for c in components if c.reference == "U1"), None)
        c2 = next((c for c in components if c.reference == "C2"), None)
        d1 = next((c for c in components if c.reference == "D1"), None)

        assert c1 and u1 and c2 and d1, "Missing expected components"

        # CRITICAL: Previous positions must be preserved
        assert (c1.position.x, c1.position.y) == positions["C1_step2"], (
            f"❌ C1 POSITION NOT PRESERVED! Was {positions['C1_step2']}, now ({c1.position.x}, {c1.position.y})"
        )
        assert (u1.position.x, u1.position.y) == positions["U1_step2"], (
            f"❌ U1 POSITION NOT PRESERVED! Was {positions['U1_step2']}, now ({u1.position.x}, {u1.position.y})"
        )
        assert (c2.position.x, c2.position.y) == positions["C2_step2"], (
            f"❌ C2 POSITION NOT PRESERVED! Was {positions['C2_step2']}, now ({c2.position.x}, {c2.position.y})"
        )

        positions["D1_step3"] = (d1.position.x, d1.position.y)

        print(f"✅ Step 3: Protection diode added, positions PRESERVED")
        print(f"   - C1 preserved at {positions['C1_step2']} ✓")
        print(f"   - U1 preserved at {positions['U1_step2']} ✓")
        print(f"   - C2 preserved at {positions['C2_step2']} ✓")
        print(f"   - D1 auto-placed at {positions['D1_step3']}")

        # =====================================================================
        # STEP 4: Simulate KiCad Refinement - Position D1
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: KiCad Refinement - Position D1 near input")
        print("="*70)

        # Move D1 to (25, 50) - before C1
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        # Find D1 and move it
        ref_pattern = '(property "Reference" "D1"'
        ref_pos = sch_content.find(ref_pattern)
        assert ref_pos != -1, "Could not find D1 in schematic"

        symbol_start = sch_content.rfind('(symbol', 0, ref_pos)
        paren_count = 0
        i = symbol_start
        symbol_end = -1

        while i < len(sch_content):
            if sch_content[i] == '(':
                paren_count += 1
            elif sch_content[i] == ')':
                paren_count -= 1
                if paren_count == 0:
                    symbol_end = i + 1
                    break
            i += 1

        d1_block = sch_content[symbol_start:symbol_end]
        d1_block_moved = re.sub(
            r'\(at\s+[\d.]+\s+[\d.]+\s+[\d.]+\)',
            '(at 25 50 0)',
            d1_block,
            count=1
        )

        sch_content = (
            sch_content[:symbol_start] +
            d1_block_moved +
            sch_content[symbol_end:]
        )

        with open(schematic_file, 'w') as f:
            f.write(sch_content)

        # Verify
        sch = Schematic.load(str(schematic_file))
        d1 = next((c for c in sch.components if c.reference == "D1"), None)
        assert d1.position.x == 25.0 and d1.position.y == 50.0
        positions["D1_step4"] = (d1.position.x, d1.position.y)

        print(f"✅ Step 4: D1 positioned at {positions['D1_step4']}")

        # =====================================================================
        # STEP 5: Add Power Indicators in Python (D2, R1)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Add Indicators - Uncomment LED D2 + resistor R1 in Python")
        print("="*70)

        # Read current modified code
        with open(python_file, "r") as f:
            current_code = f.read()

        # Uncomment D2 and R1 - replace entire commented blocks
        d2_r1_commented = '''    # STEP 5: LED indicator and resistor (uncommented by test)
    # d2 = Component(
    #     symbol="Device:LED",
    #     ref="D2",
    #     value="RED",
    #     footprint="LED_SMD:LED_0603_1608Metric",
    # )
    #
    # r1 = Component(
    #     symbol="Device:R",
    #     ref="R1",
    #     value="1k",
    #     footprint="Resistor_SMD:R_0603_1608Metric",
    # )'''

        d2_r1_uncommented = '''    # STEP 5: LED indicator and resistor (uncommented by test)
    d2 = Component(
        symbol="Device:LED",
        ref="D2",
        value="RED",
        footprint="LED_SMD:LED_0603_1608Metric",
    )

    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )'''

        modified_code = current_code.replace(d2_r1_commented, d2_r1_uncommented)

        with open(python_file, "w") as f:
            f.write(modified_code)

        # Regenerate
        result = subprocess.run(
            ["uv", "run", "voltage_regulator.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 5 failed: Regeneration with D2, R1\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Validate: ALL previous positions PRESERVED (C1, U1, C2, D1), D2 and R1 added
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 6, f"Expected 6 components, got {len(components)}"

        # Find all components
        c1 = next((c for c in components if c.reference == "C1"), None)
        u1 = next((c for c in components if c.reference == "U1"), None)
        c2 = next((c for c in components if c.reference == "C2"), None)
        d1 = next((c for c in components if c.reference == "D1"), None)
        d2 = next((c for c in components if c.reference == "D2"), None)
        r1 = next((c for c in components if c.reference == "R1"), None)

        assert c1 and u1 and c2 and d1 and d2 and r1, "Missing expected components"

        # CRITICAL: ALL previous positions must be preserved
        assert (c1.position.x, c1.position.y) == positions["C1_step2"], (
            f"❌ C1 POSITION NOT PRESERVED in Step 5!"
        )
        assert (u1.position.x, u1.position.y) == positions["U1_step2"], (
            f"❌ U1 POSITION NOT PRESERVED in Step 5!"
        )
        assert (c2.position.x, c2.position.y) == positions["C2_step2"], (
            f"❌ C2 POSITION NOT PRESERVED in Step 5!"
        )
        assert (d1.position.x, d1.position.y) == positions["D1_step4"], (
            f"❌ D1 POSITION NOT PRESERVED in Step 5!"
        )

        positions["D2_step5"] = (d2.position.x, d2.position.y)
        positions["R1_step5"] = (r1.position.x, r1.position.y)

        print(f"✅ Step 5: Indicators added, ALL positions PRESERVED")
        print(f"   - C1 preserved at {positions['C1_step2']} ✓")
        print(f"   - U1 preserved at {positions['U1_step2']} ✓")
        print(f"   - C2 preserved at {positions['C2_step2']} ✓")
        print(f"   - D1 preserved at {positions['D1_step4']} ✓")
        print(f"   - D2 auto-placed at {positions['D2_step5']}")
        print(f"   - R1 auto-placed at {positions['R1_step5']}")

        # =====================================================================
        # FINAL VALIDATION: Verify complete workflow integrity
        # =====================================================================
        print("\n" + "="*70)
        print("FINAL VALIDATION: Complete workflow integrity")
        print("="*70)

        # Final check: All components present, positions preserved
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 6, f"Final validation: Expected 6 components, got {len(components)}"

        # Verify all positions one last time
        position_checks = [
            ("C1", positions["C1_step2"]),
            ("U1", positions["U1_step2"]),
            ("C2", positions["C2_step2"]),
            ("D1", positions["D1_step4"]),
            ("D2", positions["D2_step5"]),
            ("R1", positions["R1_step5"]),
        ]

        all_preserved = True
        for ref, expected_pos in position_checks:
            comp = next((c for c in components if c.reference == ref), None)
            assert comp, f"{ref} not found in final schematic"
            actual_pos = (comp.position.x, comp.position.y)
            if actual_pos != expected_pos:
                print(f"   ❌ {ref}: Expected {expected_pos}, got {actual_pos}")
                all_preserved = False
            else:
                print(f"   ✅ {ref}: Position preserved at {expected_pos}")

        assert all_preserved, "Some positions were not preserved through workflow"

        print(f"\n🎉 COMPLETE MULTI-STEP WORKFLOW VALIDATED!")
        print(f"   ✅ 5 design iterations completed")
        print(f"   ✅ 2 Python code modifications (added D1, then D2+R1)")
        print(f"   ✅ 2 KiCad layout sessions (initial layout, position D1)")
        print(f"   ✅ ALL positions preserved throughout")
        print(f"   ✅ True bidirectional workflow ACHIEVED!")
        print(f"\n💡 Professional EE workflow is VIABLE with circuit-synth!")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
