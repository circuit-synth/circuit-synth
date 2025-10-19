#!/usr/bin/env python3
"""
Op-Amp Voltage Follower (Buffer) Circuit
Unity-gain buffer for impedance matching and signal isolation
"""

from circuit_synth import *

@circuit(name="OpAmp_Voltage_Follower")
def opamp_voltage_follower(vcc, gnd, input_signal, output_signal):
    """
    Op-amp configured as voltage follower (unity-gain buffer)

    Key features:
    - Unity gain (Vout = Vin)
    - Very high input impedance (~10^12 Ω)
    - Very low output impedance (~10 Ω)
    - Excellent for buffering high-impedance sources

    Common applications:
    - Buffer sensor outputs before ADC
    - Impedance matching between stages
    - Isolate high-impedance sources from loads
    - Drive long cables or multiple loads
    - Active filtering stages

    Args:
        vcc: Positive supply (e.g., +5V, +3.3V)
        gnd: Ground / negative supply
        input_signal: High-impedance input signal
        output_signal: Low-impedance buffered output

    Circuit topology:
        - Non-inverting input (+) connected to input signal
        - Inverting input (-) connected to output (100% feedback)
        - Output follows input with unity gain

    Recommended op-amps:
    - MCP6001: Single, rail-to-rail, low power, SOT-23-5
    - OPA2340: Dual, rail-to-rail, precision, SOIC-8
    - LMV321: Single, rail-to-rail, general purpose, SOT-23-5
    """

    # Op-amp in SOT-23-5 package (common for single op-amps)
    # Pin configuration: 1=OUT, 2=GND, 3=IN+, 4=IN-, 5=VCC
    opamp = Component(
        symbol="Amplifier_Operational:MCP6001",  # Single rail-to-rail op-amp
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-23-5"
    )

    # Power supply decoupling capacitor
    cap_vcc = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Optional: Output filtering capacitor (reduces high-frequency noise)
    cap_out = Component(
        symbol="Device:C",
        ref="C",
        value="10nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Connections
    # Power supply
    opamp["V+"] += vcc
    opamp["V-"] += gnd
    cap_vcc[1] += vcc
    cap_vcc[2] += gnd

    # Voltage follower configuration
    opamp["+"] += input_signal      # Non-inverting input
    opamp["-"] += output_signal     # Inverting input (feedback from output)
    opamp["OUT"] += output_signal   # Output

    # Output filtering
    cap_out[1] += output_signal
    cap_out[2] += gnd


@circuit(name="Dual_OpAmp_Follower")
def dual_opamp_follower(vcc, gnd, input_a, output_a, input_b, output_b):
    """
    Dual op-amp voltage follower for two independent channels

    Useful for:
    - Buffering multiple sensor outputs
    - Dual-channel data acquisition
    - Stereo audio buffering
    """

    # Dual op-amp in SOIC-8 package
    # Contains two independent op-amps
    opamp_dual = Component(
        symbol="Amplifier_Operational:OPA2340",  # Dual rail-to-rail precision op-amp
        ref="U",
        footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
    )

    # Shared power supply decoupling
    cap_vcc = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Power connections (shared by both op-amps)
    opamp_dual["V+"] += vcc
    opamp_dual["V-"] += gnd
    cap_vcc[1] += vcc
    cap_vcc[2] += gnd

    # First op-amp (channel A)
    opamp_dual["1+"] += input_a     # Non-inverting input
    opamp_dual["1-"] += output_a    # Inverting input (feedback)
    opamp_dual["1OUT"] += output_a  # Output

    # Second op-amp (channel B)
    opamp_dual["2+"] += input_b     # Non-inverting input
    opamp_dual["2-"] += output_b    # Inverting input (feedback)
    opamp_dual["2OUT"] += output_b  # Output


@circuit(name="Sensor_Buffer_Example")
def sensor_buffer_example(vcc_3v3, gnd, sensor_out, mcu_adc_in):
    """
    Example: Buffer high-impedance sensor output before MCU ADC

    Problem: Some sensors have high output impedance (>10kΩ)
             MCU ADCs typically need low impedance (<10kΩ) for accurate readings

    Solution: Op-amp voltage follower provides:
             - High input impedance (doesn't load sensor)
             - Low output impedance (drives ADC properly)
             - No signal attenuation (unity gain)
    """
    opamp_voltage_follower(vcc_3v3, gnd, sensor_out, mcu_adc_in)


# Design notes and calculations
"""
Op-Amp Voltage Follower Design Notes:

1. **Input Impedance:**
   - Typical: 10^12 Ω (extremely high)
   - Benefit: Doesn't load the source
   - Use case: pH sensors, glass electrodes, high-Z probes

2. **Output Impedance:**
   - Typical: <100 Ω (very low)
   - Benefit: Can drive heavy loads
   - Max current: Check op-amp datasheet (typically 20-50mA)

3. **Bandwidth:**
   - Unity-gain bandwidth = op-amp GBW product
   - MCP6001: 1 MHz
   - OPA2340: 5.5 MHz
   - Select based on signal frequency requirements

4. **Stability:**
   - Voltage follower is inherently stable (100% feedback)
   - Add small cap (10-100pF) at output if ringing occurs
   - Keep PCB traces short to avoid parasitic oscillation

5. **Power Supply:**
   - Rail-to-rail op-amps: Output swings close to VCC and GND
   - Input voltage range: Typically GND to VCC
   - Single supply operation: Use GND as V- reference

6. **Applications:**
   - Buffer between stages with impedance mismatch
   - Drive long cables (reduces signal degradation)
   - Multiple load distribution (one source, many loads)
   - Active probe circuits
   - Isolation in mixed-signal designs
"""
