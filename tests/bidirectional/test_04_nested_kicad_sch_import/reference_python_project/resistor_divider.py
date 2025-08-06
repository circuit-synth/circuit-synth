#!/usr/bin/env python3
"""
resistor_divider subcircuit with integrated power filtering

Enhanced resistor divider circuit with:
- Voltage division (R1, R2)
- Integrated power conditioning via capacitor bank
Components: 2 resistors + capacitor bank subcircuit
Nets: 3 (VIN, GND, MID)
"""

import logging

from capacitor_bank import capacitor_bank

from circuit_synth import *

logger = logging.getLogger(__name__)

# Define resistor components for reuse
Device_R = Component(
    symbol="Device:R", ref="R", footprint="Resistor_SMD:R_0603_1608Metric"
)


@circuit
def resistor_divider(vin, gnd, mid):
    """
    Enhanced resistor divider with power conditioning

    Provides:
    - Voltage division: VIN -> MID (via R1, R2)
    - Power filtering: Clean VIN supply via capacitor bank
    """
    logger.info("Creating resistor divider with power conditioning")

    # Create resistors with proper references and values
    r1 = Device_R()
    r1.ref = "R1"
    r1.value = "1k"

    r2 = Device_R()
    r2.ref = "R2"
    r2.value = "1k"

    # Connect resistors in voltage divider configuration
    r1[1] += vin  # Connect R1 pin 1 to VIN
    r1[2] += mid  # Connect R1 pin 2 to MID (voltage divider output)
    r2[1] += mid  # Connect R2 pin 1 to MID
    r2[2] += gnd  # Connect R2 pin 2 to GND

    # Add power conditioning via capacitor bank
    # This provides clean, filtered power for the resistor divider
    cap_bank = capacitor_bank(vin, gnd)

    logger.info("Resistor divider with power conditioning created")
