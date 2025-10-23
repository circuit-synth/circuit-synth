"""Minimal Circuit Template

Empty template for experienced circuit-synth users.
This provides the basic structure without any example components.

Use this template when:
- You know exactly what circuit you want to build
- You don't need example/tutorial code
- You want a clean starting point
- You're experienced with circuit-synth syntax

Documentation: https://circuit-synth.readthedocs.io
"""
from circuit_synth import Component, Net, circuit


@circuit(name="My_Circuit")
def my_circuit():
    """
    Your circuit implementation goes here.

    Basic workflow:
    1. Create components: Component(symbol=..., ref=..., footprint=...)
    2. Define nets: Net('NET_NAME')
    3. Connect components to nets: component[pin] += net
    4. Return locals() or specific dict of components/nets

    Example component creation:
        mcu = Component(
            symbol="MCU_ST_STM32F4:STM32F411CEUx",
            ref="U",
            footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
        )

    Example net and connection:
        vcc = Net('VCC_3V3')
        gnd = Net('GND')
        mcu["VDD"] += vcc
        mcu["VSS"] += gnd

    For finding components:
        Use /find-symbol to search KiCad symbols
        Use /find-footprint to search KiCad footprints
        Use /find_stm32 for STM32 peripheral searches
    """

    # TODO: Create your components here
    # Example:
    # resistor = Component(
    #     symbol="Device:R",
    #     ref="R",
    #     value="10k",
    #     footprint="Resistor_SMD:R_0603_1608Metric"
    # )

    # TODO: Define your nets
    # Example:
    # vcc = Net('VCC')
    # gnd = Net('GND')

    # TODO: Make connections
    # Example:
    # resistor[1] += vcc
    # resistor[2] += gnd

    pass  # Remove this when you add your code


if __name__ == '__main__':
    # Generate KiCad project when run directly
    circuit_obj = my_circuit()

    circuit_obj.generate_kicad_project(
        project_name="my_circuit",
        placement_algorithm="hierarchical",  # Use "simple" for non-hierarchical
        generate_pcb=True
    )

    print("✅ Circuit generated successfully!")
    print("📁 Open in KiCad: my_circuit/my_circuit.kicad_pro")
