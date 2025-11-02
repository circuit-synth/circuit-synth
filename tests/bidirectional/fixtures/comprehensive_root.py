#!/usr/bin/env python3
"""Comprehensive root circuit fixture for bidirectional synchronization tests.

This fixture contains ALL schematic element types to ensure CRUD operations
preserve all other elements during synchronization.

Used by: Phase 1 Component CRUD tests (tests 10-17)

Contains:
- 3 components (R1, R2, C1) - Different types for comprehensive coverage
- 2 power symbols (VCC, GND)
- 2 nets with labels (DATA, CLK)
- Connections between components
"""

from circuit_synth import circuit, Component, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Comprehensive root circuit with ALL element types.

    This is the INITIAL STATE for all Phase 1 CRUD tests.

    Components:
    - R1: 10k resistor (0603 SMD)
    - R2: 4.7k resistor (0603 SMD)
    - C1: 100nF capacitor (0603 SMD)

    Power:
    - VCC: +5V power rail
    - GND: Ground

    Nets:
    - DATA: Connects R1.1 to C1.1
    - CLK: Connects R2.1 to R2.2 (loopback for testing)

    Power Connections:
    - VCC connects to R1.2
    - GND connects to C1.2 and R2.2
    """

    # =========================================================================
    # Components - Different types for comprehensive testing
    # =========================================================================
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # =========================================================================
    # Power Symbols (created as special Nets)
    # =========================================================================
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # =========================================================================
    # Nets with Labels
    # =========================================================================
    data = Net("DATA")
    clk = Net("CLK")

    # =========================================================================
    # Signal Connections
    # =========================================================================
    r1[1] += data
    c1[1] += data

    r2[1] += clk
    # Note: R2.2 connected to GND below

    # =========================================================================
    # Power Connections
    # =========================================================================
    r1[2] += vcc
    c1[2] += gnd
    r2[2] += gnd


if __name__ == "__main__":
    # Generate the circuit for manual inspection
    print("Generating comprehensive_root fixture circuit...")
    circuit_obj = comprehensive_root()
    circuit_obj.generate_kicad_project(
        project_name="comprehensive_root",
        placement_algorithm="simple",
        generate_pcb=True
    )
    print("✅ Circuit generated at: comprehensive_root/comprehensive_root.kicad_sch")
    print("\nThis fixture contains:")
    print("  - Components: R1 (10k), R2 (4.7k), C1 (100nF)")
    print("  - Power: VCC, GND")
    print("  - Nets: DATA (R1-C1), CLK (R2)")
    print("\nUse this as the initial state for all Phase 1 CRUD tests.")
