import json
import logging  # Add logging import
import re
import unittest
from pathlib import Path
from typing import Any  # Import necessary types including Any
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)  # Get logger instance


class NetlistValidationBase(unittest.TestCase):
    """Base class for netlist validation tests with flexible validation methods."""

    def safe_extract_property(self, component_ref, property_name):
        """
        Safely extract a property from the netlist with fallback mechanisms.

        Args:
            component_ref: The component reference (e.g., "U1")
            property_name: The property name to extract (e.g., "value", "footprint")

        Returns:
            The property value if found, None otherwise
        """
        # Try direct pattern
        pattern = (
            rf'\(comp\s+\(ref\s+"{component_ref}"\).*?\({property_name}\s+"([^"]+)"\)'
        )
        match = re.search(pattern, self.netlist_content, re.DOTALL)

        if match:
            return match.group(1)

        # Try alternative patterns
        alt_pattern = rf'\(comp\s+\(ref\s+"{component_ref}"\)[^)]*\)[^(]*\({property_name}\s+"([^"]+)"\)'
        match = re.search(alt_pattern, self.netlist_content, re.DOTALL)

        if match:
            return match.group(1)

        # Try looking in fields section
        fields_pattern = rf'\(comp\s+\(ref\s+"{component_ref}"\).*?\(fields.*?\(field\s+\(name\s+"{property_name}"\)\s+"([^"]+)"\)'
        match = re.search(fields_pattern, self.netlist_content, re.DOTALL)

        if match:
            return match.group(1)

        # Try looking in libparts section
        libparts_pattern = rf'\(libpart.*?\(part.*?\(field\s+\(name\s+"{property_name}"\)\s+"([^"]+)"\)'
        match = re.search(libparts_pattern, self.netlist_content, re.DOTALL)

        if match:
            return match.group(1)

        return None  # Return None if not found

    def assert_component_property(
        self, components, ref, property_name, expected_value=None
    ):
        """
        Assert that a component has a property with an expected value (if provided).

        Args:
            components: Dictionary of components
            ref: Component reference (e.g., "U1")
            property_name: Property name to check
            expected_value: Expected value (if None, just check property exists)
        """
        self.assertIn(ref, components, f"{ref} component missing")

        if expected_value is not None:
            # Extract from netlist if needed
            if isinstance(expected_value, str) and expected_value.startswith(
                "extract:"
            ):
                property_to_extract = expected_value.split(":", 1)[1]
                extracted_value = self.safe_extract_property(ref, property_to_extract)
                if extracted_value:
                    self.assertEqual(
                        components[ref][property_name],
                        extracted_value,
                        f"{ref} {property_name} mismatch",
                    )
            else:
                self.assertEqual(
                    components[ref][property_name],
                    expected_value,
                    f"{ref} {property_name} mismatch",
                )
        else:
            # Just check property exists
            self.assertIn(
                property_name, components[ref], f"{ref} {property_name} missing"
            )

    def find_subcircuit(self, subcircuits, name):
        """
        Find a subcircuit by name with helpful error message if not found.

        Args:
            subcircuits: List of subcircuits
            name: Name of the subcircuit to find

        Returns:
            The subcircuit if found, raises AssertionError otherwise
        """
        subcircuit = next((s for s in subcircuits if s["name"] == name), None)
        self.assertIsNotNone(subcircuit, f"{name} subcircuit not found")
        return subcircuit

    def assert_net_count_range(self, nets, min_count, max_count=None, message=None):
        """
        Assert that the number of nets is within an acceptable range.

        Args:
            nets: Dictionary of nets
            min_count: Minimum acceptable number of nets
            max_count: Maximum acceptable number of nets (if None, min_count + 3)
            message: Custom error message
        """
        if max_count is None:
            max_count = min_count + 3  # Allow for some flexibility

        count = len(nets)
        if message is None:
            message = (
                f"Net count {count} outside acceptable range [{min_count}-{max_count}]"
            )

        self.assertGreaterEqual(count, min_count, message)
        self.assertLessEqual(count, max_count, message)

    # Removed check_hierarchical_net as it relied on the old Structure B format.
    # Hierarchical information is now implicitly handled by net name format and subcircuit structure.
    def check_net_nodes(
        self,
        node_list: List[Dict[str, Any]],
        component_ref: str,
        pin_number: Optional[str] = None,
    ):
        """
        Check that a list of nodes contains a node for a specific component and pin.
        This helper assumes the input JSON uses the standardized Structure A format
        for nets (`Net Name -> List of Nodes`), and this function receives the
        list of node dictionaries directly for a given net.

        Each node dictionary in the list should look like:
        {
            "component": "R1",
            "pin": {
                "number": "1",
                "name": "~",
                "type": "passive"
            }
        }

        Args:
            node_list: The list of node dictionaries for a specific net (Structure A).
            component_ref: Component reference (e.g., "R1") to check for.
            pin_number: Pin number (string, e.g., "1") to check for. If None,
                        only checks if the component is connected to the net.
        """
        nodes = node_list  # The input is already the list of nodes
        logger.debug(
            f"check_net_nodes: Checking for Comp='{component_ref}', Pin='{pin_number}' in node_list (len={len(nodes)}): {nodes[:3]}..."
        )  # Log first 3 nodes
        if pin_number is None:
            # Just check component exists in any node
            found = any(node.get("component") == component_ref for node in nodes)
            self.assertTrue(
                found, f"Component {component_ref} missing from net nodes: {nodes}"
            )
        else:
            # Check specific pin
            found = any(
                node.get("component") == component_ref
                and node.get("pin", {}).get("number")
                == str(pin_number)  # Ensure pin_number is compared as string
                for node in nodes
            )
            self.assertTrue(
                found,
                f"Component {component_ref} pin {pin_number} missing from net nodes: {nodes}",
            )
