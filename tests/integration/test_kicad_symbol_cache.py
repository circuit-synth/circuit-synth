"""
Unit tests for the KiCad Symbol Cache system.

Tests the symbol library caching, tier-based search, and symbol lookup functionality.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache


class TestSymbolLibCache:
    """Test the SymbolLibCache functionality."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_kicad_env(self, monkeypatch, temp_cache_dir):
        """Mock KiCad environment variables."""
        # Set up a fake KiCad symbol directory
        fake_kicad_dir = temp_cache_dir / "kicad_symbols"
        fake_kicad_dir.mkdir()

        # Create some fake .kicad_sym files
        device_lib = fake_kicad_dir / "Device.kicad_sym"
        device_lib.write_text(
            "(kicad_symbol_lib (version 20211014) (generator kicad_symbol_editor))"
        )

        power_lib = fake_kicad_dir / "power.kicad_sym"
        power_lib.write_text(
            "(kicad_symbol_lib (version 20211014) (generator kicad_symbol_editor))"
        )

        # Set environment variable
        monkeypatch.setenv("KICAD_SYMBOL_DIR", str(fake_kicad_dir))
        monkeypatch.setenv("CIRCUIT_SYNTH_CACHE_DIR", str(temp_cache_dir / "cache"))

        # Clear singleton state
        SymbolLibCache._instance = None
        SymbolLibCache._initialized = False
        SymbolLibCache._library_data.clear()
        SymbolLibCache._symbol_index.clear()
        SymbolLibCache._library_index.clear()
        SymbolLibCache._index_built = False

        yield fake_kicad_dir

    def test_singleton_pattern(self, mock_kicad_env):
        """Test that SymbolLibCache follows singleton pattern."""
        # Multiple calls should return the same instance
        cache1 = SymbolLibCache()
        cache2 = SymbolLibCache()
        assert cache1 is cache2

    def test_cache_directory_creation(self, mock_kicad_env):
        """Test that cache directory is created."""
        cache_dir = SymbolLibCache._get_cache_dir()
        assert cache_dir.exists()
        assert cache_dir.is_dir()

    @patch("circuit_synth.kicad.kicad_symbol_cache.parse_kicad_sym_file")
    def test_get_symbol_data(self, mock_parse, mock_kicad_env):
        """Test retrieving symbol data."""
        # Mock the parser to return symbol data
        mock_parse.return_value = {
            "symbols": {
                "R": {
                    "name": "R",
                    "pins": [
                        {"number": "1", "name": "~"},
                        {"number": "2", "name": "~"},
                    ],
                    "properties": {"Reference": "R", "Value": "R"},
                }
            }
        }

        # Get symbol data
        symbol_data = SymbolLibCache.get_symbol_data("Device:R")

        assert symbol_data is not None
        assert symbol_data["name"] == "R"
        assert len(symbol_data["pins"]) == 2
        assert "properties" in symbol_data

    @patch("circuit_synth.kicad.kicad_symbol_cache.parse_kicad_sym_file")
    def test_get_symbol_data_by_name(self, mock_parse, mock_kicad_env):
        """Test retrieving symbol data by name only."""
        # Mock the parser
        mock_parse.return_value = {
            "symbols": {
                "C": {
                    "name": "C",
                    "pins": [
                        {"number": "1", "name": "~"},
                        {"number": "2", "name": "~"},
                    ],
                    "properties": {"Reference": "C", "Value": "C"},
                }
            }
        }

        # Mock the symbol index to find the symbol
        SymbolLibCache._symbol_index["C"] = {
            "lib_name": "Device",
            "lib_path": mock_kicad_env / "Device.kicad_sym",
        }
        SymbolLibCache._index_built = True

        # Get symbol data by name only
        symbol_data = SymbolLibCache.get_symbol_data_by_name("C")

        assert symbol_data is not None
        assert symbol_data["name"] == "C"

    def test_find_symbol_library(self, mock_kicad_env):
        """Test finding which library contains a symbol."""
        # Build a mock symbol index
        SymbolLibCache._symbol_index = {
            "R": {
                "lib_name": "Device",
                "lib_path": mock_kicad_env / "Device.kicad_sym",
            },
            "C": {
                "lib_name": "Device",
                "lib_path": mock_kicad_env / "Device.kicad_sym",
            },
            "VCC": {
                "lib_name": "power",
                "lib_path": mock_kicad_env / "power.kicad_sym",
            },
            "GND": {
                "lib_name": "power",
                "lib_path": mock_kicad_env / "power.kicad_sym",
            },
        }
        SymbolLibCache._index_built = True

        # Test finding libraries
        assert SymbolLibCache.find_symbol_library("R") == "Device"
        assert SymbolLibCache.find_symbol_library("VCC") == "power"
        assert SymbolLibCache.find_symbol_library("NonExistent") is None

    def test_cache_file_operations(self, mock_kicad_env):
        """Test cache file reading and writing."""
        cache_dir = SymbolLibCache._get_cache_dir()

        # Create a test cache file
        test_cache_data = {
            "file_hash": "test_hash",
            "cache_time": 1234567890,
            "symbols": {"TestSymbol": {"name": "TestSymbol", "pins": []}},
        }

        test_cache_file = cache_dir / "test_lib_12345678.json"
        with open(test_cache_file, "w") as f:
            json.dump(test_cache_data, f)

        # Verify file exists and can be read
        assert test_cache_file.exists()
        with open(test_cache_file) as f:
            loaded_data = json.load(f)
        assert loaded_data["file_hash"] == "test_hash"
        assert "TestSymbol" in loaded_data["symbols"]

    def test_library_categorization(self, mock_kicad_env):
        """Test the library categorization for tier-based search."""
        # Build categorization
        SymbolLibCache._library_categories = {
            "Device": "passive_components",
            "power": "power_symbols",
            "Connector": "connectors",
            "MCU_ST_STM32": "microcontrollers",
        }

        # Test category lookup
        assert SymbolLibCache._library_categories.get("Device") == "passive_components"
        assert SymbolLibCache._library_categories.get("power") == "power_symbols"
        assert SymbolLibCache._library_categories.get("Unknown") is None

    def test_error_handling_missing_symbol(self, mock_kicad_env):
        """Test error handling when symbol is not found."""
        with pytest.raises(FileNotFoundError):
            SymbolLibCache.get_symbol_data("NonExistent:Symbol")

    def test_error_handling_invalid_format(self, mock_kicad_env):
        """Test error handling for invalid symbol ID format."""
        with pytest.raises(ValueError) as exc_info:
            SymbolLibCache.get_symbol_data("InvalidFormat")

        assert "Invalid symbol_id format" in str(exc_info.value)

    @patch("circuit_synth.kicad.kicad_symbol_cache.parse_kicad_sym_file")
    def test_cache_expiration(self, mock_parse, mock_kicad_env):
        """Test cache expiration logic."""
        # Test expired cache detection
        assert SymbolLibCache._is_cache_expired(0, 24) is True  # Very old cache

        import time

        current_time = time.time()
        assert (
            SymbolLibCache._is_cache_expired(current_time - 3600, 2) is False
        )  # 1 hour old, 2 hour TTL
        assert (
            SymbolLibCache._is_cache_expired(current_time - 7200, 1) is True
        )  # 2 hours old, 1 hour TTL

    def test_multi_path_support(self, monkeypatch, temp_cache_dir):
        """Test support for multiple KiCad symbol directories."""
        # Create multiple symbol directories
        dir1 = temp_cache_dir / "symbols1"
        dir2 = temp_cache_dir / "symbols2"
        dir1.mkdir()
        dir2.mkdir()

        # Create symbol files in each
        (dir1 / "Custom1.kicad_sym").write_text("(kicad_symbol_lib)")
        (dir2 / "Custom2.kicad_sym").write_text("(kicad_symbol_lib)")

        # Set multiple paths (colon-separated on Unix)
        monkeypatch.setenv("KICAD_SYMBOL_DIR", f"{dir1}:{dir2}")
        monkeypatch.setenv("CIRCUIT_SYNTH_CACHE_DIR", str(temp_cache_dir / "cache"))

        # Clear singleton
        SymbolLibCache._instance = None
        SymbolLibCache._initialized = False
        SymbolLibCache._library_index.clear()

        # Parse directories
        dirs = SymbolLibCache._parse_kicad_symbol_dirs()

        assert len(dirs) == 2
        # Resolve paths to handle symlinks properly (macOS /var -> /private/var)
        resolved_dirs = [d.resolve() for d in dirs]
        assert dir1.resolve() in resolved_dirs
        assert dir2.resolve() in resolved_dirs
