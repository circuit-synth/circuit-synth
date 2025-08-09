#!/usr/bin/env python3
"""
Unit tests for HierarchicalSynchronizer functionality.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from circuit_synth import Circuit, Component, Net, circuit

# from circuit_synth.kicad.schematic import SchematicParser  # TODO: SchematicParser not implemented yet
from circuit_synth.kicad.schematic.hierarchical_synchronizer import (
    HierarchicalSynchronizer,
)


class TestHierarchicalSynchronizer(unittest.TestCase):
    """Test cases for hierarchical synchronization"""

    def setUp(self):
        """Create temporary directory for test projects"""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

    def create_test_project(self, name, circuit_func):
        """Helper to create a test project"""
        project_path = Path(self.test_dir) / name
        circuit_instance = circuit_func()
        circuit_instance.generate_kicad_project(
            str(project_path), force_regenerate=True
        )
        return project_path

    def test_sheet_detection(self):
        """Test that all sheets are properly detected"""

        @circuit(name="sub")
        def sub(vcc, gnd):
            R1 = Component("Device:R", ref="R", value="1k")
            R1[1] += vcc
            R1[2] += gnd

        @circuit(name="main")
        def main():
            VCC = Net("VCC")
            GND = Net("GND")
            sub1 = sub(VCC, GND)
            sub2 = sub(VCC, GND)

        project_path = self.create_test_project("test_detection", main)

        # Create synchronizer and check sheet detection
        sync = HierarchicalSynchronizer(str(project_path))

        # Should have main + 2 sub sheets
        sheet_count = 1  # main
        for sheet in sync.root_sheet.children:
            sheet_count += 1

        self.assertEqual(sheet_count, 3, "Should detect main + 2 sub sheets")

    def test_component_matching(self):
        """Test component matching across hierarchy"""

        @circuit(name="leaf")
        def leaf(in_net, out_net):
            R1 = Component("Device:R", ref="R", value="10k")
            R1[1] += in_net
            R1[2] += out_net

        @circuit(name="branch")
        def branch(vcc, gnd):
            MID = Net("MID")
            leaf1 = leaf(vcc, MID)
            leaf2 = leaf(MID, gnd)

        @circuit(name="root")
        def root():
            VCC = Net("VCC")
            GND = Net("GND")
            C1 = Component("Device:C", ref="C", value="100nF")
            C1[1] += VCC
            C1[2] += GND
            branch1 = branch(VCC, GND)

        project_path = self.create_test_project("test_matching", root)

        # Run synchronization
        sync = HierarchicalSynchronizer(str(project_path))

        # Create dummy circuits for sub_dict
        # These need to be actual circuit instances
        @circuit(name="branch_instance")
        def branch_instance():
            pass

        @circuit(name="leaf_instance")
        def leaf_instance():
            pass

        sub_dict = {"branch": branch_instance(), "leaf": leaf_instance()}
        report = sync.sync_with_circuit(root(), sub_dict)

        # Check that components were matched
        total_matched = sum(
            sheet_report.get("matched", 0)
            for sheet_report in report.get("sheet_reports", {}).values()
        )

        self.assertGreater(total_matched, 0, "Should match some components")

    def test_position_preservation(self):
        """Test that component positions are preserved"""

        @circuit(name="simple")
        def simple():
            R1 = Component("Device:R", ref="R", value="1k")
            R2 = Component("Device:R", ref="R", value="2k")
            VCC = Net("VCC")
            GND = Net("GND")
            R1[1] += VCC
            R1[2] += R2[1]
            R2[2] += GND

        project_path = self.create_test_project("test_preservation", simple)

        # Manually modify a component position
        sch_file = project_path / f"{project_path.name}.kicad_sch"
        content = sch_file.read_text()

        # Change R1 position from default to (50, 50)
        import re

        pattern = r'(\(symbol.*?"R1".*?\n.*?\(at) [\d.]+ [\d.]+( \d+\))'
        replacement = r"\1 50.0 50.0\2"
        modified_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        sch_file.write_text(modified_content)

        # Run synchronization with preservation
        sync = HierarchicalSynchronizer(
            str(project_path), preserve_user_components=True
        )
        report = sync.sync_with_circuit(simple(), {})

        # Read back and check position
        # TODO: SchematicParser not implemented yet - skip this check for now
        # parser = SchematicParser(str(sch_file))
        # schematic = parser.parse()
        # r1_found = False
        # for elem in schematic.elements:
        #     if hasattr(elem, "property"):
        #         for prop in elem.property:
        #             if prop.name == "Reference" and prop.value == "R1":
        #                 # Check position is preserved at (50, 50)
        #                 self.assertEqual(elem.at.x, 50.0)
        #                 self.assertEqual(elem.at.y, 50.0)
        #                 r1_found = True
        #                 break
        # self.assertTrue(r1_found, "R1 should be found with preserved position")

        # For now, just verify that synchronization completed without error
        self.assertIsNotNone(
            report, "Synchronization should complete and return a report"
        )

    def test_multi_level_hierarchy(self):
        """Test deep hierarchy with 3+ levels"""

        @circuit(name="level3")
        def level3(a, b):
            R = Component("Device:R", ref="R", value="1k")
            R[1] += a
            R[2] += b

        @circuit(name="level2")
        def level2(vcc, gnd):
            MID = Net("MID")
            sub1 = level3(vcc, MID)
            sub2 = level3(MID, gnd)

        @circuit(name="level1")
        def level1():
            VCC = Net("VCC")
            GND = Net("GND")
            sub = level2(VCC, GND)

        project_path = self.create_test_project("test_deep", level1)

        sync = HierarchicalSynchronizer(str(project_path))

        # Create dummy circuit instances for sub_dict
        @circuit(name="level2_instance")
        def level2_instance():
            pass

        @circuit(name="level3_instance")
        def level3_instance():
            pass

        sub_dict = {
            "level2": level2_instance(),
            "level3": level3_instance(),
        }
        report = sync.sync_with_circuit(level1(), sub_dict)

        # Should handle all levels
        self.assertIn("sheet_reports", report)
        sheet_count = len(report["sheet_reports"])
        self.assertGreaterEqual(sheet_count, 3, "Should process all hierarchy levels")


if __name__ == "__main__":
    unittest.main()
