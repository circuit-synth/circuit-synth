# tests/unit/io/test_json_loader.py

import shutil
import unittest

import pytest

from circuit_synth.core.exception import LibraryNotFound
from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache


class TestKicadSymbolCache(unittest.TestCase):
    """Test the new SymbolLibCache functionality for loading KiCad symbols."""

    def setUp(self):
        # Clear cache before each test
        cache_dir = SymbolLibCache._get_cache_dir()
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        SymbolLibCache._library_data.clear()
        SymbolLibCache._symbol_index.clear()
        SymbolLibCache._library_index.clear()
        SymbolLibCache._index_built = False

    def test_basic_resistor(self):
        """Test loading a basic resistor symbol (Device:R)"""
        data = SymbolLibCache.get_symbol_data("Device:R")

        # Check pin count
        self.assertEqual(len(data["pins"]), 2, "Expected 2 pins on Device:R")

        # Check description (optional for minimal test symbols)
        description = data.get("description", "")
        if description:
            self.assertIn(
                "Resistor", description, "Expected 'Resistor' in device description"
            )

        # Not a power symbol
        self.assertFalse(data["is_power"], "Resistor is not a power symbol")

    def test_resistor_network(self):
        """Test loading a complex resistor network symbol"""
        data = SymbolLibCache.get_symbol_data("Device:R_Network12_Split")

        # Check pin count
        self.assertEqual(len(data["pins"]), 13, "R_Network12_Split should have 13 pins")

        # Check description
        self.assertIn(
            "network",
            data.get("description", "").lower(),
            "Expected 'network' in description",
        )

    def test_power_symbols(self):
        """Test loading power symbols like GND and +3V3"""
        # Test GND symbol
        gnd_data = SymbolLibCache.get_symbol_data("power:GND")
        self.assertTrue(gnd_data["is_power"], "GND should be marked as power")
        self.assertEqual(len(gnd_data["pins"]), 1, "GND typically has 1 pin")

        # Test +3V3 symbol
        v3_data = SymbolLibCache.get_symbol_data("power:+3V3")
        self.assertTrue(v3_data["is_power"], "+3V3 is a power symbol")
        self.assertEqual(len(v3_data["pins"]), 1, "+3V3 typically has 1 pin")

    def test_linear_regulator_inheritance(self):
        """Test that inherited symbols maintain consistent structure"""
        parent_data = SymbolLibCache.get_symbol_data("Regulator_Linear:AP1117-15")
        child_data = SymbolLibCache.get_symbol_data("Regulator_Linear:AMS1117-3.3")

        # Check pin count consistency
        self.assertEqual(
            len(parent_data["pins"]),
            len(child_data["pins"]),
            "Child regulator should have same pin count as parent",
        )

    def test_symbol_cache(self):
        """Test that the caching mechanism works"""
        # First load should parse the file
        r1 = SymbolLibCache.get_symbol_data("Device:R")

        # Second load should use cache
        r2 = SymbolLibCache.get_symbol_data("Device:R")

        # Both should be identical
        self.assertEqual(
            r1["pins"], r2["pins"], "Cached symbol data should be identical"
        )

    def test_invalid_symbol(self):
        """Test handling of invalid symbol names"""
        with self.assertRaises(ValueError):
            SymbolLibCache.get_symbol_data("InvalidSymbol")  # Missing colon

        with self.assertRaises((FileNotFoundError, LibraryNotFound)):
            SymbolLibCache.get_symbol_data("NonExistent:Symbol")

    def tearDown(self):
        # Clean up after each test
        cache_dir = SymbolLibCache._get_cache_dir()
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
