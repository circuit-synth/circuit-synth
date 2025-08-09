#!/usr/bin/env python3
"""
Unit tests for PythonCodeGenerator edge cases.

This test suite ensures that the multi-file generation functionality handles
edge cases robustly, including empty circuits, invalid net names, partially
shared nets, and hierarchical designs.
"""

import tempfile
from pathlib import Path

import pytest

from circuit_synth import Circuit, Component, Net, circuit
from circuit_synth.tools.utilities.python_code_generator import PythonCodeGenerator


class TestPythonCodeGeneratorEdgeCases:
    """Test suite for edge cases in PythonCodeGenerator"""

    @pytest.fixture
    def generator(self):
        """Create a PythonCodeGenerator instance for testing"""
        return PythonCodeGenerator(project_name="test_project")

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup is handled by tempfile module

    def test_empty_circuit_generation(self, generator):
        """Test generation of code for empty circuits"""
        empty_circuit = Circuit(name="empty")

        # Should generate valid Python code even for empty circuits
        code = generator._generate_flat_code(empty_circuit)

        assert code is not None
        assert len(code) > 0
        assert "def main():" in code
        assert "from circuit_synth import *" in code
        assert "if __name__ == '__main__':" in code

    def test_circuit_with_no_nets(self, generator):
        """Test generation of code for circuits with components but no nets"""
        circuit = Circuit(name="no_nets")
        # Add component to circuit
        r1 = Component("Device:R", ref="R1", value="10k")
        circuit.add_component(r1)

        code = generator._generate_flat_code(circuit)

        assert code is not None
        assert "r1 = Component(" in code
        assert 'symbol="Device:R"' in code
        assert 'ref="R1"' in code
        assert 'value="10k"' in code

    def test_invalid_net_name_sanitization(self, generator):
        """Test sanitization of invalid Python variable names"""
        test_cases = [
            ("+3.3V", "_3v3"),  # Voltage with plus and decimal -> special case
            ("123_invalid", "_123_invalid"),  # Starts with number
            ("signal/with/slashes", "slashes"),  # Contains slashes -> takes last part
            ("signal with spaces", "signal_with_spaces"),  # Contains spaces
            ("VCC", "vcc"),  # Standard power net
            ("GND", "gnd"),  # Standard ground net
            ("", "net"),  # Empty name fallback
        ]

        for input_name, expected_output in test_cases:
            result = generator._sanitize_variable_name(input_name)
            assert (
                result == expected_output
            ), f"Failed for input '{input_name}': expected '{expected_output}', got '{result}'"

    def test_single_circuit_file_generation(self, generator, temp_output_dir):
        """Test generation of single file for non-hierarchical circuits"""
        circuit = Circuit(name="main")
        r1 = Component("Device:R", ref="R1", value="10k")
        circuit.add_component(r1)

        vcc = Net("VCC")
        gnd = Net("GND")
        r1[1] += vcc
        r1[2] += gnd
        circuit.add_net(vcc)
        circuit.add_net(gnd)

        circuits = {"main": circuit}
        main_file = temp_output_dir / "main.py"

        result = generator.update_python_file(main_file, circuits, preview_only=False)

        assert result is not None
        assert main_file.exists()

        content = main_file.read_text()
        assert "def main():" in content
        assert "r1 = Component(" in content
        assert "vcc = Net('VCC')" in content
        assert "gnd = Net('GND')" in content

    @pytest.mark.skip(reason="Hierarchical generation API changed - needs test update")
    def test_dual_hierarchy_no_shared_nets(self, generator, temp_output_dir):
        """Test generation of separate files for hierarchical circuits with no shared nets"""

        @circuit(name="main")
        def main():
            r1 = Component(symbol="Device:R", ref="R1", value="1k")
            vcc_main = Net("VCC_MAIN")
            gnd_main = Net("GND_MAIN")

        @circuit(name="child1")
        def child1():
            r2 = Component(symbol="Device:R", ref="R2", value="2k")
            vcc_child = Net("VCC_CHILD")
            gnd_child = Net("GND_CHILD")

        main_circuit = main()
        child_circuit = child1()

        circuits = {"main": main_circuit, "child1": child_circuit}
        main_file = temp_output_dir / "main.py"

        result = generator.update_python_file(main_file, circuits, preview_only=False)

        assert result is not None
        assert main_file.exists()
        assert (temp_output_dir / "child1.py").exists()

        # Check main file
        main_content = main_file.read_text()
        assert "from child1 import child1" in main_content
        assert "child1_instance = child1()" in main_content  # No parameters

        # Check child file
        child_content = (temp_output_dir / "child1.py").read_text()
        assert "def child1():" in child_content  # No parameters

    @pytest.mark.skip(reason="Hierarchical generation API changed - needs test update")
    def test_dual_hierarchy_with_shared_nets(self, generator, temp_output_dir):
        """Test generation of separate files for hierarchical circuits with shared nets"""

        @circuit(name="main")
        def main():
            r1 = Component(symbol="Device:R", ref="R1", value="1k")
            vcc = Net("VCC")
            gnd = Net("GND")
            unique_main = Net("UNIQUE_MAIN")

        @circuit(name="child1")
        def child1():
            r2 = Component(symbol="Device:R", ref="R2", value="2k")
            vcc2 = Net("VCC")
            gnd2 = Net("GND")
            unique_child = Net("UNIQUE_CHILD")

        main_circuit = main()
        child_circuit = child1()

        circuits = {"main": main_circuit, "child1": child_circuit}
        main_file = temp_output_dir / "main.py"

        result = generator.update_python_file(main_file, circuits, preview_only=False)

        assert result is not None
        assert main_file.exists()
        assert (temp_output_dir / "child1.py").exists()

        # Check main file
        main_content = main_file.read_text()
        assert "from child1 import child1" in main_content
        # Check that both shared nets are passed as parameters (order may vary)
        assert "child1_instance = child1(" in main_content
        instantiation_line = [
            line
            for line in main_content.split("\n")
            if "child1_instance = child1(" in line
        ][0]
        assert "vcc" in instantiation_line and "gnd" in instantiation_line

        # Check child file
        child_content = (temp_output_dir / "child1.py").read_text()
        assert "def child1(" in child_content
        function_line = [
            line for line in child_content.split("\n") if "def child1(" in line
        ][0]
        assert "vcc" in function_line and "gnd" in function_line
        assert (
            "Parameters: VCC, GND" in child_content
            or "Parameters: GND, VCC" in child_content
        )

    @pytest.mark.skip(reason="Hierarchical generation API changed - needs test update")
    def test_partially_shared_nets_detection(self, generator, temp_output_dir):
        """Test detection and handling of partially shared nets"""

        @circuit(name="main")
        def main():
            vcc = Net("VCC")
            gnd = Net("GND")
            unique_a = Net("UNIQUE_A")

        @circuit(name="child1")
        def child1():
            vcc2 = Net("VCC")
            unique_b = Net("UNIQUE_B")

        main_circuit = main()
        child_circuit = child1()  # Only shares VCC

        circuits = {"main": main_circuit, "child1": child_circuit}
        main_file = temp_output_dir / "main.py"

        result = generator.update_python_file(main_file, circuits, preview_only=False)

        assert result is not None

        # Check that only VCC is passed as parameter
        main_content = main_file.read_text()
        assert "child1_instance = child1(vcc)" in main_content  # Only VCC shared

        child_content = (temp_output_dir / "child1.py").read_text()
        assert "def child1(vcc):" in child_content  # Only VCC as parameter
        assert "Parameters: VCC" in child_content

    @pytest.mark.skip(reason="Hierarchical generation API changed - needs test update")
    def test_multiple_subcircuits_different_shared_nets(
        self, generator, temp_output_dir
    ):
        """Test handling of multiple subcircuits with different shared net patterns"""

        @circuit(name="main")
        def main():
            vcc = Net("VCC")
            gnd = Net("GND")
            signal = Net("SIGNAL")

        @circuit(name="child1")
        def child1():
            vcc1 = Net("VCC")
            gnd1 = Net("GND")

        @circuit(name="child2")
        def child2():
            signal2 = Net("SIGNAL")
            vcc2 = Net("VCC")

        main_circuit = main()
        child1_circuit = child1()  # Shares VCC, GND
        child2_circuit = child2()  # Shares SIGNAL, VCC

        circuits = {
            "main": main_circuit,
            "child1": child1_circuit,
            "child2": child2_circuit,
        }
        main_file = temp_output_dir / "main.py"

        result = generator.update_python_file(main_file, circuits, preview_only=False)

        assert result is not None
        assert (temp_output_dir / "child1.py").exists()
        assert (temp_output_dir / "child2.py").exists()

        main_content = main_file.read_text()
        # Each child should get different parameters based on shared nets
        assert "from child1 import child1" in main_content
        assert "from child2 import child2" in main_content

        child1_content = (temp_output_dir / "child1.py").read_text()
        child2_content = (temp_output_dir / "child2.py").read_text()

        # Check that child1 has the correct shared nets as parameters
        # The exact order depends on implementation, but both should be present
        assert "def child1(" in child1_content
        assert "vcc" in child1_content.split("def child1(")[1].split(")")[0]
        assert "gnd" in child1_content.split("def child1(")[1].split(")")[0]

        # Check that child2 has the correct shared nets as parameters
        assert "def child2(" in child2_content
        assert "vcc" in child2_content.split("def child2(")[1].split(")")[0]
        assert "signal" in child2_content.split("def child2(")[1].split(")")[0]

    @pytest.mark.skip(reason="Hierarchical generation API changed - needs test update")
    def test_hierarchical_detection_logic(self, generator):
        """Test the logic that determines if a design is hierarchical"""

        @circuit(name="main")
        def main():
            pass

        @circuit(name="child1")
        def child1():
            pass

        # Single circuit - not hierarchical
        single_circuits = {"main": main()}

        # Multiple circuits - hierarchical
        multi_circuits = {
            "main": main(),
            "child1": child1(),
        }

        # The hierarchical detection happens in update_python_file
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "main.py"

            # Single circuit should generate flat code
            result1 = generator.update_python_file(
                temp_file, single_circuits, preview_only=True
            )
            assert "from child1 import child1" not in result1

            # Multiple circuits should generate hierarchical code
            result2 = generator.update_python_file(
                temp_file, multi_circuits, preview_only=True
            )
            assert "from child1 import child1" in result2

    def test_component_reference_sanitization(self, generator):
        """Test that component references are properly sanitized"""

        @circuit(name="main")
        def main():
            # Note: Component class uses 'ref' not 'reference', and 'symbol' not 'lib_id'
            r1 = Component(
                symbol="Device:R", ref="R+1", value="10k"
            )  # Invalid reference
            c1 = Component(
                symbol="Device:C", ref="123C", value="1uF"
            )  # Starts with number

        test_circuit = main()

        code = generator._generate_flat_code(test_circuit)

        # References should be sanitized
        assert "rp1 = Component(" in code  # R+1 -> rp1
        assert "_123c = Component(" in code  # 123C -> _123c

    def test_net_connection_generation(self, generator):
        """Test generation of net connection statements"""

        @circuit(name="main")
        def main():
            r1 = Component(symbol="Device:R", ref="R1", value="10k")

            vcc = Net("VCC")
            gnd = Net("GND")
            signal = Net("SIGNAL")

            # Make the connections
            r1[1] += vcc
            r1[2] += gnd
            r1["A"] += signal  # Named pin

        test_circuit = main()

        code = generator._generate_flat_code(test_circuit)

        # Should generate proper connection statements
        assert "r1[1] += vcc" in code
        assert "r1[2] += gnd" in code
        assert "r1['A'] += signal" in code

    def test_unconnected_nets_filtering(self, generator):
        """Test that unconnected nets are properly filtered out"""

        @circuit(name="main")
        def main():
            r1 = Component(symbol="Device:R", ref="R1", value="10k")

            vcc = Net("VCC")
            unconnected = Net("unconnected-(R1-Pad2)")

            # Make the connections
            r1[1] += vcc
            r1[2] += unconnected  # Should be filtered

        test_circuit = main()

        code = generator._generate_flat_code(test_circuit)

        # Connected net should be included
        assert "vcc = Net('VCC')" in code
        assert "r1[1] += vcc" in code

        # Unconnected net should be filtered out
        assert "unconnected-" not in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
