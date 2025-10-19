#!/usr/bin/env python3
"""
RS-485 Transceiver Circuit
Robust half-duplex serial communication for industrial/long-distance applications
"""

from circuit_synth import *

@circuit(name="RS485_Transceiver")
def rs485_transceiver(vcc, gnd, uart_tx, uart_rx, re_de_control, rs485_a, rs485_b):
    """
    RS-485 transceiver for differential serial communication

    Key features:
    - Long distance: Up to 1200 meters (4000 feet)
    - High noise immunity: Differential signaling
    - Multi-drop: Up to 32 nodes on one bus
    - Speed: Up to 10 Mbps (distance dependent)

    Common applications:
    - Industrial automation (Modbus RTU)
    - Building automation (BACnet MS/TP)
    - Long-distance sensor networks
    - Multi-drop communication systems

    Args:
        vcc: Supply voltage (3.3V or 5V)
        gnd: Ground reference
        uart_tx: UART TX from microcontroller
        uart_rx: UART RX to microcontroller
        re_de_control: Receiver Enable / Driver Enable control pin
                      (LOW = receive mode, HIGH = transmit mode)
        rs485_a: RS-485 A line (non-inverting)
        rs485_b: RS-485 B line (inverting)

    Circuit topology:
        MCU UART <--> RS-485 Transceiver IC <--> Differential Bus (A/B)

    Note: RE and DE pins are typically tied together and controlled
          by MCU GPIO (HIGH to transmit, LOW to receive)
    """

    # RS-485 transceiver IC (popular choices: MAX485, SN65HVD72, ISO1176)
    # Using MAX485 pinout as reference (SOIC-8)
    transceiver = Component(
        symbol="Interface_UART:MAX485",  # Half-duplex RS-485 transceiver
        ref="U",
        footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
    )

    # Power supply decoupling capacitor
    cap_vcc = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Bus termination resistor (120Ω, only at each end of bus)
    # Note: Only populate on end nodes, not intermediate nodes
    r_term = Component(
        symbol="Device:R",
        ref="R",
        value="120",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Failsafe bias resistors (optional but recommended)
    # Ensures defined bus state when no driver is active
    r_bias_a = Component(
        symbol="Device:R",
        ref="R",
        value="560",  # Pull A high
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r_bias_b = Component(
        symbol="Device:R",
        ref="R",
        value="560",  # Pull B low
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # ESD protection diodes (optional but recommended for robustness)
    tvs_a = Component(
        symbol="Device:D_TVS",
        ref="D",
        footprint="Diode_SMD:D_SOD-523"
    )

    tvs_b = Component(
        symbol="Device:D_TVS",
        ref="D",
        footprint="Diode_SMD:D_SOD-523"
    )

    # Power connections
    transceiver["VCC"] += vcc
    transceiver["GND"] += gnd
    cap_vcc[1] += vcc
    cap_vcc[2] += gnd

    # UART interface
    transceiver["DI"] += uart_tx   # Data Input (from MCU TX)
    transceiver["RO"] += uart_rx   # Receiver Output (to MCU RX)

    # Driver/Receiver enable (typically tied together)
    transceiver["DE"] += re_de_control  # Driver Enable
    transceiver["RE"] += re_de_control  # Receiver Enable (active LOW)

    # RS-485 bus connections
    transceiver["A"] += rs485_a    # Non-inverting output
    transceiver["B"] += rs485_b    # Inverting output

    # Bus termination (120Ω between A and B)
    r_term[1] += rs485_a
    r_term[2] += rs485_b

    # Failsafe biasing
    r_bias_a[1] += vcc       # Pull A toward VCC
    r_bias_a[2] += rs485_a
    r_bias_b[1] += rs485_b   # Pull B toward GND
    r_bias_b[2] += gnd

    # ESD protection
    tvs_a[1] += rs485_a
    tvs_a[2] += gnd
    tvs_b[1] += rs485_b
    tvs_b[2] += gnd


@circuit(name="RS485_Simple")
def rs485_simple(vcc, gnd, uart_tx, uart_rx, re_de_control, rs485_a, rs485_b):
    """
    Simplified RS-485 circuit (minimal components)

    Use this for:
    - Short bus lengths (<100m)
    - Single point-to-point connections
    - Indoor, low-noise environments
    - Cost-sensitive designs

    Omits:
    - Failsafe bias resistors
    - ESD protection
    - Just transceiver + decoupling + termination
    """

    transceiver = Component(
        symbol="Interface_UART:MAX485",
        ref="U",
        footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
    )

    cap_vcc = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    r_term = Component(
        symbol="Device:R",
        ref="R",
        value="120",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Power
    transceiver["VCC"] += vcc
    transceiver["GND"] += gnd
    cap_vcc[1] += vcc
    cap_vcc[2] += gnd

    # UART
    transceiver["DI"] += uart_tx
    transceiver["RO"] += uart_rx
    transceiver["DE"] += re_de_control
    transceiver["RE"] += re_de_control

    # Bus
    transceiver["A"] += rs485_a
    transceiver["B"] += rs485_b
    r_term[1] += rs485_a
    r_term[2] += rs485_b


# Design notes and best practices
"""
RS-485 Circuit Design Notes:

1. **Termination Resistors:**
   - Value: 120Ω (matches cable characteristic impedance)
   - Location: Only at both ENDS of the bus
   - Do NOT populate on intermediate nodes
   - Prevents signal reflections

2. **Failsafe Biasing:**
   - A-line: Pull-up resistor to VCC (typically 560Ω)
   - B-line: Pull-down resistor to GND (typically 560Ω)
   - Ensures defined idle state (A > B)
   - Required when bus may be undriven

3. **Cable Requirements:**
   - Twisted pair (STP or UTP)
   - 120Ω characteristic impedance
   - Common cables: Cat5e, Cat6, industrial RS-485 cable
   - Shield connection: Ground at ONE end only (avoid ground loops)

4. **Multi-Drop Topology:**
   - Daisy-chain (linear bus) topology preferred
   - Avoid star or stub connections (causes reflections)
   - Maximum 32 unit loads per segment
   - Use repeaters for more nodes or longer distances

5. **Driver Enable Control:**
   - MCU must control RE/DE pin timing
   - DE HIGH: Transmit mode (driver enabled)
   - RE LOW: Receive mode (receiver enabled)
   - Typical firmware: Toggle before/after UART transmission

6. **ESD Protection:**
   - Recommended for industrial environments
   - TVS diodes on A and B lines
   - Clamp voltage: Just above VCC (e.g., 5.5V for 5V system)

7. **Common IC Choices:**
   - MAX485: Basic, cheap, 2.5 Mbps, 3.3V/5V
   - SN65HVD72: Enhanced ESD, ±15kV, 20 Mbps, 3.3V
   - ISO1176: Isolated, 2.5kV isolation, 20 Mbps, 3.3V/5V
   - LTC2850: Wide supply (3V-5.5V), 20 Mbps, ±60V fault

8. **Data Rate vs Distance:**
   - 100 kbps: 1200 m (4000 ft)
   - 1 Mbps: 300 m (1000 ft)
   - 10 Mbps: 10 m (30 ft)
   - Lower speed = longer reliable distance

9. **Protocol Considerations:**
   - Half-duplex: Only one node transmits at a time
   - Master-slave or token-passing required
   - Common protocols: Modbus RTU, Profibus, BACnet MS/TP

10. **Testing Tips:**
    - Use oscilloscope to check differential voltage (A-B)
    - Idle state: |V(A) - V(B)| > 200mV (defined)
    - Active: |V(A) - V(B)| should be 1.5V to 5V
    - Check for reflections (ringing) - indicates termination issues
"""
