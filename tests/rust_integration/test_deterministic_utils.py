#!/usr/bin/env python3
"""
Deterministic Testing Utilities for Rust Integration TDD

This module provides utilities to handle the non-deterministic elements
we discovered in the baseline investigation, allowing us to create
reliable tests for Rust integration.

Key Functions:
- Normalize timestamps and UUIDs from outputs for comparison
- Create deterministic test fixtures
- Validate functional equivalence despite non-deterministic metadata
"""

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DeterministicTestUtils:
    """
    Utilities for deterministic testing despite non-deterministic metadata
    """

    @staticmethod
    def normalize_json_output(json_content: str) -> str:
        """
        Normalize JSON output by removing non-deterministic elements

        This handles the timestamp issue we found: "tstamps": "/root-4508312656/"
        """
        try:
            data = json.loads(json_content)

            # Recursively normalize timestamps
            normalized_data = DeterministicTestUtils._normalize_dict(data)

            # Return deterministic JSON (sorted keys for consistency)
            return json.dumps(normalized_data, sort_keys=True, indent=2)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON for normalization: {e}")
            return json_content

    @staticmethod
    def _normalize_dict(obj: Any) -> Any:
        """Recursively normalize dictionary objects"""
        if isinstance(obj, dict):
            normalized = {}
            for key, value in obj.items():
                if key == "tstamps" and isinstance(value, str):
                    # Normalize timestamp paths: "/root-4508312656/" -> "/root-TIMESTAMP/"
                    normalized[key] = re.sub(r"/root-\d+/", "/root-TIMESTAMP/", value)
                elif key.endswith("_uuid") or key == "uuid":
                    # Normalize UUIDs to fixed value
                    normalized[key] = "UUID-NORMALIZED"
                else:
                    normalized[key] = DeterministicTestUtils._normalize_dict(value)
            return normalized
        elif isinstance(obj, list):
            return [DeterministicTestUtils._normalize_dict(item) for item in obj]
        else:
            return obj

    @staticmethod
    def normalize_kicad_schematic(schematic_content: str) -> str:
        """
        Normalize KiCad schematic content by removing timestamps and UUIDs
        """
        # Remove or normalize common non-deterministic patterns
        patterns = [
            # UUIDs: (uuid "550e8400-e29b-41d4-a716-446655440000")
            (r'\(uuid "[0-9a-f-]+"\)', '(uuid "NORMALIZED-UUID")'),
            # Timestamps: (at 2023.12.25 10:30:45)
            (
                r"\(at \d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}\)",
                "(at NORMALIZED-TIMESTAMP)",
            ),
            # Version info with timestamps
            (r'\(version "\d+\.\d+\.\d+".*?\)', '(version "NORMALIZED")'),
            # Generator info with versions
            (r'\(generator "[^"]*"\)', '(generator "NORMALIZED")'),
        ]

        normalized = schematic_content
        for pattern, replacement in patterns:
            normalized = re.sub(pattern, replacement, normalized)

        return normalized

    @staticmethod
    def compare_outputs_functionally(
        output1: str, output2: str, file_type: str = "unknown"
    ) -> bool:
        """
        Compare two outputs functionally, ignoring non-deterministic metadata

        Args:
            output1: First output to compare
            output2: Second output to compare
            file_type: Type of file ("json", "kicad_sch", "netlist")

        Returns:
            True if outputs are functionally equivalent
        """
        if file_type == "json":
            norm1 = DeterministicTestUtils.normalize_json_output(output1)
            norm2 = DeterministicTestUtils.normalize_json_output(output2)
            return norm1 == norm2

        elif file_type == "kicad_sch":
            norm1 = DeterministicTestUtils.normalize_kicad_schematic(output1)
            norm2 = DeterministicTestUtils.normalize_kicad_schematic(output2)
            return norm1 == norm2

        elif file_type == "netlist":
            # Netlist files should be fully deterministic already
            return output1 == output2

        else:
            # Default: exact comparison
            return output1 == output2

    @staticmethod
    def create_functional_checksum(content: str, file_type: str = "unknown") -> str:
        """
        Create a checksum based on functional content, ignoring metadata
        """
        if file_type == "json":
            normalized = DeterministicTestUtils.normalize_json_output(content)
        elif file_type == "kicad_sch":
            normalized = DeterministicTestUtils.normalize_kicad_schematic(content)
        else:
            normalized = content

        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def validate_rust_python_equivalence(
        python_output: str,
        rust_output: str,
        file_type: str = "unknown",
        operation_name: str = "unknown",
    ) -> bool:
        """
        Validate that Rust and Python outputs are functionally equivalent

        This is the core validation function for TDD tests.
        """
        logger.info(f"🔍 Validating Rust↔Python equivalence for {operation_name}")
        logger.info(f"   📊 File type: {file_type}")
        logger.info(f"   📏 Python output: {len(python_output)} chars")
        logger.info(f"   📏 Rust output: {len(rust_output)} chars")

        # Functional comparison
        functionally_equivalent = DeterministicTestUtils.compare_outputs_functionally(
            python_output, rust_output, file_type
        )

        if functionally_equivalent:
            logger.info(f"   ✅ Functional equivalence: PASS")
        else:
            logger.error(f"   ❌ Functional equivalence: FAIL")

            # Create checksums for debugging
            python_checksum = DeterministicTestUtils.create_functional_checksum(
                python_output, file_type
            )
            rust_checksum = DeterministicTestUtils.create_functional_checksum(
                rust_output, file_type
            )

            logger.error(f"   🔐 Python checksum: {python_checksum}")
            logger.error(f"   🔐 Rust checksum: {rust_checksum}")

        return functionally_equivalent


