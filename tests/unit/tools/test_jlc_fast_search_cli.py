"""
Unit tests for the jlc-fast CLI import command.

The JLCPCB lookup is mocked so the tests run without network access.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from circuit_synth.manufacturing.jlcpcb.component_import import (
    JlcPartNotFoundError,
    JlcPartSpec,
)
from circuit_synth.tools.jlc_fast_search_cli import cli

RESISTOR_SPEC = JlcPartSpec(
    lcsc_part="C25804",
    manufacturer_part="RC0603FR-0710KL",
    manufacturer="YAGEO",
    description="10K Ohm Resistor, 1%, 1/10W",
    package="0603",
    stock=956234,
    basic_part=True,
    price="$0.0030",
    symbol="Device:R",
    footprint="Resistor_SMD:R_0603_1608Metric",
    value="10K",
    ref_prefix="R",
)


class TestImportCommand(unittest.TestCase):
    """Behavior of `jlc-fast import`."""

    def setUp(self):
        self.runner = CliRunner()

    def _run(self, importer: MagicMock, args):
        """Run the CLI with a mocked importer."""
        with patch(
            "circuit_synth.tools.jlc_fast_search_cli.get_component_importer",
            return_value=importer,
        ):
            return self.runner.invoke(cli, args)

    def test_import_prints_component_definition(self):
        """A resolvable part prints its metadata and component definition."""
        importer = MagicMock()
        importer.resolve_part.return_value = RESISTOR_SPEC

        result = self._run(importer, ["import", "C25804"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Device:R", result.output)
        self.assertIn("C25804", result.output)
        importer.resolve_part.assert_called_once_with("C25804")

    def test_import_json_output_is_machine_readable(self):
        """The --json flag emits the resolved part as JSON."""
        importer = MagicMock()
        importer.resolve_part.return_value = RESISTOR_SPEC

        result = self._run(importer, ["import", "C25804", "--json"])

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["lcsc_part"], "C25804")
        self.assertEqual(payload["symbol"], "Device:R")
        self.assertEqual(payload["properties"]["JLCPCB_Part_Type"], "Basic")

    def test_import_reports_unknown_part(self):
        """An unresolvable part exits with a non zero status."""
        importer = MagicMock()
        importer.resolve_part.side_effect = JlcPartNotFoundError(
            "No JLCPCB catalog entry found for C999999"
        )

        result = self._run(importer, ["import", "C999999"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("C999999", result.output)

    def test_import_requires_symbol_when_unmapped(self):
        """A part without a symbol mapping asks for an explicit symbol."""
        importer = MagicMock()
        importer.resolve_part.return_value = JlcPartSpec(lcsc_part="C999999")

        result = self._run(importer, ["import", "C999999"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("--symbol", result.output)

    def test_import_accepts_symbol_override(self):
        """An explicit symbol override is used for code generation."""
        importer = MagicMock()
        importer.resolve_part.return_value = JlcPartSpec(lcsc_part="C999999")

        result = self._run(
            importer,
            ["import", "C999999", "--symbol", "Device:R", "--json"],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["symbol"], "Device:R")


if __name__ == "__main__":
    unittest.main()
