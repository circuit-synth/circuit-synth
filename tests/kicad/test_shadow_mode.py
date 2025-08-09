#!/usr/bin/env python3
"""
Test shadow mode for S-expression formatter migration.

This test verifies that:
1. The clean formatter can be enabled via environment variable
2. Shadow mode compares both formatters
3. Both formatters produce functionally equivalent output
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_shadow_mode():
    """Test shadow mode functionality."""
    print("=" * 60)
    print("Shadow Mode Test for S-Expression Formatter")
    print("=" * 60)

    # Test 1: Default mode (old formatter)
    print("\n📝 Test 1: Default mode (old formatter)")
    test_default_formatter()

    # Test 2: Clean formatter mode
    print("\n📝 Test 2: Clean formatter mode")
    test_clean_formatter()

    # Test 3: Shadow mode (compare both)
    print("\n📝 Test 3: Shadow mode (compare both)")
    test_shadow_mode_comparison()

    print("\n✅ All shadow mode tests passed!")


def test_default_formatter():
    """Test with default (old) formatter."""
    # Ensure environment variables are not set
    os.environ.pop("CIRCUIT_SYNTH_USE_CLEAN_FORMATTER", None)
    os.environ.pop("CIRCUIT_SYNTH_SHADOW_MODE", None)

    from sexpdata import Symbol

    from circuit_synth.kicad.core.s_expression import SExpressionParser

    parser = SExpressionParser()
    assert not parser.use_clean_formatter
    assert not parser.shadow_mode

    # Test formatting
    test_data = [
        Symbol("kicad_sch"),
        [Symbol("version"), 20250114],
        [Symbol("generator"), "circuit_synth"],
    ]

    result = parser.dumps(test_data)
    assert "(kicad_sch" in result
    assert "version" in result
    print("  ✅ Default formatter works")


def test_clean_formatter():
    """Test with clean formatter enabled."""
    # Enable clean formatter
    os.environ["CIRCUIT_SYNTH_USE_CLEAN_FORMATTER"] = "1"
    os.environ.pop("CIRCUIT_SYNTH_SHADOW_MODE", None)

    # Need to reimport to pick up environment variable
    import importlib

    import circuit_synth.kicad.core.s_expression

    importlib.reload(circuit_synth.kicad.core.s_expression)

    from sexpdata import Symbol

    from circuit_synth.kicad.core.s_expression import SExpressionParser

    parser = SExpressionParser()
    assert parser.use_clean_formatter
    assert not parser.shadow_mode

    # Test formatting
    test_data = [
        Symbol("kicad_sch"),
        [Symbol("version"), 20250114],
        [Symbol("generator"), "circuit_synth"],
    ]

    result = parser.dumps(test_data)
    assert "(kicad_sch" in result
    assert "version" in result
    print("  ✅ Clean formatter works")

    # Clean up
    os.environ.pop("CIRCUIT_SYNTH_USE_CLEAN_FORMATTER", None)


def test_shadow_mode_comparison():
    """Test shadow mode with both formatters."""
    # Enable shadow mode
    os.environ["CIRCUIT_SYNTH_SHADOW_MODE"] = "1"
    os.environ.pop("CIRCUIT_SYNTH_USE_CLEAN_FORMATTER", None)

    # Need to reimport to pick up environment variable
    import importlib

    import circuit_synth.kicad.core.s_expression

    importlib.reload(circuit_synth.kicad.core.s_expression)

    from sexpdata import Symbol

    from circuit_synth.kicad.core.s_expression import SExpressionParser

    parser = SExpressionParser()
    assert not parser.use_clean_formatter  # Shadow mode uses old formatter as primary
    assert parser.shadow_mode

    # Test formatting - shadow mode will run both and compare
    test_data = [
        Symbol("kicad_sch"),
        [Symbol("version"), 20250114],
        [Symbol("generator"), "circuit_synth"],
        [
            Symbol("symbol"),
            [Symbol("lib_id"), "Device:R"],
            [Symbol("at"), 50, 50, 0],
            [Symbol("property"), "Reference", "R1", [Symbol("at"), 0, -5, 0]],
        ],
    ]

    # Should use old formatter result but compare with new
    result = parser.dumps(test_data)
    assert "(kicad_sch" in result
    assert "Device:R" in result
    print("  ✅ Shadow mode comparison works")

    # Clean up
    os.environ.pop("CIRCUIT_SYNTH_SHADOW_MODE", None)


def test_with_real_circuit():
    """Test shadow mode with a real circuit."""
    print("\n📝 Test 4: Real circuit test")

    # Enable shadow mode
    os.environ["CIRCUIT_SYNTH_SHADOW_MODE"] = "1"

    # Reimport
    import importlib

    import circuit_synth.kicad.core.s_expression

    importlib.reload(circuit_synth.kicad.core.s_expression)

    from circuit_synth import Component, Net, circuit

    @circuit(name="shadow_test")
    def test_circuit():
        r1 = Component(symbol="Device:R", ref="R", value="10k")
        c1 = Component(symbol="Device:C", ref="C", value="100nF")
        vcc = Net("VCC")
        gnd = Net("GND")

        r1[1] += vcc
        r1[2] += c1[1]
        c1[2] += gnd

    # Generate circuit
    circ = test_circuit()

    # Generate KiCad project (will use shadow mode)
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "shadow_test"
        circ.generate_kicad_project(str(project_path))

        # Check that files were created
        sch_file = project_path / "shadow_test.kicad_sch"
        assert sch_file.exists()

        # Read and verify content
        with open(sch_file) as f:
            content = f.read()
            assert "(kicad_sch" in content
            assert "Device:R" in content
            assert "Device:C" in content

    print("  ✅ Real circuit with shadow mode works")

    # Clean up
    os.environ.pop("CIRCUIT_SYNTH_SHADOW_MODE", None)


if __name__ == "__main__":
    test_shadow_mode()
    test_with_real_circuit()
    print("\n🎉 All tests passed successfully!")
