"""
Unit tests for KiCad CLI export methods.

Tests verify method signatures, parameter handling, and return types
without requiring actual KiCad installation.
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from circuit_synth.pcb.kicad_cli import KiCadCLI


class TestKiCadCLIExportMethods(unittest.TestCase):
    """Test suite for new export methods in KiCadCLI."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the kicad-cli path to avoid requiring actual KiCad installation
        with patch.object(KiCadCLI, "_find_kicad_cli", return_value="/usr/bin/kicad-cli"):
            self.cli = KiCadCLI()

    def test_export_schematic_pdf_exists(self):
        """Test that export_schematic_pdf method exists."""
        self.assertTrue(hasattr(self.cli, "export_schematic_pdf"))
        self.assertTrue(callable(self.cli.export_schematic_pdf))

    def test_export_bom_exists(self):
        """Test that export_bom method exists."""
        self.assertTrue(hasattr(self.cli, "export_bom"))
        self.assertTrue(callable(self.cli.export_bom))

    @patch.object(KiCadCLI, "run_command")
    def test_export_schematic_pdf_returns_path(self, mock_run):
        """Test that export_schematic_pdf returns a Path object."""
        mock_run.return_value = MagicMock(returncode=0)

        result = self.cli.export_schematic_pdf(
            schematic_file="/tmp/test.kicad_sch",
            output_path="/tmp/test.pdf"
        )

        self.assertIsInstance(result, Path)
        self.assertEqual(result, Path("/tmp/test.pdf"))

    @patch.object(KiCadCLI, "run_command")
    def test_export_schematic_pdf_default_params(self, mock_run):
        """Test export_schematic_pdf with default parameters."""
        mock_run.return_value = MagicMock(returncode=0)

        self.cli.export_schematic_pdf(
            schematic_file="/tmp/test.kicad_sch",
            output_path="/tmp/test.pdf"
        )

        # Verify run_command was called
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]

        # Check command structure
        self.assertEqual(args[0], "sch")
        self.assertEqual(args[1], "export")
        self.assertEqual(args[2], "pdf")
        self.assertIn("--output", args)

    @patch.object(KiCadCLI, "run_command")
    def test_export_schematic_pdf_all_pages_false(self, mock_run):
        """Test export_schematic_pdf with all_pages=False."""
        mock_run.return_value = MagicMock(returncode=0)

        self.cli.export_schematic_pdf(
            schematic_file="/tmp/test.kicad_sch",
            output_path="/tmp/test.pdf",
            all_pages=False
        )

        args = mock_run.call_args[0][0]
        self.assertIn("--no-all-pages", args)

    @patch.object(KiCadCLI, "run_command")
    def test_export_schematic_pdf_black_and_white(self, mock_run):
        """Test export_schematic_pdf with black_and_white=True."""
        mock_run.return_value = MagicMock(returncode=0)

        self.cli.export_schematic_pdf(
            schematic_file="/tmp/test.kicad_sch",
            output_path="/tmp/test.pdf",
            black_and_white=True
        )

        args = mock_run.call_args[0][0]
        self.assertIn("--black-and-white", args)

    @patch.object(KiCadCLI, "run_command")
    def test_export_bom_returns_path(self, mock_run):
        """Test that export_bom returns a Path object."""
        mock_run.return_value = MagicMock(returncode=0)

        result = self.cli.export_bom(
            schematic_file="/tmp/test.kicad_sch",
            output_path="/tmp/test.csv"
        )

        self.assertIsInstance(result, Path)
        self.assertEqual(result, Path("/tmp/test.csv"))

    @patch.object(KiCadCLI, "run_command")
    def test_export_bom_default_format(self, mock_run):
        """Test export_bom with default CSV format."""
        mock_run.return_value = MagicMock(returncode=0)

        self.cli.export_bom(
            schematic_file="/tmp/test.kicad_sch",
            output_path="/tmp/test.csv"
        )

        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "sch")
        self.assertEqual(args[1], "export")
        self.assertEqual(args[2], "bom")
        self.assertIn("--format", args)
        format_idx = args.index("--format")
        self.assertEqual(args[format_idx + 1], "csv")

    @patch.object(KiCadCLI, "run_command")
    def test_export_bom_all_formats(self, mock_run):
        """Test export_bom with all supported formats."""
        mock_run.return_value = MagicMock(returncode=0)

        formats = ["csv", "tsv", "txt", "json", "xml"]
        for fmt in formats:
            with self.subTest(format=fmt):
                self.cli.export_bom(
                    schematic_file="/tmp/test.kicad_sch",
                    output_path=f"/tmp/test.{fmt}",
                    format=fmt
                )

                args = mock_run.call_args[0][0]
                format_idx = args.index("--format")
                self.assertEqual(args[format_idx + 1], fmt)

    def test_export_bom_invalid_format(self):
        """Test export_bom raises ValueError for unsupported format."""
        with self.assertRaises(ValueError) as context:
            self.cli.export_bom(
                schematic_file="/tmp/test.kicad_sch",
                output_path="/tmp/test.xyz",
                format="xyz"
            )

        self.assertIn("Unsupported format", str(context.exception))
        self.assertIn("xyz", str(context.exception))

    @patch.object(KiCadCLI, "run_command")
    def test_export_schematic_pdf_accepts_path_objects(self, mock_run):
        """Test that export_schematic_pdf accepts Path objects."""
        mock_run.return_value = MagicMock(returncode=0)

        result = self.cli.export_schematic_pdf(
            schematic_file=Path("/tmp/test.kicad_sch"),
            output_path=Path("/tmp/test.pdf")
        )

        self.assertIsInstance(result, Path)

    @patch.object(KiCadCLI, "run_command")
    def test_export_bom_accepts_path_objects(self, mock_run):
        """Test that export_bom accepts Path objects."""
        mock_run.return_value = MagicMock(returncode=0)

        result = self.cli.export_bom(
            schematic_file=Path("/tmp/test.kicad_sch"),
            output_path=Path("/tmp/test.csv")
        )

        self.assertIsInstance(result, Path)


if __name__ == "__main__":
    unittest.main()
