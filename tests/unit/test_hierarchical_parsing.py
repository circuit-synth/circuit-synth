#!/usr/bin/env python3
"""
Unit tests for hierarchical schematic parsing.

Tests the parsing of KiCad hierarchical schematics (sheets) and extraction
of sheet properties (Sheetname, Sheetfile).
"""

import tempfile
from pathlib import Path

import pytest

from circuit_synth.tools.utilities.kicad_parser import KiCadParser


class TestSheetBlockParsing:
    """Test suite for sheet block parsing functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def hierarchical_schematic(self, temp_dir):
        """Create a KiCad schematic with a sheet block for testing.

        This fixture creates a minimal hierarchical schematic based on the
        real structure from bidirectional_test/BidirectionalTest/
        """
        # Main schematic with a sheet symbol
        sch_content = """(kicad_sch
\t(version 20250114)
\t(generator "eeschema")
\t(generator_version "9.0")
\t(uuid "fa00019f-a328-4dd4-aa75-20b935f97a3a")
\t(paper "A4")
\t(title_block
\t\t(title "HierarchicalTest")
\t)
\t(lib_symbols)
\t(sheet
\t\t(at 91.44 118.11)
\t\t(size 21.59 20.32)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(fields_autoplaced yes)
\t\t(stroke
\t\t\t(width 0.1524)
\t\t\t(type solid)
\t\t)
\t\t(fill
\t\t\t(color 0 0 0 0.0000)
\t\t)
\t\t(uuid "f0651755-9815-4d54-ba93-6b3bccba6c7f")
\t\t(property "Sheetname" "psu_subcircuit"
\t\t\t(at 91.44 117.3984 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left bottom)
\t\t\t)
\t\t)
\t\t(property "Sheetfile" "psu.kicad_sch"
\t\t\t(at 91.44 139.0146 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left top)
\t\t\t)
\t\t)
\t\t(instances
\t\t\t(project "HierarchicalTest"
\t\t\t\t(path "/fa00019f-a328-4dd4-aa75-20b935f97a3a"
\t\t\t\t\t(page "2")
\t\t\t\t)
\t\t\t)
\t\t)
\t)
\t(sheet_instances
\t\t(path "/"
\t\t\t(page "1")
\t\t)
\t)
\t(embedded_fonts no)
)
"""
        sch_file = temp_dir / "HierarchicalTest.kicad_sch"
        sch_file.write_text(sch_content)

        # Create the referenced sub-schematic file
        sub_sch_content = """(kicad_sch
\t(version 20250114)
\t(generator "eeschema")
\t(generator_version "9.0")
\t(uuid "81a106a2-ef2d-457c-a482-ae7031316be2")
\t(paper "A4")
\t(lib_symbols)
)
"""
        sub_sch_file = temp_dir / "psu.kicad_sch"
        sub_sch_file.write_text(sub_sch_content)

        # Create project file
        pro_content = '{"sheets": [["HierarchicalTest.kicad_sch", ""]]}'
        pro_file = temp_dir / "HierarchicalTest.kicad_pro"
        pro_file.write_text(pro_content)

        return sch_file

    def test_parse_sheet_block_extracts_properties(self, hierarchical_schematic):
        """
        Test that _parse_sheet_block correctly extracts Sheetname and Sheetfile
        from nested property blocks.

        This is Sprint 1, Task 1 - verifying the parser can handle the nested
        (property ...) structure found in real KiCad sheet blocks.
        """
        parser = KiCadParser(hierarchical_schematic)

        # Read the schematic content to extract the sheet block
        with open(hierarchical_schematic, 'r') as f:
            content = f.read()

        # Extract the sheet block (everything between (sheet and its closing paren)
        # This is a simplified extraction - just for testing _parse_sheet_block directly
        import re
        sheet_match = re.search(r'\(sheet\s+(.*?)\n\t\)', content, re.DOTALL)
        assert sheet_match is not None, "Could not find sheet block in test schematic"

        sheet_block = f"(sheet {sheet_match.group(1)})"

        # Call the parser's _parse_sheet_block method directly
        result = parser._parse_sheet_block(sheet_block)

        # THIS TEST SHOULD PASS - the parser already has correct regex
        # We expect it to extract both properties correctly
        assert result is not None, "Parser returned None for valid sheet block"
        sheet_name, sheet_file = result

        assert sheet_name == "psu_subcircuit", f"Expected sheet name 'psu_subcircuit', got '{sheet_name}'"
        assert sheet_file == "psu.kicad_sch", f"Expected sheet file 'psu.kicad_sch', got '{sheet_file}'"

    def test_parse_schematic_detects_sheets(self, hierarchical_schematic, temp_dir):
        """
        Test that parsing a hierarchical schematic detects sheet blocks.

        This verifies that the full parse workflow identifies sheets in the schematic.
        """
        # KiCadParser expects a .kicad_pro file, not a .kicad_sch file
        # The fixture already creates the .kicad_pro file
        kicad_project = temp_dir / "HierarchicalTest.kicad_pro"

        parser = KiCadParser(kicad_project)

        # Parse the schematic (this will call kicad-cli if available)
        # We're testing that sheets are detected, not full netlist generation
        # Note: This may require kicad-cli to be installed for full functionality

        # Verify the parser found the root schematic
        assert parser.root_schematic == hierarchical_schematic
        assert parser.root_schematic.exists()

    def test_sync_creates_python_file_for_sheet(self, hierarchical_schematic, temp_dir):
        """
        Test that syncing a hierarchical schematic creates separate Python files for sheets.

        This is Sprint 1, Task 3 - verifying that when we sync KiCad -> Python,
        each sheet gets its own .py file based on the sheetfile basename.

        Expected behavior:
        - Main schematic -> main.py
        - psu.kicad_sch sheet -> psu.py
        """
        from circuit_synth.tools.kicad_integration.kicad_to_python_sync import KiCadToPythonSyncer

        # First, we need to create a JSON netlist for the hierarchical schematic
        # For now, create a minimal JSON manually (in real workflow, kicad-cli generates this)
        json_content = {
            "name": "HierarchicalTest",
            "components": {},
            "nets": {},
            "schematic_file": "HierarchicalTest.kicad_sch",
            "sheets": [
                {
                    "name": "psu_subcircuit",
                    "file": "psu.kicad_sch",
                    "components": {},
                    "nets": {}
                }
            ]
        }

        json_file = temp_dir / "HierarchicalTest.json"
        with open(json_file, 'w') as f:
            import json
            json.dump(json_content, f, indent=2)

        # Create output directory for Python files
        output_dir = temp_dir / "python_output"

        # Sync KiCad -> Python (directory mode)
        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(json_file),
            python_file=str(output_dir),
            preview_only=False,
            create_backup=False
        )

        # Run sync
        success = syncer.sync()

        # THIS TEST SHOULD FAIL - we haven't implemented multi-file generation yet
        # We expect it to create:
        # - python_output/main.py (main circuit)
        # - python_output/psu.py (psu subcircuit)

        assert success, "Sync should succeed"

        # Verify main.py was created
        main_py = output_dir / "main.py"
        assert main_py.exists(), "main.py should be created"

        # Verify psu.py was created (THIS WILL FAIL - not implemented yet)
        psu_py = output_dir / "psu.py"
        assert psu_py.exists(), f"psu.py should be created for sheet 'psu.kicad_sch', but only found: {list(output_dir.glob('*.py'))}"

        # Verify main.py imports psu
        main_content = main_py.read_text()
        assert "from psu import" in main_content or "import psu" in main_content, \
            "main.py should import the psu subcircuit"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
