#!/usr/bin/env python3
"""
Fixture: Circuit for testing conflict resolution.

Initial state: R1=10k, R2=1k
Conflict scenario:
  - Python edit: R1→47k, add R3=4.7k
  - KiCad edit: R1→22k, add R4=100k (manual, not in Python)

Tests circuit-synth behavior when same component modified in both Python and KiCad
without intermediate synchronization.

Real-world use case: Developer forgets to import KiCad changes before editing Python,
or multiple developers working on same circuit simultaneously.
"""

from circuit_synth import circuit, Component


@circuit(name="conflicting_edits")
def conflicting_edits():
    """Circuit with potential conflicting edits between Python and KiCad."""

    # R1: Subject of conflict
    # Initial: 10k
    # Python will change to: 47k
    # KiCad will manually change to: 22k
    # Question: Which wins?
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",  # CONFLICT: Change this to "47k" for conflict test
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # R2: Unchanged in both Python and KiCad (control)
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # R3: Added only in Python (uncomment for conflict test)
    # Uncomment this to add R3 in Python side of conflict
    # r3 = Component(
    #     symbol="Device:R",
    #     ref="R3",
    #     value="4.7k",
    #     footprint="Resistor_SMD:R_0603_1608Metric",
    # )

    # R4: Will be added manually in KiCad only
    # NOT present in Python code
    # Question: Does it survive regeneration?


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = conflicting_edits()

    circuit_obj.generate_kicad_project(
        project_name="conflicting_edits",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Conflicting edits circuit generated!")
    print("📁 Open in KiCad: conflicting_edits/conflicting_edits.kicad_pro")
    print("")
    print("Next steps for conflict test:")
    print("1. Open KiCad and change R1 to 22k, add R4")
    print("2. Edit this Python file: change R1 to 47k, uncomment R3")
    print("3. Regenerate without importing: uv run conflicting_edits.py")
    print("4. Observe which changes survive (Python or KiCad)")
