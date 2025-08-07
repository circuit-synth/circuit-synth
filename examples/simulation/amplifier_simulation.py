#!/usr/bin/env python3
"""
Comprehensive SPICE Simulation Example: Op-Amp Amplifier Circuit

This example demonstrates the enhanced SPICE simulation capabilities including:
- Using verified manufacturer models
- Automated test bench generation
- Multiple analysis types (DC, AC, Transient)
- Component model selection
"""

from circuit_synth import Circuit, Component, Net
from circuit_synth.simulation import (
    ACAnalysis,
    CircuitSimulator,
    DCAnalysis,
    TestBenchGenerator,
    TransientAnalysis,
    get_manufacturer_models,
)


def create_non_inverting_amplifier():
    """
    Create a non-inverting op-amp amplifier circuit with gain of 10.

    Circuit topology:
    - Op-amp: LM358 (using verified TI model)
    - Gain: 1 + (R2/R1) = 1 + (9k/1k) = 10
    - Single supply: 12V
    - Input: 0.5V DC with 100mV sine wave
    """

    # Create circuit
    circuit = Circuit("Non-Inverting Amplifier")

    # Create nets
    vcc = Net("VCC")
    gnd = Net("GND")
    vin = Net("VIN")
    vout = Net("VOUT")
    vfb = Net("VFB")  # Feedback node

    # Power supply (12V)
    v_supply = Component(
        symbol="Device:V",
        ref="V1",
        value="12V",
        footprint="TestPoint:TestPoint_Pad_D1.0mm",
    )
    v_supply[1] += vcc
    v_supply[2] += gnd

    # Input signal source (0.5V DC + 100mV sine)
    # This would be configured in test bench
    v_input = Component(
        symbol="Device:V",
        ref="V2",
        value="SINE(0.5 0.1 1k)",  # DC offset, amplitude, frequency
        footprint="TestPoint:TestPoint_Pad_D1.0mm",
    )
    v_input[1] += vin
    v_input[2] += gnd

    # Op-amp (LM358)
    # Using simplified symbol - in real circuit would use proper symbol
    opamp = Component(
        symbol="Amplifier_Operational:LM358",
        ref="U1",
        value="LM358_TI",  # Reference to manufacturer model
        footprint="Package_DIP:DIP-8_W7.62mm",
    )
    # Pin connections for LM358 (single op-amp section)
    # Pin 3: Non-inverting input (+)
    # Pin 2: Inverting input (-)
    # Pin 1: Output
    # Pin 8: VCC
    # Pin 4: GND
    opamp[3] += vin  # Non-inverting input
    opamp[2] += vfb  # Inverting input (feedback)
    opamp[1] += vout  # Output
    opamp[8] += vcc  # Power
    opamp[4] += gnd  # Ground

    # Feedback resistors for gain setting
    # Gain = 1 + (R2/R1) = 1 + (9k/1k) = 10
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r1[1] += vfb
    r1[2] += gnd

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="9k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r2[1] += vout
    r2[2] += vfb

    # Output load resistor
    r_load = Component(
        symbol="Device:R",
        ref="R3",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r_load[1] += vout
    r_load[2] += gnd

    # Decoupling capacitor for power supply
    c_decouple = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    c_decouple[1] += vcc
    c_decouple[2] += gnd

    # Add components to circuit
    circuit.add_components([v_supply, v_input, opamp, r1, r2, r_load, c_decouple])

    return circuit


def simulate_amplifier():
    """
    Run comprehensive simulation of the amplifier circuit.
    """

    print("=" * 60)
    print("SPICE SIMULATION: Non-Inverting Amplifier")
    print("=" * 60)

    # Create the circuit
    circuit = create_non_inverting_amplifier()
    print(f"\n✓ Created circuit: {circuit.name}")
    print(f"  Components: {len(circuit.components)}")
    print(f"  Nets: {len(circuit.nets)}")

    # Get manufacturer models
    models = get_manufacturer_models()
    lm358_model = models.get_model("LM358_TI")
    if lm358_model:
        print(f"\n✓ Using manufacturer model: {lm358_model.name}")
        print(f"  Manufacturer: {lm358_model.manufacturer}")
        print(f"  Description: {lm358_model.description}")

        # Get download info
        source_info = models.get_model_source_info("LM358_TI")
        print(f"  Official model source: {source_info['download_url']}")

    # Generate test bench automatically
    print("\n" + "=" * 60)
    print("AUTOMATED TEST BENCH GENERATION")
    print("=" * 60)

    testbench = TestBenchGenerator(circuit)
    testbench_config = testbench.generate_automatic()

    print(f"\n✓ Generated test bench: {testbench_config['description']}")
    print("\n  Analyses to run:")
    for analysis in testbench_config["analyses"]:
        print(f"    - {analysis['type']}: {analysis['description']}")

    # Create simulator
    print("\n" + "=" * 60)
    print("RUNNING SIMULATIONS")
    print("=" * 60)

    try:
        # Note: This would work if PySpice is installed
        sim = CircuitSimulator(circuit)

        # 1. DC Operating Point Analysis
        print("\n1. DC Operating Point Analysis")
        print("-" * 30)
        dc_analysis = DCAnalysis(operating_point=True)
        # dc_result = sim.run_dc_analysis(dc_analysis)
        print("   Would calculate DC bias conditions:")
        print("   - Input DC: 0.5V")
        print("   - Expected output DC: 0.5V × 10 = 5.0V")
        print("   - Op-amp supply current")

        # 2. AC Frequency Response
        print("\n2. AC Frequency Response")
        print("-" * 30)
        ac_analysis = ACAnalysis(
            start_frequency=1, stop_frequency=1e6, points_per_decade=20
        )
        # ac_result = sim.run_ac_analysis(ac_analysis)
        print("   Would analyze frequency response:")
        print("   - Gain at 1kHz: 20dB (10×)")
        print("   - -3dB bandwidth (limited by op-amp GBW)")
        print("   - Phase margin")

        # 3. Transient Analysis
        print("\n3. Transient Time-Domain Analysis")
        print("-" * 30)
        transient = TransientAnalysis(
            step_time=1e-6, end_time=5e-3, start_time=0  # 5ms = 5 periods at 1kHz
        )
        # transient_result = sim.run_transient_analysis(transient)
        print("   Would simulate time-domain response:")
        print("   - Input: 0.5V + 0.1V×sin(2π×1000×t)")
        print("   - Expected output: 5V + 1V×sin(2π×1000×t)")
        print("   - Check for distortion and slew rate limiting")

    except ImportError:
        print("\n⚠️  PySpice not installed - showing simulation setup only")
        print("   Install with: pip install PySpice")

    # Show how to use different models
    print("\n" + "=" * 60)
    print("AVAILABLE MANUFACTURER MODELS")
    print("=" * 60)

    print("\nSample of available verified models:")
    sample_models = [
        "2N3904",  # NPN transistor
        "2N7000",  # N-channel MOSFET
        "1N4148",  # Fast diode
        "TL072_TI",  # JFET op-amp
        "IRFZ44N_INFINEON",  # Power MOSFET
    ]

    for model_name in sample_models:
        model = models.get_model(model_name)
        if model:
            print(f"\n  {model_name}:")
            print(f"    Type: {model.model_type}")
            print(f"    Description: {model.description}")

    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print("=" * 60)


def demonstrate_model_sources():
    """
    Demonstrate how to get official SPICE models from manufacturers.
    """
    print("\n" + "=" * 60)
    print("HOW TO GET OFFICIAL SPICE MODELS")
    print("=" * 60)

    from circuit_synth.simulation.manufacturer_models import print_download_instructions

    print_download_instructions()


if __name__ == "__main__":
    # Run the simulation example
    simulate_amplifier()

    # Show model download instructions
    # demonstrate_model_sources()  # Uncomment to see download instructions

    print("\n✨ Enhanced SPICE simulation example complete!")
    print("   This example demonstrates:")
    print("   - Verified manufacturer models")
    print("   - Automated test bench generation")
    print("   - Multiple analysis types")
    print("   - Model source documentation")
