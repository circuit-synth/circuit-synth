#!/usr/bin/env python3
"""
Fixture: Circuit with text annotations (design notes).

Tests the ability to add, preserve, and manage text annotations in schematics.
Text annotations are critical for circuit documentation and collaboration.

Example annotations:
- "DESIGN NOTE: This is power section"
- "POWER BUDGET: 500mW"
- "TODO: Add decoupling capacitors"
- "WARNING: High-speed signals - route with care"
"""

from circuit_synth import *


@circuit(name="circuit_with_notes")
def circuit_with_notes():
    """Circuit with resistors and text annotations (design notes)."""

    # Create simple components for basic circuit
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Create net connecting resistors
    net1 = Net("net1")
    r1[1] += net1
    r2[1] += net1

    # Add text annotations (design notes) to circuit
    # Position is (x, y) in mm from top-left of schematic

    # Get the current circuit context
    from circuit_synth.core.decorators import get_current_circuit
    circuit_obj = get_current_circuit()

    # Design note at top of schematic - identifies power section
    note1 = add_text(
        text="DESIGN NOTE: This is power section",
        position=(20, 20),
        size=1.5,
        bold=False,
    )

    # Power budget note - documents power constraints
    note2 = add_text(
        text="POWER BUDGET: 500mW max",
        position=(20, 40),
        size=1.27,
        bold=False,
    )

    # Add annotations to circuit
    circuit_obj.add_annotation(note1)
    circuit_obj.add_annotation(note2)

    # MARKER: Additional annotations can be added here


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = circuit_with_notes()

    circuit_obj.generate_kicad_project(
        project_name="circuit_with_notes",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Circuit with text annotations generated successfully!")
    print("📁 Open in KiCad: circuit_with_notes/circuit_with_notes.kicad_pro")
    print("\n📝 Text annotations added:")
    print("   - 'DESIGN NOTE: This is power section' at (20, 20)")
    print("   - 'POWER BUDGET: 500mW max' at (20, 40)")
