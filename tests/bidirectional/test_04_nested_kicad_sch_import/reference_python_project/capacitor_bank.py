#!/usr/bin/env python3
"""
capacitor_bank subcircuit

Multi-stage power filtering with bypass and decoupling capacitors
Components: 3 capacitors (C1: 100nF, C2: 10µF, C3: 1µF)
Nets: 2 (VCC, GND)
"""

import logging

from circuit_synth import *

logger = logging.getLogger(__name__)

# Define capacitor components for reuse
Device_C_100nF = Component(
    symbol="Device:C",
    ref="C",
    value="100nF",
    footprint="Capacitor_SMD:C_0603_1608Metric",
)

Device_C_10uF = Component(
    symbol="Device:C",
    ref="C",
    value="10µF",
    footprint="Capacitor_SMD:C_0805_2012Metric",
)

Device_C_1uF = Component(
    symbol="Device:C", ref="C", value="1µF", footprint="Capacitor_SMD:C_0603_1608Metric"
)


@circuit
def capacitor_bank(vcc, gnd):
    """
    Multi-stage power filtering capacitor bank

    Provides comprehensive power supply filtering with:
    - C1 (100nF): High-frequency noise filtering
    - C2 (10µF): Mid-frequency filtering and energy storage
    - C3 (1µF): Intermediate frequency filtering
    """
    logger.info("Creating capacitor bank for power filtering")

    # Instantiate filtering capacitors
    c1 = Device_C_100nF()
    c1.ref = "C1"

    c2 = Device_C_10uF()
    c2.ref = "C2"

    c3 = Device_C_1uF()
    c3.ref = "C3"

    # Connect all capacitors between VCC and GND for filtering
    # High-frequency bypass capacitor
    c1[1] += vcc
    c1[2] += gnd

    # Bulk energy storage capacitor
    c2[1] += vcc
    c2[2] += gnd

    # Intermediate frequency filtering
    c3[1] += vcc
    c3[2] += gnd

    logger.info("Capacitor bank filtering circuit created")
