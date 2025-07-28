"""
Reference Manager for KiCad Schematic API.

Manages component reference designators, ensuring uniqueness and following
standard naming conventions for different component types.
"""

import logging
import re
from collections import defaultdict
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ReferenceManager:
    """
    Manages component reference designators.

    This class ensures that all component references are unique and follow
    standard naming conventions. It can generate new references automatically
    or validate user-provided references.
    """

    # Standard reference prefixes mapped to component patterns
    REFERENCE_PREFIX_MAP = {
        # Passive components
        "Device:R": "R",  # Resistors
        "Device:C": "C",  # Capacitors
        "Device:L": "L",  # Inductors
        "Device:D": "D",  # Diodes
        "Device:LED": "D",  # LEDs
        "Device:Crystal": "Y",  # Crystals
        "Device:Resonator": "Y",  # Resonators
        "Device:Ferrite": "FB",  # Ferrite beads
        "Device:Fuse": "F",  # Fuses
        "Device:Varistor": "RV",  # Varistors
        "Device:Thermistor": "TH",  # Thermistors
        "Device:Transformer": "T",  # Transformers
        # Active components
        "Device:Q_": "Q",  # Transistors (BJT, FET, etc.)
        "Transistor_": "Q",  # Transistor library
        "Diode:": "D",  # Diode library
        # Integrated circuits
        "Amplifier_": "U",  # Amplifiers
        "MCU_": "U",  # Microcontrollers
        "Memory_": "U",  # Memory chips
        "Interface_": "U",  # Interface ICs
        "Logic_": "U",  # Logic gates
        "Analog:": "U",  # Analog ICs
        "Regulator_": "U",  # Voltage regulators
        "Driver_": "U",  # Driver ICs
        "Sensor_": "U",  # Sensor ICs
        # Connectors and mechanical
        "Connector": "J",  # Connectors
        "Switch": "SW",  # Switches
        "Relay": "K",  # Relays
        "Motor": "M",  # Motors
        "Battery": "BT",  # Batteries
        "Jumper": "JP",  # Jumpers
        # Power
        "Power:": "PWR",  # Power symbols (special case)
        "power:": "PWR",  # Power symbols (lowercase variant)
        # Default
        "": "U",  # Default for unknown components
    }

    def __init__(self):
        """Initialize the reference manager."""
        self.used_references: Set[str] = set()
        self.reference_counters: Dict[str, int] = defaultdict(int)
        self._prefix_cache: Dict[str, str] = {}

    def add_existing_references(self, references: List[str]) -> None:
        """
        Add existing references from a schematic to the manager.

        Args:
            references: List of existing reference designators
        """
        for ref in references:
            if ref and not ref.endswith("?"):  # Ignore unassigned references
                self.used_references.add(ref)
                # Update counter based on existing references
                prefix, number = self._split_reference(ref)
                if prefix and number is not None:
                    self.reference_counters[prefix] = max(
                        self.reference_counters[prefix], number
                    )

    def generate_reference(self, lib_id: str, preferred: Optional[str] = None) -> str:
        """
        Generate a unique reference designator.

        Args:
            lib_id: The library ID of the component (e.g., "Device:R")
            preferred: Optional preferred reference to use if available

        Returns:
            A unique reference designator

        Raises:
            ValueError: If the preferred reference is invalid
        """
        # Try to use preferred reference if provided
        if preferred:
            if self.is_reference_available(preferred):
                self.used_references.add(preferred)
                self._update_counter_from_reference(preferred)
                return preferred
            else:
                logger.warning(f"Preferred reference '{preferred}' is already in use")

        # Generate new reference
        prefix = self._get_reference_prefix(lib_id)
        counter = self.reference_counters[prefix] + 1

        # Find next available number
        while f"{prefix}{counter}" in self.used_references:
            counter += 1

        reference = f"{prefix}{counter}"
        self.used_references.add(reference)
        self.reference_counters[prefix] = counter

        logger.debug(f"Generated reference '{reference}' for lib_id '{lib_id}'")
        return reference

    def is_reference_available(self, reference: str) -> bool:
        """
        Check if a reference is available for use.

        Args:
            reference: The reference to check

        Returns:
            True if the reference is available, False otherwise
        """
        return reference not in self.used_references and self._is_valid_reference(
            reference
        )

    def release_reference(self, reference: str) -> None:
        """
        Release a reference so it can be reused.

        Args:
            reference: The reference to release
        """
        if reference in self.used_references:
            self.used_references.remove(reference)
            logger.debug(f"Released reference '{reference}'")

    def update_reference(self, old_reference: str, new_reference: str) -> bool:
        """
        Update a reference from old to new.

        Args:
            old_reference: The current reference
            new_reference: The new reference to use

        Returns:
            True if successful, False if new reference is not available
        """
        if new_reference in self.used_references and new_reference != old_reference:
            return False

        if not self._is_valid_reference(new_reference):
            return False

        if old_reference in self.used_references:
            self.used_references.remove(old_reference)

        self.used_references.add(new_reference)
        self._update_counter_from_reference(new_reference)

        return True

    def get_next_reference(self, prefix: str) -> str:
        """
        Get the next available reference for a given prefix.

        Args:
            prefix: The reference prefix (e.g., "R", "C", "U")

        Returns:
            The next available reference
        """
        counter = self.reference_counters[prefix] + 1

        while f"{prefix}{counter}" in self.used_references:
            counter += 1

        return f"{prefix}{counter}"

    def _get_reference_prefix(self, lib_id: str) -> str:
        """
        Determine the reference prefix for a library ID.

        Args:
            lib_id: The library ID (e.g., "Device:R")

        Returns:
            The appropriate reference prefix
        """
        # Check cache first
        if lib_id in self._prefix_cache:
            return self._prefix_cache[lib_id]

        # Check exact matches first
        if lib_id in self.REFERENCE_PREFIX_MAP:
            prefix = self.REFERENCE_PREFIX_MAP[lib_id]
            self._prefix_cache[lib_id] = prefix
            return prefix

        # Check pattern matches
        for pattern, prefix in self.REFERENCE_PREFIX_MAP.items():
            if pattern and lib_id.startswith(pattern):
                self._prefix_cache[lib_id] = prefix
                return prefix

        # Default to "U" for unknown components
        logger.warning(f"Unknown lib_id '{lib_id}', using default prefix 'U'")
        self._prefix_cache[lib_id] = "U"
        return "U"

    def _split_reference(self, reference: str) -> tuple[str, Optional[int]]:
        """
        Split a reference into prefix and number.

        Args:
            reference: The reference to split (e.g., "R1", "U10")

        Returns:
            Tuple of (prefix, number) or (reference, None) if no number
        """
        match = re.match(r"^([A-Z]+)(\d+)$", reference)
        if match:
            return match.group(1), int(match.group(2))
        return reference, None

    def _is_valid_reference(self, reference: str) -> bool:
        """
        Check if a reference follows valid format.

        Args:
            reference: The reference to validate

        Returns:
            True if valid, False otherwise
        """
        # Valid reference format: one or more uppercase letters followed by digits
        return bool(re.match(r"^[A-Z]+\d+$", reference))

    def _update_counter_from_reference(self, reference: str) -> None:
        """
        Update the counter based on a reference.

        Args:
            reference: The reference to process
        """
        prefix, number = self._split_reference(reference)
        if prefix and number is not None:
            self.reference_counters[prefix] = max(
                self.reference_counters[prefix], number
            )

    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about reference usage.

        Returns:
            Dictionary mapping prefixes to counts
        """
        stats = {}
        for ref in self.used_references:
            prefix, _ = self._split_reference(ref)
            if prefix:
                stats[prefix] = stats.get(prefix, 0) + 1
        return stats

    def clear(self) -> None:
        """Clear all stored references and counters."""
        self.used_references.clear()
        self.reference_counters.clear()
        self._prefix_cache.clear()
