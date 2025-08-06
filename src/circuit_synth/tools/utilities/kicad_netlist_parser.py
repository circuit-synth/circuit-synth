#!/usr/bin/env python3
"""
KiCad netlist parser for extracting circuit connections.

This module handles parsing of KiCad .net files to extract component
and net connection information.
"""

import logging
import re
from pathlib import Path
from typing import List, Tuple

from circuit_synth.tools.utilities.models import Component, Net

logger = logging.getLogger(__name__)


class KiCadNetlistParser:
    """Parse KiCad netlist files to extract real connections"""

    def __init__(self):
        pass

    def parse_netlist(self, netlist_path: Path) -> Tuple[List[Component], List[Net]]:
        """Parse a KiCad .net file to extract components and nets with real connections"""
        logger.info(f"Parsing KiCad netlist: {netlist_path}")

        if not netlist_path.exists():
            logger.error(f"Netlist file not found: {netlist_path}")
            return [], []

        try:
            with open(netlist_path, "r") as f:
                content = f.read()

            # Parse S-expressions to extract components and nets
            components = self._parse_components_from_netlist(content)
            nets = self._parse_nets_from_netlist(content)

            logger.info(
                f"Parsed {len(components)} components and {len(nets)} nets from netlist"
            )

            # Debug: log netlist content if parsing fails
            if len(components) == 0 and len(nets) == 0:
                logger.warning(
                    "Netlist parsing returned no results - debugging netlist content:"
                )
                logger.debug(f"Netlist content (first 500 chars): {content[:500]}")

            return components, nets

        except Exception as e:
            logger.error(f"Failed to parse netlist {netlist_path}: {e}")
            return [], []

    def _parse_components_from_netlist(self, content: str) -> List[Component]:
        """Extract component information from netlist"""
        components = []

        # Find all component definitions in (components ...) block
        components_match = re.search(
            r"\(components(.*?)\)\s*\(libparts", content, re.DOTALL
        )
        if not components_match:
            return components

        components_block = components_match.group(1)

        # Find individual component entries - handle multi-line format
        comp_matches = re.findall(
            r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]*)"\)(.*?)(?=\(comp \(ref|\Z)',
            components_block,
            re.DOTALL,
        )

        for ref, value, comp_data in comp_matches:
            # Extract footprint
            footprint_match = re.search(r'\(footprint "([^"]*)"', comp_data)
            footprint = footprint_match.group(1) if footprint_match else ""

            # Extract libsource (lib_id)
            libsource_match = re.search(
                r'\(libsource \(lib "([^"]+)"\) \(part "([^"]+)"\)', comp_data
            )
            if libsource_match:
                lib = libsource_match.group(1)
                part = libsource_match.group(2)
                lib_id = f"{lib}:{part}"
            else:
                lib_id = "Unknown:Unknown"

            component = Component(
                reference=ref, lib_id=lib_id, value=value, footprint=footprint
            )
            components.append(component)
            logger.debug(f"Parsed component: {ref} = {lib_id} ({value})")

        return components

    def _parse_nets_from_netlist(self, content: str) -> List[Net]:
        """Extract net connections from netlist"""
        nets = []

        # Find all net definitions in (nets ...) block
        nets_match = re.search(r"\(nets(.*?)\)\s*$", content, re.DOTALL)
        if not nets_match:
            return nets

        nets_block = nets_match.group(1)

        # Find individual net entries - match actual KiCad format from the netlist
        net_matches = re.findall(
            r'\(net \(code "(\d+)"\) \(name "([^"]+)"\) \(class "[^"]*"\)(.*?)(?=\(net|\Z)',
            nets_block,
            re.DOTALL,
        )

        for code, net_name, nodes_block in net_matches:
            connections = []

            # Find all node connections in this net
            node_matches = re.findall(
                r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', nodes_block
            )

            for ref, pin in node_matches:
                connections.append((ref, pin))

            if connections:  # Only add nets that have connections
                # Clean net name - remove leading slash from hierarchical labels
                clean_net_name = net_name
                if clean_net_name.startswith("/"):
                    clean_net_name = clean_net_name[1:]

                net = Net(name=clean_net_name, connections=connections)
                nets.append(net)
                logger.debug(
                    f"Parsed net: {clean_net_name} with {len(connections)} connections"
                )

        return nets
