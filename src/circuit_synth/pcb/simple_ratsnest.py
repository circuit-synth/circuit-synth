"""
Simple ratsnest generation - just flatten netlist connections to KiCad ratsnest format.
"""

import re
from pathlib import Path


def add_ratsnest_to_pcb(pcb_file: str, netlist_file: str) -> bool:
    """Add ratsnest entries from netlist to PCB file."""

    # Read netlist
    with open(netlist_file, "r") as f:
        netlist = f.read()

    # Extract connections
    connections = []
    net_pattern = (
        r'\(net\s+\(code\s+"\d+"\)\s+\(name\s+"([^"]+)"\)(.*?)(?=\(net\s+\(code|$)'
    )
    for net_name, net_content in re.findall(net_pattern, netlist, re.DOTALL):
        if net_name == "":
            continue

        # Get pads on this net
        pads = []
        for ref, pin in re.findall(
            r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', net_content
        ):
            clean_ref = ref.split("/")[-1] if "/" in ref else ref
            pads.append((clean_ref, pin))

        # Connect first pad to all others
        if len(pads) > 1:
            first_ref, first_pin = pads[0]
            for ref, pin in pads[1:]:
                connections.append(
                    f'  (ratsnest (net "{net_name}") (pad "{first_ref}" "{first_pin}") (pad "{ref}" "{pin}"))'
                )

    if not connections:
        return False

    # Add to PCB file
    with open(pcb_file, "r") as f:
        pcb_content = f.read()

    # Insert before final closing paren
    insert_pos = pcb_content.rfind(")")
    new_content = (
        pcb_content[:insert_pos]
        + "\n"
        + "\n".join(connections)
        + "\n"
        + pcb_content[insert_pos:]
    )

    with open(pcb_file, "w") as f:
        f.write(new_content)

    return True
