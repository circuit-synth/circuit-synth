"""
Manual Test Script - Basic Voltage Divider
Part of the Round-Trip Preservation Manual Test Plan

This is the starting point for Test 1 in MANUAL_TEST_PLAN.md
"""

import sys
from pathlib import Path

# Add circuit-synth to path to use local development version
# __file__ -> examples/ -> round-trip/ -> docs/ -> circuit-synth/
project_root = Path(__file__).parent.parent.parent.parent
src_path = str(project_root / "src")

# Remove the specific old circuit-synth-examples path if it exists
old_path = "/Users/shanemattner/Desktop/circuit-synth-examples/submodules/circuit-synth/src"
if old_path in sys.path:
    sys.path.remove(old_path)

# Insert local development version at the beginning
sys.path.insert(0, src_path)

from circuit_synth import Component, Net, circuit
import logging

# Enable debug logging to see what's happening
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

@circuit(name="voltage_divider")
def voltage_divider():
    r1 = Component(
        "Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    r2 = Component(
        "Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    vin = Net("VIN")
    vout = Net("VOUT")
    gnd = Net("GND")

    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd

    return r1, r2

if __name__ == "__main__":
    c = voltage_divider()
    c.generate_kicad_project("voltage_divider", force_regenerate=False, generate_pcb=False)
    print("✅ Test 1: Basic voltage divider generated successfully!")
    print("📂 Open: voltage_divider/voltage_divider.kicad_sch")
