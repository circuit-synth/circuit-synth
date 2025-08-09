#!/usr/bin/env python3
"""
Test script for S-expression formatter migration using the test harness.

This script:
1. Loads reference circuits
2. Captures baseline outputs
3. Prepares for parallel testing when new formatter is ready
"""

import json
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from circuit_synth.kicad.formatter_test_harness import FormatterTestHarness


def load_reference_circuit_json():
    """Load the reference circuit JSON data."""
    project_root = Path(__file__).parent.parent.parent
    json_path = (
        project_root
        / "reference_circuit-synth"
        / "reference_generated"
        / "circuit.json"
    )

    if not json_path.exists():
        # Try alternate location
        json_path = project_root / "reference_circuit-synth" / "circuit.json"

    if json_path.exists():
        with open(json_path) as f:
            return json.load(f)
    else:
        print(f"Warning: Could not find circuit.json at {json_path}")
        return None


def test_formatter_migration_phase0():
    """Phase 0: Setup and baseline capture."""
    print("=" * 60)
    print("Phase 0: Formatter Migration - Baseline Capture")
    print("=" * 60)

    # Initialize test harness
    output_dir = (
        Path(__file__).parent.parent.parent / "test_output" / "formatter_migration"
    )
    harness = FormatterTestHarness(output_dir)

    # Test 1: Simple resistor circuit
    print("\n📝 Test 1: Simple resistor circuit")
    simple_circuit = {
        "uuid": "simple-test-001",
        "components": [
            {
                "reference": "R1",
                "lib_id": "Device:R",
                "value": "10k",
                "x": 50.8,
                "y": 63.5,
                "uuid": "r1-uuid",
            }
        ],
    }

    baseline_path = harness.capture_baseline("simple_resistor", simple_circuit)
    print(f"  ✅ Baseline captured: {baseline_path}")

    # Test 2: Multi-component circuit
    print("\n📝 Test 2: Multi-component circuit")
    multi_circuit = {
        "uuid": "multi-test-002",
        "components": [
            {
                "reference": "R1",
                "lib_id": "Device:R",
                "value": "10k",
                "x": 50.8,
                "y": 63.5,
                "uuid": "r1-uuid",
            },
            {
                "reference": "C1",
                "lib_id": "Device:C",
                "value": "100nF",
                "x": 76.2,
                "y": 63.5,
                "uuid": "c1-uuid",
            },
            {
                "reference": "U1",
                "lib_id": "MCU_Microchip_ATmega:ATmega328P-PU",
                "value": "ATmega328P",
                "x": 101.6,
                "y": 76.2,
                "uuid": "u1-uuid",
            },
        ],
    }

    baseline_path = harness.capture_baseline("multi_component", multi_circuit)
    print(f"  ✅ Baseline captured: {baseline_path}")

    # Test 3: USB-C connector (complex component)
    print("\n📝 Test 3: USB-C connector circuit")
    usb_circuit = {
        "uuid": "usb-test-003",
        "components": [
            {
                "reference": "P1",
                "lib_id": "Connector:USB_C_Plug_USB2.0",
                "value": "USB_C_Plug_USB2.0",
                "x": 58.42,
                "y": 66.04,
                "uuid": "usb-uuid",
            }
        ],
    }

    baseline_path = harness.capture_baseline("usb_connector", usb_circuit)
    print(f"  ✅ Baseline captured: {baseline_path}")

    # Test 4: Multi-unit component (LM324)
    print("\n📝 Test 4: Multi-unit LM324 op-amp")
    lm324_circuit = {
        "uuid": "lm324-test-004",
        "components": [
            {
                "reference": "U1",
                "lib_id": "Amplifier_Operational:LM324",
                "value": "LM324",
                "x": 45.72,
                "y": 58.42,
                "unit": 1,
                "uuid": "lm324-unit1",
            },
            {
                "reference": "U1",
                "lib_id": "Amplifier_Operational:LM324",
                "value": "LM324",
                "x": 76.2,
                "y": 58.42,
                "unit": 2,
                "uuid": "lm324-unit2",
            },
        ],
    }

    baseline_path = harness.capture_baseline("multi_unit_lm324", lm324_circuit)
    print(f"  ✅ Baseline captured: {baseline_path}")

    # Test 5: Hierarchical design
    print("\n📝 Test 5: Hierarchical design with sheets")
    hier_circuit = {
        "uuid": "hier-test-005",
        "components": [
            {
                "reference": "R1",
                "lib_id": "Device:R",
                "value": "10k",
                "x": 50.8,
                "y": 50.8,
                "uuid": "main-r1",
            }
        ],
        "sheets": [
            {
                "name": "child1",
                "file": "child1.kicad_sch",
                "x": 81.28,
                "y": 57.15,
                "width": 39.21,
                "height": 20.32,
                "uuid": "sheet-child1",
            }
        ],
    }

    baseline_path = harness.capture_baseline("hierarchical_design", hier_circuit)
    print(f"  ✅ Baseline captured: {baseline_path}")

    # Load and test actual reference circuit if available
    ref_circuit_data = load_reference_circuit_json()
    if ref_circuit_data:
        print("\n📝 Test 6: Actual reference circuit")
        baseline_path = harness.capture_baseline("reference_circuit", ref_circuit_data)
        print(f"  ✅ Baseline captured: {baseline_path}")

    # Generate baseline report
    print("\n📊 Generating baseline report...")
    report_path = harness.generate_report()
    print(f"  ✅ Report generated: {report_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("Phase 0 Complete: Baseline Established")
    print("=" * 60)
    print(f"Output directory: {harness.output_dir}")
    print(f"Total tests: {harness.migration_status['tests_run']}")
    print("\nNext steps:")
    print("1. Review baseline outputs in:", harness.baseline_dir)
    print("2. Implement CleanSExprFormatter")
    print("3. Run Phase 1 parallel testing")

    return harness


def test_formatter_migration_phase1():
    """Phase 1: Shadow mode - run both formatters in parallel."""
    print("=" * 60)
    print("Phase 1: Formatter Migration - Shadow Mode Testing")
    print("=" * 60)

    # Load existing harness or create new
    output_dir = (
        Path(__file__).parent.parent.parent / "test_output" / "formatter_migration"
    )
    harness = FormatterTestHarness(output_dir)

    # Update phase
    harness.migration_status["phase"] = 1

    # Run parallel tests for each baseline
    test_circuits = [
        (
            "simple_resistor",
            {
                "uuid": "simple-test-001",
                "components": [
                    {
                        "reference": "R1",
                        "lib_id": "Device:R",
                        "value": "10k",
                        "x": 50.8,
                        "y": 63.5,
                    }
                ],
            },
        ),
        (
            "multi_component",
            {
                "uuid": "multi-test-002",
                "components": [
                    {
                        "reference": "R1",
                        "lib_id": "Device:R",
                        "value": "10k",
                        "x": 50.8,
                        "y": 63.5,
                    },
                    {
                        "reference": "C1",
                        "lib_id": "Device:C",
                        "value": "100nF",
                        "x": 76.2,
                        "y": 63.5,
                    },
                ],
            },
        ),
    ]

    print("\n🔄 Running parallel tests...")
    for test_name, circuit_data in test_circuits:
        print(f"\n  Testing: {test_name}")
        result = harness.run_parallel_test(test_name, circuit_data)

        if result["identical"]:
            print(f"    ✅ Outputs identical")
        elif result["functional_equivalent"]:
            print(f"    ✅ Functionally equivalent (formatting differs)")
        else:
            print(f"    ❌ Not equivalent - review differences")

    # Generate comparison report
    print("\n📊 Generating comparison report...")
    report_path = harness.generate_report()
    print(f"  ✅ Report generated: {report_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("Phase 1 Summary")
    print("=" * 60)
    print(f"Tests run: {harness.migration_status['tests_run']}")
    print(f"Tests passed: {harness.migration_status['tests_passed']}")
    print(f"Tests failed: {harness.migration_status['tests_failed']}")

    if (
        harness.migration_status["tests_passed"]
        == harness.migration_status["tests_run"]
    ):
        print("\n✅ All tests passing! Ready for Phase 2.")
    else:
        print("\n⚠️ Some tests failing. Review before proceeding to Phase 2.")

    return harness


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--phase1":
        # Run Phase 1 (shadow mode)
        test_formatter_migration_phase1()
    else:
        # Default: Run Phase 0 (baseline capture)
        test_formatter_migration_phase0()
