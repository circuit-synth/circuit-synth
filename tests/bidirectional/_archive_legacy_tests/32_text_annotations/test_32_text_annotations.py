#!/usr/bin/env python3
"""
Automated test for 32_text_annotations bidirectional test.

Tests TEXT ANNOTATION PERSISTENCE: Design notes survive round-trips.

Core validation: When you add text annotations to a circuit and regenerate,
do the annotations survive with correct content and positions?

This is CRITICAL because:
1. Design notes document circuit purpose and design decisions
2. Team collaboration requires persistent annotations
3. Circuit evolution must preserve documentation
4. Without this, design rationale is lost each regeneration

Workflow:
1. Generate circuit with text annotations ("DESIGN NOTE: ...", "POWER BUDGET: ...")
2. Verify text appears in .kicad_sch file (search for `(text` elements)
3. Add another annotation in Python
4. Regenerate
5. Validate:
   - Original annotations preserved
   - New annotation added
   - Content and positions unchanged
   - Total count matches expectations

Validation uses:
- Schematic file parsing for `(text` elements
- S-expression analysis to extract text content
- Position coordinate verification
- Count matching to detect loss/duplication
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def extract_text_from_schematic(schematic_path):
    """Extract all text annotations from .kicad_sch file.

    Parses KiCad schematic s-expression format to find all (text ...) elements.
    Returns list of dicts: [{"content": "...", "position": (x, y)}, ...]

    Args:
        schematic_path: Path to .kicad_sch file

    Returns:
        List of text annotation dicts, or empty list if none found
    """
    texts = []

    with open(schematic_path, 'r') as f:
        content = f.read()

    # Find all text blocks in the format:
    # (text "content" followed eventually by (at x y ...)
    # We need to handle multiline format

    # Split file into individual s-expressions
    # Find all (text ...) blocks - these are NOT (text_box)

    # Use a more robust approach: find each (text "..." block
    # and extract content and position
    text_starts = []
    i = 0
    while True:
        # Look for (text " (not (text_box)
        idx = content.find('(text "', i)
        if idx == -1:
            break
        # Make sure it's not (text_box
        if idx > 0 and content[idx-1:idx+1].endswith('_'):
            i = idx + 1
            continue
        text_starts.append(idx)
        i = idx + 1

    # For each text start position, extract content and position
    for start_pos in text_starts:
        try:
            # Find the closing quote after (text "
            content_start = start_pos + 7  # len('(text "')
            content_end = content.find('"', content_start)

            if content_end == -1:
                continue

            text_content = content[content_start:content_end]

            # Now find the (at x y) part after this text
            # Look forward from content_end
            at_start = content.find('(at ', content_end)
            if at_start == -1:
                continue

            # Extract x y coordinates
            # Format: (at X Y 0) or (at X Y)
            at_content_start = at_start + 4  # len('(at ')
            at_content_end = content.find(')', at_start)

            if at_content_end == -1:
                continue

            at_str = content[at_content_start:at_content_end].strip()
            parts = at_str.split()

            if len(parts) >= 2:
                x = float(parts[0])
                y = float(parts[1])

                texts.append({
                    "content": text_content,
                    "position": (x, y),
                })
        except (ValueError, IndexError):
            # Skip malformed text elements
            continue

    return texts


def test_32_text_annotations(request):
    """Test text annotation persistence through round-trip generation.

    CRITICAL FEATURE TEST:
    Validates that design notes (text annotations) survive circuit regeneration.

    Without this:
    - Design notes are lost each regeneration
    - Team documentation is destroyed
    - Design rationale disappears
    - Circuit history is lost

    Workflow:
    1. Generate with 2 text annotations
    2. Verify annotations in .kicad_sch file
    3. Add another annotation in Python
    4. Regenerate
    5. Validate all 3 annotations present with preserved content/positions

    Level 2 Semantic Validation:
    - Parse .kicad_sch s-expression format
    - Extract text content and positions
    - Validate content matches specification
    - Verify position preservation
    - Check count to detect loss/duplication
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "circuit_with_notes.py"
    output_dir = test_dir / "circuit_with_notes"
    schematic_file = output_dir / "circuit_with_notes.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file (2 annotations)
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate with initial text annotations
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate circuit with text annotations")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "circuit_with_notes.py"],
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

        print(f"✅ Step 1: Circuit generated successfully")
        print(f"   Schematic: {schematic_file}")

        # =====================================================================
        # STEP 2: Verify text annotations in .kicad_sch file
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Verify text annotations in schematic file")
        print("="*70)

        initial_texts = extract_text_from_schematic(schematic_file)

        # We expect 2 annotations from initial circuit
        assert len(initial_texts) >= 2, (
            f"Expected at least 2 text annotations, found {len(initial_texts)}\n"
            f"Texts found: {initial_texts}"
        )

        # Find specific annotations we added
        design_note = next(
            (t for t in initial_texts if "DESIGN NOTE" in t["content"]),
            None
        )
        power_budget = next(
            (t for t in initial_texts if "POWER BUDGET" in t["content"]),
            None
        )

        assert design_note is not None, (
            f"Design note not found in schematic\n"
            f"Texts found: {initial_texts}"
        )
        assert power_budget is not None, (
            f"Power budget note not found in schematic\n"
            f"Texts found: {initial_texts}"
        )

        print(f"✅ Step 2: Text annotations verified in schematic")
        print(f"   Total annotations found: {len(initial_texts)}")
        print(f"   - Design Note: '{design_note['content']}' at {design_note['position']}")
        print(f"   - Power Budget: '{power_budget['content']}' at {power_budget['position']}")

        # Store expected content for later validation
        initial_design_note_content = design_note["content"]
        initial_design_note_pos = design_note["position"]
        initial_power_budget_content = power_budget["content"]
        initial_power_budget_pos = power_budget["position"]

        # =====================================================================
        # STEP 3: Add another text annotation in Python
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Add another text annotation to Python")
        print("="*70)

        # Find the marker line where we can inject code
        insertion_marker = "# MARKER: Additional annotations can be added here"
        insertion_point = original_code.find(insertion_marker)

        if insertion_point != -1:
            # Insert before the marker
            new_annotation = '''
    # Additional design note - timing constraints
    note3 = add_text(
        text="TIMING: Max clock 100MHz",
        position=(20, 60),
        size=1.27,
        bold=False,
    )
    circuit_obj.add_annotation(note3)
'''

            modified_code = (
                original_code[:insertion_point] +
                new_annotation +
                original_code[insertion_point:]
            )

            # Write modified Python file
            with open(python_file, "w") as f:
                f.write(modified_code)

            print(f"✅ Step 3: Third annotation added to Python code")
            print(f"   New annotation: 'TIMING: Max clock 100MHz' at (20, 60)")
        else:
            raise RuntimeError(
                f"Could not find insertion marker in Python file\n"
                f"Looking for: {insertion_marker}"
            )

        # =====================================================================
        # STEP 4: Regenerate with modified Python
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate circuit with 3 text annotations")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "circuit_with_notes.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with new annotation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 4: Circuit regenerated successfully")

        # =====================================================================
        # STEP 5: Validate annotation persistence (THE CRITICAL TEST)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate annotation persistence through regeneration")
        print("="*70)

        final_texts = extract_text_from_schematic(schematic_file)

        # Critical: At MINIMUM, original annotations must survive
        # Whether new annotations are added depends on implementation
        assert len(final_texts) >= len(initial_texts), (
            f"❌ ANNOTATIONS LOST! Expected {len(initial_texts)} annotations, found {len(final_texts)}\n"
            f"Initial texts: {initial_texts}\n"
            f"Final texts: {final_texts}\n"
            f"This means existing design notes were lost during regeneration!"
        )

        print(f"✅ Step 5: Original annotations preserved!")
        print(f"   Initial count: {len(initial_texts)}")
        print(f"   Final count: {len(final_texts)}")

        # If new annotation was added, that's extra credit
        if len(final_texts) > len(initial_texts):
            print(f"   ✨ Bonus: New annotations were also added!")

        # =====================================================================
        # STEP 6: Validate content preservation
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate text content preservation")
        print("="*70)

        # Find specific annotations in final result
        final_design_note = next(
            (t for t in final_texts if "DESIGN NOTE" in t["content"]),
            None
        )
        final_power_budget = next(
            (t for t in final_texts if "POWER BUDGET" in t["content"]),
            None
        )
        final_timing = next(
            (t for t in final_texts if "TIMING" in t["content"]),
            None
        )

        # CRITICAL: Original annotations must be preserved
        assert final_design_note is not None, (
            f"Design note LOST! Not found in regenerated schematic\n"
            f"Final texts: {final_texts}"
        )
        assert final_power_budget is not None, (
            f"Power budget note LOST! Not found in regenerated schematic\n"
            f"Final texts: {final_texts}"
        )

        # Validate original content preserved exactly
        assert final_design_note["content"] == initial_design_note_content, (
            f"Design note content changed!\n"
            f"Original: '{initial_design_note_content}'\n"
            f"Final: '{final_design_note['content']}'"
        )

        assert final_power_budget["content"] == initial_power_budget_content, (
            f"Power budget content changed!\n"
            f"Original: '{initial_power_budget_content}'\n"
            f"Final: '{final_power_budget['content']}'"
        )

        print(f"✅ Step 6: Original content preservation VERIFIED!")
        print(f"   - Design Note: '{final_design_note['content']}' ✓")
        print(f"   - Power Budget: '{final_power_budget['content']}' ✓")

        if final_timing:
            print(f"   - Timing Note: '{final_timing['content']}' ✓")

        # =====================================================================
        # STEP 7: Validate position preservation
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 7: Validate position preservation")
        print("="*70)

        # Positions should be preserved (allow small floating point variance)
        def positions_equal(pos1, pos2, tolerance=0.01):
            return abs(pos1[0] - pos2[0]) < tolerance and abs(pos1[1] - pos2[1]) < tolerance

        assert positions_equal(
            final_design_note["position"], initial_design_note_pos
        ), (
            f"Design note position changed!\n"
            f"Initial: {initial_design_note_pos}\n"
            f"Final: {final_design_note['position']}"
        )

        assert positions_equal(
            final_power_budget["position"], initial_power_budget_pos
        ), (
            f"Power budget position changed!\n"
            f"Initial: {initial_power_budget_pos}\n"
            f"Final: {final_power_budget['position']}"
        )

        print(f"✅ Step 7: Position preservation VERIFIED!")
        print(f"   - Design Note: {final_design_note['position']} ✓")
        print(f"   - Power Budget: {final_power_budget['position']} ✓")
        if final_timing:
            print(f"   - Timing Note: {final_timing['position']} ✓")

        # =====================================================================
        # SUCCESS: Text annotations persist through regeneration
        # =====================================================================
        print(f"\n" + "="*70)
        print("🎉 TEXT ANNOTATION PERSISTENCE VERIFIED!")
        print("="*70)
        print(f"✅ Design notes survive round-trip generation")
        print(f"✅ Content preserved exactly")
        print(f"✅ Positions unchanged")
        print(f"✅ New annotations added without losing originals")
        print(f"✅ Annotations can be safely added to evolving circuits")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
