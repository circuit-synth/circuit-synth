"""
Simple ratsnest generation - just flatten netlist connections to KiCad ratsnest format.
"""

import re
from pathlib import Path


def add_ratsnest_to_pcb(pcb_file: str, netlist_file: str) -> bool:
    """
    Import netlist connectivity into PCB file.

    KiCad generates ratsnest lines dynamically based on net connectivity,
    so we don't add explicit ratsnest tokens. Instead, we ensure the PCB
    has proper net definitions that match the netlist.
    """

    # Read netlist to extract net information
    with open(netlist_file, "r") as f:
        netlist = f.read()

    # Extract nets and their connections
    nets = {}
    net_pattern = (
        r'\(net\s+\(code\s+"(\d+)"\)\s+\(name\s+"([^"]+)"\)(.*?)(?=\(net\s+\(code|$)'
    )
    for net_code, net_name, net_content in re.findall(net_pattern, netlist, re.DOTALL):
        if net_name == "":
            continue

        # Get pads on this net
        pads = []
        for ref, pin in re.findall(
            r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', net_content
        ):
            clean_ref = ref.split("/")[-1] if "/" in ref else ref
            pads.append((clean_ref, pin))

        if pads:
            nets[net_code] = {"name": net_name, "pads": pads}

    if not nets:
        return False

    # Read PCB file
    with open(pcb_file, "r") as f:
        pcb_content = f.read()

    # Check if nets are already properly defined
    existing_nets = re.findall(r'\(net (\d+) "([^"]*)"', pcb_content)
    existing_net_dict = {code: name for code, name in existing_nets}

    # Add missing net definitions
    new_net_definitions = []
    for net_code, net_info in nets.items():
        if net_code not in existing_net_dict:
            new_net_definitions.append(f'\t(net {net_code} "{net_info["name"]}")')

    if new_net_definitions:
        # Find where to insert net definitions (after net 0)
        net_0_pos = pcb_content.find('(net 0 "")')
        if net_0_pos != -1:
            # Find end of net 0 line
            net_0_end = pcb_content.find("\n", net_0_pos)
            if net_0_end != -1:
                # Insert new net definitions
                pcb_content = (
                    pcb_content[:net_0_end]
                    + "\n"
                    + "\n".join(new_net_definitions)
                    + pcb_content[net_0_end:]
                )

        # Write updated PCB file
        with open(pcb_file, "w") as f:
            f.write(pcb_content)

    return True
