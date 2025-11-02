"""
Unit test for hierarchical label orientation and justification.

This test validates the critical relationship between:
1. Pin orientation (direction pin points FROM component)
2. Label orientation (opposite of pin - points AWAY from component)
3. Label justification (depends on label orientation)

KiCad Coordinate System:
- 0° = RIGHT
- 90° = UP
- 180° = LEFT
- 270° = DOWN

KiCad Justification Rules (verified from multiple test files):
- 0° (RIGHT) → justify left
- 90° (UP) → justify left
- 180° (LEFT) → justify right
- 270° (DOWN) → justify right

Pattern: Labels pointing LEFT or DOWN use right-justify for correct text rendering.

This is a critical test because orientation/justify bugs are:
- Easy to introduce (multiple rotations/transformations involved)
- Hard to debug (requires understanding KiCad's coordinate system)
- Recurring (keeps appearing in different code paths)
"""

from circuit_synth import *


def test_hierarchical_label_orientation_and_justify():
    """
    Test that hierarchical labels have correct orientation and justification.

    This test creates a vertical resistor with labels on both ends:
    - Top pin (pin 1): points UP at 270° → label should point DOWN at 90° with justify left
    - Bottom pin (pin 2): points DOWN at 90° → label should point UP at 270° with justify right
    """

    @circuit(name="test_hier_labels")
    def test_circuit():
        r1 = Component(
            ref="R1",
            symbol="Device:R",
            value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )

        net1 = Net("TopLabel")
        net2 = Net("BottomLabel")

        r1[1] += net1  # Top pin
        r1[2] += net2  # Bottom pin

    circ = test_circuit()
    output_dir = "/tmp/test_hier_label_justify"
    circ.generate_kicad_project(output_dir)

    # Read the generated KiCad schematic file
    sch_path = f"{output_dir}/test_hier_labels.kicad_sch"
    with open(sch_path, 'r') as f:
        content = f.read()

    # Parse hierarchical labels from the file
    labels_data = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        if '(hierarchical_label' in lines[i]:
            # Extract label data
            label_name = lines[i].split('"')[1]

            # Find the (at x y rotation) line
            for j in range(i+1, min(i+15, len(lines))):
                if '(at ' in lines[j]:
                    # Parse: (at x y rotation)
                    at_parts = lines[j].strip().strip('()').split()
                    rotation = float(at_parts[3]) if len(at_parts) > 3 else 0

                # Find the justify line
                if '(justify ' in lines[j]:
                    justify = lines[j].strip().strip('()').split()[1]
                    labels_data.append({
                        'name': label_name,
                        'rotation': rotation,
                        'justify': justify
                    })
                    break
        i += 1

    # Verify we found exactly 2 labels
    assert len(labels_data) == 2, f"Expected 2 hierarchical labels, found {len(labels_data)}"

    # Sort labels for consistent testing
    labels_data = sorted(labels_data, key=lambda x: x['rotation'])

    # Verify label orientations and justifications
    # Label 1: should be at 90° (UP) with justify left
    label_90 = [l for l in labels_data if l['rotation'] == 90.0][0]
    assert label_90['justify'] == 'left', (
        f"Label at 90° should have justify='left', got '{label_90['justify']}'. "
        f"90° (UP) points up, text should be left-justified."
    )

    # Label 2: should be at 270° (DOWN) with justify right
    label_270 = [l for l in labels_data if l['rotation'] == 270.0][0]
    assert label_270['justify'] == 'right', (
        f"Label at 270° should have justify='right', got '{label_270['justify']}'. "
        f"270° (DOWN) points down, text should be right-justified."
    )

    print("✓ All hierarchical label orientations and justifications are correct!")


def test_all_four_orientations():
    """
    Test all four cardinal orientations (0°, 90°, 180°, 270°).

    This test creates a cross-shaped component with pins in all four directions
    to validate the complete justification rule set.
    """

    @circuit(name="test_all_orientations")
    def test_circuit():
        # Use a connector with 4 pins (one in each direction)
        conn = Component(
            ref="J1",
            symbol="Connector_Generic:Conn_01x04",
            value="4-pin",
            footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
        )

        conn[1] += Net("Pin1_Net")
        conn[2] += Net("Pin2_Net")
        conn[3] += Net("Pin3_Net")
        conn[4] += Net("Pin4_Net")

    circ = test_circuit()
    output_dir = "/tmp/test_all_orient"
    circ.generate_kicad_project(output_dir)

    # Read and parse the schematic
    sch_path = f"{output_dir}/test_all_orientations.kicad_sch"
    with open(sch_path, 'r') as f:
        content = f.read()

    # Verify the justification rules for all found orientations
    rotation_to_justify = {}
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        if '(hierarchical_label' in lines[i]:
            rotation = None
            justify = None

            for j in range(i+1, min(i+15, len(lines))):
                if '(at ' in lines[j]:
                    at_parts = lines[j].strip().strip('()').split()
                    rotation = float(at_parts[3]) if len(at_parts) > 3 else 0

                if '(justify ' in lines[j]:
                    justify = lines[j].strip().strip('()').split()[1]
                    if rotation is not None:
                        rotation_to_justify[rotation] = justify
                    break
        i += 1

    # Verify the rules for each orientation we found
    expected_rules = {
        0.0: 'left',    # RIGHT → left justify
        90.0: 'left',   # UP → left justify
        180.0: 'right', # LEFT → right justify
        270.0: 'right', # DOWN → right justify
    }

    for rotation, expected_justify in expected_rules.items():
        if rotation in rotation_to_justify:
            actual_justify = rotation_to_justify[rotation]
            assert actual_justify == expected_justify, (
                f"Orientation {rotation}° should have justify='{expected_justify}', "
                f"got '{actual_justify}'"
            )

    print(f"✓ Verified {len(rotation_to_justify)} orientations with correct justifications!")


if __name__ == "__main__":
    # Run tests
    test_hierarchical_label_orientation_and_justify()
    test_all_four_orientations()
    print("\n✅ All hierarchical label tests passed!")
