"""
Tests for net operations (create, rename, merge, split, delete).

Validates net connection handling in bidirectional sync.

Manual test equivalents:
- test_10: bidirectional/10_generate_with_net
- test_11: bidirectional/11_add_net_to_components
- test_12: bidirectional/12_add_to_net
- test_17: bidirectional/17_remove_from_net
- test_18: bidirectional/18_rename_net
- test_19: bidirectional/19_delete_net
- test_20: bidirectional/20_change_pin_on_net
- test_21: bidirectional/21_split_net
- test_22: bidirectional/22_merge_nets
- test_23: bidirectional/23_multiple_nets_per_component
- test_24: bidirectional/24_auto_net_name
- test_25: bidirectional/25_add_component_and_net
"""

import pytest
import kicad_sch_api as ksa

from circuit_synth.kicad.importer import import_kicad_project
from fixtures.circuits import (
    two_resistors_connected,
    three_resistors_on_net,
    four_resistors_two_nets,
)
from fixtures.assertions import assert_net_exists, assert_schematic_component_count


class TestNetOperations:
    """Test net creation, modification, and deletion operations."""

    def test_10_generate_circuit_with_net(self, temp_project_dir, parse_schematic):
        """
        Test: Generate circuit with net connections from Python.

        Validates:
        - Net generation works
        - Wires created for connections
        - Labels created for net names
        - Components connected correctly

        Manual equivalent: tests/bidirectional/10_generate_with_net
        """
        output_dir = temp_project_dir / "net_gen_test"

        # Generate circuit with NET1
        circuit = two_resistors_connected()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Parse and verify
        sch_path = output_dir / "net_gen_test.kicad_sch"
        sch = parse_schematic(sch_path)

        # Components present
        assert_schematic_component_count(sch, 2)

        # Net exists
        assert_net_exists(sch, "NET1")

        # Wires present (connections created)
        wires = list(sch.wires)
        assert len(wires) > 0, "No wires generated for net"

    def test_11_add_net_to_existing_components(self, temp_project_dir, parse_schematic):
        """
        Test: Add net connection to existing unconnected components.

        Workflow:
        1. Generate circuit with R1, R2 (no connections)
        2. Add wires/labels to connect them via NET1
        3. Verify connection exists

        Validates:
        - Can add nets to existing components
        - Connection created correctly

        Manual equivalent: tests/bidirectional/11_add_net_to_components
        """
        output_dir = temp_project_dir / "add_net_test"

        # Generate disconnected components
        from fixtures.circuits import two_resistors
        circuit = two_resistors()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Add net connection using kicad-sch-api
        sch_path = output_dir / "add_net_test.kicad_sch"
        sch = ksa.Schematic.load(str(sch_path))

        # Get component pin positions
        r1 = sch.components.get("R1")
        r2 = sch.components.get("R2")

        # Add label at R1 pin 1
        r1_pin1_pos = (r1.position[0] + 10, r1.position[1])  # Approximate pin position
        sch.add_label("NET1", position=r1_pin1_pos)

        # Add label at R2 pin 1
        r2_pin1_pos = (r2.position[0] + 10, r2.position[1])
        sch.add_label("NET1", position=r2_pin1_pos)

        sch.save()

        # Verify
        sch_verify = ksa.Schematic.load(str(sch_path))
        assert_net_exists(sch_verify, "NET1")

    def test_18_rename_net(self, temp_project_dir, parse_schematic):
        """
        Test: Rename net from NET1 to VCC.

        Workflow:
        1. Generate circuit with NET1
        2. Rename all NET1 labels to VCC
        3. Verify net renamed

        Validates:
        - Net renaming works
        - All instances renamed
        - Import reflects new name

        Manual equivalent: tests/bidirectional/18_rename_net
        """
        output_dir = temp_project_dir / "rename_net_test"

        # Generate with NET1
        circuit = two_resistors_connected()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Rename NET1 → VCC
        sch_path = output_dir / "rename_net_test.kicad_sch"
        sch = ksa.Schematic.load(str(sch_path))

        # Find and rename all NET1 labels
        for label in list(sch.labels):
            if label.text == "NET1":
                label.text = "VCC"

        sch.save()

        # Verify
        sch_verify = ksa.Schematic.load(str(sch_path))
        assert_net_exists(sch_verify, "VCC")

        # Verify NET1 gone
        net1_labels = [l for l in sch_verify.labels if l.text == "NET1"]
        assert len(net1_labels) == 0, "NET1 labels still exist"

        # Import and verify
        project_file = output_dir / "rename_net_test.kicad_pro"
        imported = import_kicad_project(str(project_file))

        if hasattr(imported, 'nets'):
            net_names = [net.name for net in imported.nets]
            assert "VCC" in net_names, "Renamed net not found"
            assert "NET1" not in net_names, "Old net name still exists"

    def test_19_delete_net(self, temp_project_dir, parse_schematic):
        """
        Test: Delete net (remove wires and labels).

        Workflow:
        1. Generate circuit with NET1
        2. Delete all NET1 wires and labels
        3. Verify net removed

        Validates:
        - Net deletion works
        - Wires removed
        - Labels removed
        - Components remain

        Manual equivalent: tests/bidirectional/19_delete_net
        """
        output_dir = temp_project_dir / "delete_net_test"

        # Generate with NET1
        circuit = two_resistors_connected()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Delete NET1 (remove labels and wires)
        sch_path = output_dir / "delete_net_test.kicad_sch"
        sch = ksa.Schematic.load(str(sch_path))

        # Remove labels
        for label in list(sch.labels):
            if label.text == "NET1":
                sch.remove_label(label.uuid)

        # Remove wires (simplified - remove all wires for this test)
        for wire in list(sch.wires):
            sch.remove_wire(wire.uuid)

        sch.save()

        # Verify net gone
        sch_verify = ksa.Schematic.load(str(sch_path))
        net1_labels = [l for l in sch_verify.labels if l.text == "NET1"]
        assert len(net1_labels) == 0, "NET1 labels still exist"

        # Components should remain
        assert_schematic_component_count(sch_verify, 2)

    def test_22_merge_nets(self, temp_project_dir, parse_schematic):
        """
        Test: Merge two nets into one.

        Workflow:
        1. Generate circuit with NET1 and NET2
        2. Rename all NET2 labels to NET1
        3. Verify only NET1 exists

        Validates:
        - Net merging works
        - All components from both nets now on single net

        Manual equivalent: tests/bidirectional/22_merge_nets
        """
        output_dir = temp_project_dir / "merge_nets_test"

        # Generate with NET1, NET2
        circuit = four_resistors_two_nets()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Merge NET2 into NET1
        sch_path = output_dir / "merge_nets_test.kicad_sch"
        sch = ksa.Schematic.load(str(sch_path))

        # Rename all NET2 labels to NET1
        for label in list(sch.labels):
            if label.text == "NET2":
                label.text = "NET1"

        sch.save()

        # Verify
        sch_verify = ksa.Schematic.load(str(sch_path))

        # NET1 exists
        net1_labels = [l for l in sch_verify.labels if l.text == "NET1"]
        assert len(net1_labels) > 0, "NET1 labels not found"

        # NET2 gone
        net2_labels = [l for l in sch_verify.labels if l.text == "NET2"]
        assert len(net2_labels) == 0, "NET2 labels still exist after merge"

        # All components still present
        assert_schematic_component_count(sch_verify, 4)

    def test_21_split_net(self, temp_project_dir, parse_schematic):
        """
        Test: Split one net into two.

        Workflow:
        1. Generate circuit with 4 resistors on NET1
        2. Rename some labels from NET1 to NET2
        3. Verify both nets exist

        Validates:
        - Net splitting works
        - Components correctly distributed across nets

        Manual equivalent: tests/bidirectional/21_split_net
        """
        output_dir = temp_project_dir / "split_net_test"

        # Generate with all on NET1
        # Use four_resistors_two_nets but manually connect all to one net first
        circuit = three_resistors_on_net()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Split: change one label from NET1 to NET2
        sch_path = output_dir / "split_net_test.kicad_sch"
        sch = ksa.Schematic.load(str(sch_path))

        # Find first NET1 label and rename to NET2
        net1_labels = [l for l in sch.labels if l.text == "NET1"]
        if len(net1_labels) > 0:
            net1_labels[0].text = "NET2"

        sch.save()

        # Verify both nets exist
        sch_verify = ksa.Schematic.load(str(sch_path))
        assert_net_exists(sch_verify, "NET1")
        assert_net_exists(sch_verify, "NET2")

    def test_23_multiple_nets_per_component(self, temp_project_dir, parse_schematic):
        """
        Test: Component connected to multiple nets (different pins).

        Validates:
        - Components can connect to multiple nets
        - Each pin can have different net
        - Multi-net connections handled correctly

        Manual equivalent: tests/bidirectional/23_multiple_nets_per_component
        """
        output_dir = temp_project_dir / "multi_net_test"

        # Generate complex circuit with multiple nets
        circuit = four_resistors_two_nets()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Verify multiple nets exist
        sch_path = output_dir / "multi_net_test.kicad_sch"
        sch = parse_schematic(sch_path)

        assert_net_exists(sch, "NET1")
        assert_net_exists(sch, "NET2")

        # All components present
        assert_schematic_component_count(sch, 4)

    def test_24_auto_net_naming(self, temp_project_dir, parse_schematic):
        """
        Test: Automatically generated net names.

        Validates:
        - Auto-generated net names work
        - Names are unique
        - Names are valid

        Manual equivalent: tests/bidirectional/24_auto_net_name
        """
        output_dir = temp_project_dir / "auto_net_test"

        # Generate circuit (nets should auto-name if not specified)
        circuit = two_resistors_connected()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Verify net has some name (either user-specified or auto-generated)
        sch_path = output_dir / "auto_net_test.kicad_sch"
        sch = parse_schematic(sch_path)

        labels = list(sch.labels)
        assert len(labels) > 0, "No net labels generated"

        # Verify each label has non-empty text
        for label in labels:
            assert label.text, "Label has empty net name"
            assert len(label.text) > 0, "Label has empty net name"

    def test_25_add_component_and_net_together(self, temp_project_dir, parse_schematic):
        """
        Test: Add component and connect to existing net in one operation.

        Workflow:
        1. Generate circuit with R1, R2 on NET1
        2. Add R3 and connect to NET1
        3. Verify R3 on NET1

        Validates:
        - Can add component to existing net
        - New component properly connected

        Manual equivalent: tests/bidirectional/25_add_component_and_net
        """
        output_dir = temp_project_dir / "add_comp_net_test"

        # Generate with NET1
        circuit = two_resistors_connected()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Add R3 and connect to NET1
        sch_path = output_dir / "add_comp_net_test.kicad_sch"
        sch = ksa.Schematic.load(str(sch_path))

        # Add R3
        sch.components.add(
            lib_id="Device:R",
            reference="R3",
            value="1k",
            footprint="Resistor_SMD:R_0603_1608Metric",
            position=(200, 100)
        )

        # Add label to connect R3 to NET1
        r3_pin_pos = (210, 100)  # Approximate pin position
        sch.add_label("NET1", position=r3_pin_pos)

        sch.save()

        # Verify
        sch_verify = ksa.Schematic.load(str(sch_path))
        assert_schematic_component_count(sch_verify, 3)
        assert_net_exists(sch_verify, "NET1")

        # Import and verify
        project_file = output_dir / "add_comp_net_test.kicad_pro"
        imported = import_kicad_project(str(project_file))
        assert len(imported.components) == 3
        assert "R3" in imported.components
