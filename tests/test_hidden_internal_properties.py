"""
Test that internal properties (hierarchy_path, project_name, root_uuid) are hidden from view.

Issue #555: These properties should be retained internally for parsing but hidden from
display in KiCad schematics to avoid cluttering sub-sheet components.
"""

import tempfile
from pathlib import Path

import pytest
from kicad_sch_api import Schematic

from circuit_synth import Component, Net, circuit


@circuit(name="TestProject")
def test_circuit():
    """Test circuit with hierarchical subcircuit."""
    # Add a component to the root
    resistor = Component("Device:R", ref="R", value="10k")

    # Create a subcircuit
    @circuit(name="PowerSupply")
    def power_supply():
        """Power supply subcircuit."""
        vreg = Component("Regulator_Linear:AMS1117-3.3", ref="U", value="AMS1117-3.3")

    # Instantiate the subcircuit
    power = power_supply()
    return power


def test_internal_properties_are_hidden_in_subsheet():
    """
    Test that hierarchy_path, project_name, and root_uuid properties are hidden
    in sub-sheet components but still retained for parsing.
    """
    # Create a simple hierarchical circuit
    root_circuit = test_circuit()

    # Generate schematic files
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        root.generate_kicad_project(
            project_name="TestProject",
            output_dir=str(output_dir),
            force_regenerate=True
        )

        # Load the generated sub-sheet schematic
        power_sch_path = output_dir / "PowerSupply.kicad_sch"
        assert power_sch_path.exists(), f"Sub-sheet schematic not found: {power_sch_path}"

        power_sch = Schematic.load(str(power_sch_path))

        # Find the voltage regulator component
        vreg_comp = None
        for comp in power_sch.components:
            if comp.reference == "U1":
                vreg_comp = comp
                break

        assert vreg_comp is not None, "Voltage regulator component not found in sub-sheet"

        # CRITICAL ASSERTIONS:
        # 1. Properties should exist (needed for parsing)
        assert "hierarchy_path" in vreg_comp.properties, \
            "hierarchy_path property should exist (needed for instance generation)"
        assert "project_name" in vreg_comp.properties, \
            "project_name property should exist (needed for instance generation)"
        assert "root_uuid" in vreg_comp.properties, \
            "root_uuid property should exist (needed for instance generation)"

        # 2. Properties should be HIDDEN (not visible in KiCad)
        assert "hierarchy_path" in vreg_comp.hidden_properties, \
            "hierarchy_path should be in hidden_properties set"
        assert "project_name" in vreg_comp.hidden_properties, \
            "project_name should be in hidden_properties set"
        assert "root_uuid" in vreg_comp.hidden_properties, \
            "root_uuid should be in hidden_properties set"


def test_internal_properties_not_visible_in_kicad_file():
    """
    Test that hidden properties are marked with (hide yes) in the KiCad schematic file.
    """
    # Create a simple hierarchical circuit
    with Circuit("TestProject") as root:
        with Circuit("SubCircuit") as sub:
            comp = Component("Device:C", ref="C1", value="10uF")

        root.add_subcircuit(sub, x=50, y=50)

    # Generate schematic files
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        root.generate_kicad_project(
            project_name="TestProject",
            output_dir=str(output_dir),
            force_regenerate=True
        )

        # Read the raw KiCad schematic file
        sub_sch_path = output_dir / "SubCircuit.kicad_sch"
        assert sub_sch_path.exists(), f"Sub-circuit schematic not found: {sub_sch_path}"

        with open(sub_sch_path, 'r') as f:
            sch_content = f.read()

        # Check that internal properties have (hide yes) flag
        # Example format: (property "hierarchy_path" "/..." ... (effects ... (hide yes)))
        assert '(property "hierarchy_path"' in sch_content, \
            "hierarchy_path property should exist in schematic"
        assert '(property "project_name"' in sch_content, \
            "project_name property should exist in schematic"
        assert '(property "root_uuid"' in sch_content, \
            "root_uuid property should exist in schematic"

        # Verify they have (hide yes) flag
        # This is a simplified check - the full format is complex
        lines = sch_content.split('\n')
        for i, line in enumerate(lines):
            if '(property "hierarchy_path"' in line or \
               '(property "project_name"' in line or \
               '(property "root_uuid"' in line:
                # Search next few lines for (hide yes)
                next_lines = '\n'.join(lines[i:i+5])
                assert '(hide yes)' in next_lines, \
                    f"Property should have (hide yes) flag: {line}"


def test_root_sheet_components_dont_need_internal_properties():
    """
    Test that components on the root sheet don't have internal properties
    (they're not needed for flat designs).
    """
    # Create a flat circuit (no hierarchy)
    with Circuit("FlatCircuit") as root:
        resistor = Component("Device:R", ref="R1", value="10k")

    # Generate schematic
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        root.generate_kicad_project(
            project_name="FlatCircuit",
            output_dir=str(output_dir),
            force_regenerate=True
        )

        # Load the root schematic
        root_sch_path = output_dir / "FlatCircuit.kicad_sch"
        assert root_sch_path.exists()

        root_sch = Schematic.load(str(root_sch_path))

        # Find the resistor
        resistor_comp = None
        for comp in root_sch.components:
            if comp.reference == "R1":
                resistor_comp = comp
                break

        assert resistor_comp is not None, "Resistor not found in root sheet"

        # Root sheet components should NOT have hierarchy_path or root_uuid
        # (project_name might still be set for consistency)
        assert "hierarchy_path" not in resistor_comp.properties or \
               resistor_comp.properties.get("hierarchy_path") == "/", \
            "Root sheet component shouldn't have hierarchy_path"
        assert "root_uuid" not in resistor_comp.properties, \
            "Root sheet component shouldn't have root_uuid"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