class TDDTestFixtures:
    """
    Create deterministic test fixtures for TDD testing
    """

    @staticmethod
    def create_simple_component() -> Dict[str, Any]:
        """Create a simple component for testing"""
        return {
            "ref": "R1",
            "symbol": "Device:R",
            "value": "10K",
            "lib_id": "Device:R",
            "footprint": "Resistor_SMD:R_0603_1608Metric",
            "position": {"x": 100.0, "y": 100.0},
            "rotation": 0.0,
            "pins": [
                {
                    "number": "1",
                    "name": "~",
                    "x": -2.54,
                    "y": 0.0,
                    "orientation": 180.0,
                },
                {"number": "2", "name": "~", "x": 2.54, "y": 0.0, "orientation": 0.0},
            ],
        }

    @staticmethod
    def create_complex_component() -> Dict[str, Any]:
        """Create a complex component (MCU) for testing"""
        return {
            "ref": "U1",
            "symbol": "RF_Module:ESP32-S3-MINI-1",
            "value": "ESP32-S3-MINI-1",
            "lib_id": "RF_Module:ESP32-S3-MINI-1",
            "footprint": "RF_Module:ESP32-S2-MINI-1",
            "position": {"x": 200.0, "y": 150.0},
            "rotation": 0.0,
            "pins": [
                {
                    "number": "1",
                    "name": "GND",
                    "x": -15.24,
                    "y": 17.78,
                    "orientation": 180.0,
                },
                {
                    "number": "2",
                    "name": "3V3",
                    "x": -15.24,
                    "y": 15.24,
                    "orientation": 180.0,
                },
                {
                    "number": "3",
                    "name": "EN",
                    "x": -15.24,
                    "y": 12.70,
                    "orientation": 180.0,
                },
                # Add more pins as needed for comprehensive testing
            ],
        }

    @staticmethod
    def create_test_circuit_data() -> Dict[str, Any]:
        """Create a minimal but complete circuit for testing"""
        return {
            "name": "test_circuit",
            "description": "Deterministic test circuit for TDD",
            "components": [
                TDDTestFixtures.create_simple_component(),
            ],
            "nets": [
                {
                    "name": "VCC",
                    "connected_pins": [{"component_ref": "R1", "pin_id": "1"}],
                },
                {
                    "name": "GND",
                    "connected_pins": [{"component_ref": "R1", "pin_id": "2"}],
                },
            ],
        }


class TDDMemoryBankUpdater:
    """
    Automatically update memory bank with TDD progress
    """

    def __init__(self, memory_bank_path: Path = None):
        if memory_bank_path is None:
            memory_bank_path = (
                Path(__file__).parent.parent.parent / "memory-bank" / "progress"
            )

        self.memory_bank_path = memory_bank_path
        self.tdd_log_file = memory_bank_path / "rust-tdd-log.md"

        # Ensure directory exists
        self.memory_bank_path.mkdir(parents=True, exist_ok=True)

        # Initialize log file if it doesn't exist
        if not self.tdd_log_file.exists():
            self._initialize_tdd_log()

    def _initialize_tdd_log(self):
        """Initialize the TDD progress log"""
        with open(self.tdd_log_file, "w") as f:
            f.write("# Rust Integration TDD Progress Log\n\n")
            f.write(
                "This file tracks the Test-Driven Development progress for Rust integration.\n\n"
            )
            f.write("## Progress Log\n\n")

    def log_test_result(
        self, test_name: str, status: str, details: Optional[str] = None
    ):
        """Log a test result to the memory bank"""
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.tdd_log_file, "a") as f:
            f.write(f"- **{timestamp}**: `{test_name}` - **{status}**\n")
            if details:
                f.write(f"  - {details}\n")
            f.write("\n")

    def log_tdd_cycle(self, function_name: str, cycle_phase: str, status: str):
        """Log TDD cycle progress (RED/GREEN/REFACTOR)"""
        self.log_test_result(
            f"TDD-{function_name}-{cycle_phase}",
            status,
            f"TDD cycle {cycle_phase} phase for {function_name}",
        )

    def log_milestone(self, milestone: str, description: str):
        """Log a major milestone completion"""
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.tdd_log_file, "a") as f:
            f.write(f"## 🎯 MILESTONE: {milestone}\n")
            f.write(f"**Time**: {timestamp}  \n")
            f.write(f"**Description**: {description}\n\n")


# Global instance for easy access
memory_bank_updater = TDDMemoryBankUpdater()
