#!/usr/bin/env python3
"""
Blank circuit for testing bidirectional sync foundation.

This is the simplest possible circuit-synth circuit: completely empty,
no components, no nets, just the circuit decorator and function.

Used to test:
- Basic Python → KiCad generation
- Basic KiCad → Python import
- Foundation of round-trip behavior
"""

from circuit_synth import circuit


@circuit(name="blank")
def blank():
    """Blank circuit with no components or nets."""
    pass


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = blank()

    circuit_obj.generate_kicad_project(
        project_name="blank",
        placement_algorithm="simple",  # Simple for blank circuit
        generate_pcb=True,
    )

    print("✅ Blank circuit generated successfully!")
    print("📁 Open in KiCad: blank/blank.kicad_pro")
