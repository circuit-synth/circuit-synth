#!/usr/bin/env python3
"""Circuit with two resistors, then delete one."""

from circuit_synth import circuit, Component


@circuit(name="delete_test")
def delete_test():
    """Circuit with two resistors."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # This component will be deleted
    # r2 = Component(
    #     symbol="Device:R",
    #     ref="R2",
    #     value="20k",
    #     footprint="Resistor_SMD:R_0603_1608Metric"
    # )


if __name__ == "__main__":
    circuit_obj = delete_test()
    circuit_obj.generate_kicad_project(
        project_name="delete_test",
        placement_algorithm="simple",
        generate_pcb=True,
    )
