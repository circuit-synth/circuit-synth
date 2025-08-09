#!/usr/bin/env python3
"""
Tests for DigiKey Integration

Tests the DigiKey API client, caching, and component search functionality.
"""

import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from circuit_synth.manufacturing.digikey import (
    DigiKeyAPIClient,
    DigiKeyCache,
    DigiKeyComponent,
    DigiKeyComponentSearch,
    DigiKeyConfig,
    search_digikey_components,
)


class TestDigiKeyConfig(unittest.TestCase):
    """Test DigiKey configuration."""

    def test_config_from_environment(self):
        """Test creating config from environment variables."""
        with patch.dict(
            os.environ,
            {
                "DIGIKEY_CLIENT_ID": "test_id",
                "DIGIKEY_CLIENT_SECRET": "test_secret",
                "DIGIKEY_CLIENT_SANDBOX": "true",
                "DIGIKEY_STORAGE_PATH": "/tmp/test_cache",
            },
        ):
            config = DigiKeyConfig.from_environment()

            self.assertEqual(config.client_id, "test_id")
            self.assertEqual(config.client_secret, "test_secret")
            self.assertTrue(config.sandbox_mode)
            self.assertEqual(config.cache_dir, Path("/tmp/test_cache"))

    def test_config_defaults(self):
        """Test config with minimal environment."""
        from circuit_synth.manufacturing.digikey.config_manager import (
            DigiKeyConfigManager,
        )

        with patch.dict(os.environ, {}, clear=True):
            # Mock the config manager to return empty config (no file found)
            with patch.object(
                DigiKeyConfigManager,
                "get_config",
                return_value={
                    "client_id": "",
                    "client_secret": "",
                    "sandbox_mode": False,
                },
            ):
                config = DigiKeyConfig.from_environment()

                self.assertEqual(config.client_id, "")
                self.assertEqual(config.client_secret, "")
                self.assertFalse(config.sandbox_mode)
                self.assertEqual(
                    config.cache_dir, Path.home() / ".circuit_synth" / "digikey_cache"
                )


class TestDigiKeyCache(unittest.TestCase):
    """Test DigiKey caching functionality."""

    def setUp(self):
        """Set up test cache directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = DigiKeyCache(cache_dir=Path(self.temp_dir), ttl_seconds=60)

    def tearDown(self):
        """Clean up test cache directory."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_search_cache(self):
        """Test caching search results."""
        search_params = {"keyword": "STM32", "filters": {}, "max_results": 10}
        results = {"Products": [{"DigiKeyPartNumber": "TEST-123"}]}

        # Cache should be empty initially
        self.assertIsNone(self.cache.get_search_cache(search_params))

        # Set cache
        self.cache.set_search_cache(search_params, results)

        # Retrieve from cache
        cached = self.cache.get_search_cache(search_params)
        self.assertIsNotNone(cached)
        self.assertEqual(
            cached["results"]["Products"][0]["DigiKeyPartNumber"], "TEST-123"
        )

    def test_product_cache(self):
        """Test caching product details."""
        part_number = "TEST-PN-123"
        product_data = {
            "DigiKeyPartNumber": part_number,
            "ManufacturerPartNumber": "MPN-123",
            "Description": {"Value": "Test Component"},
        }

        # Cache should be empty initially
        self.assertIsNone(self.cache.get_product_cache(part_number))

        # Set cache
        self.cache.set_product_cache(part_number, product_data)

        # Retrieve from cache
        cached = self.cache.get_product_cache(part_number)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["data"]["ManufacturerPartNumber"], "MPN-123")

    def test_cache_expiry(self):
        """Test that cache expires after TTL."""
        # Create cache with 1 second TTL
        cache = DigiKeyCache(cache_dir=Path(self.temp_dir) / "expiry", ttl_seconds=1)

        part_number = "EXPIRE-TEST"
        product_data = {"test": "data"}

        # Set cache
        cache.set_product_cache(part_number, product_data)

        # Should be valid immediately
        self.assertIsNotNone(cache.get_product_cache(part_number))

        # Wait for expiry
        time.sleep(2)

        # Should be expired
        self.assertIsNone(cache.get_product_cache(part_number))

    def test_cache_stats(self):
        """Test cache statistics."""
        # Add some cached items
        self.cache.set_search_cache({"keyword": "test1"}, {"data": "1"})
        self.cache.set_search_cache({"keyword": "test2"}, {"data": "2"})
        self.cache.set_product_cache("PN1", {"data": "p1"})

        stats = self.cache.get_cache_stats()

        self.assertEqual(stats["search_cache"]["total_files"], 2)
        self.assertEqual(stats["search_cache"]["valid_files"], 2)
        self.assertEqual(stats["product_cache"]["total_files"], 1)
        self.assertEqual(stats["product_cache"]["valid_files"], 1)


class TestDigiKeyAPIClient(unittest.TestCase):
    """Test DigiKey API client."""

    def setUp(self):
        """Set up test client."""
        self.config = DigiKeyConfig(
            client_id="test_id",
            client_secret="test_secret",
            sandbox_mode=True,
        )

    @patch("circuit_synth.manufacturing.digikey.api_client.requests.post")
    def test_get_access_token(self, mock_post):
        """Test OAuth token acquisition."""
        # Mock token response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "test_token_12345",
            "expires_in": 1800,
        }
        mock_post.return_value = mock_response

        client = DigiKeyAPIClient(self.config)
        token = client._get_access_token()

        self.assertEqual(token, "test_token_12345")
        self.assertEqual(client.access_token, "test_token_12345")

        # Verify token request
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], client.token_url)
        self.assertEqual(call_args[1]["data"]["grant_type"], "client_credentials")

    @patch("circuit_synth.manufacturing.digikey.api_client.requests.request")
    def test_search_products(self, mock_request):
        """Test product search."""
        # Mock search response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Products": [
                {
                    "DigiKeyPartNumber": "296-1234-ND",
                    "ManufacturerPartNumber": "LM358",
                    "Description": {"Value": "Op Amp"},
                }
            ]
        }
        mock_request.return_value = mock_response

        # Mock the token acquisition
        with patch.object(
            DigiKeyAPIClient, "_get_access_token", return_value="test_token"
        ):
            client = DigiKeyAPIClient(self.config)
            results = client.search_products("LM358", record_count=5)

        self.assertEqual(len(results["Products"]), 1)
        self.assertEqual(results["Products"][0]["ManufacturerPartNumber"], "LM358")


class TestDigiKeyComponent(unittest.TestCase):
    """Test DigiKeyComponent dataclass."""

    def test_manufacturability_score(self):
        """Test manufacturability score calculation."""
        # High score component (good stock, low price, low MOQ)
        comp1 = DigiKeyComponent(
            digikey_part_number="TEST-1",
            manufacturer_part_number="MPN-1",
            manufacturer="TestCorp",
            description="Test Component",
            quantity_available=15000,
            quantity_on_hand=15000,
            unit_price=0.05,
            min_order_qty=1,
            packaging="Cut Tape",
            category="Resistors",
            family="Chip Resistor",
            datasheet_url=None,
            parameters={},
            price_breaks=[],
        )

        # Low availability, higher price
        comp2 = DigiKeyComponent(
            digikey_part_number="TEST-2",
            manufacturer_part_number="MPN-2",
            manufacturer="TestCorp",
            description="Test Component",
            quantity_available=50,
            quantity_on_hand=50,
            unit_price=25.00,
            min_order_qty=100,
            packaging="Bulk",
            category="ICs",
            family="Microcontroller",
            datasheet_url=None,
            parameters={},
            price_breaks=[],
        )

        score1 = comp1.manufacturability_score
        score2 = comp2.manufacturability_score

        self.assertGreater(score1, 80)  # Should have high score
        self.assertLess(score2, 30)  # Should have low score
        self.assertGreater(score1, score2)  # comp1 should score higher

    def test_is_in_stock(self):
        """Test stock availability check."""
        in_stock = DigiKeyComponent(
            digikey_part_number="TEST",
            manufacturer_part_number="TEST",
            manufacturer="Test",
            description="Test",
            quantity_available=100,
            quantity_on_hand=100,
            unit_price=1.0,
            min_order_qty=1,
            packaging="Test",
            category="Test",
            family="Test",
            datasheet_url=None,
            parameters={},
            price_breaks=[],
        )

        out_of_stock = DigiKeyComponent(
            digikey_part_number="TEST",
            manufacturer_part_number="TEST",
            manufacturer="Test",
            description="Test",
            quantity_available=0,
            quantity_on_hand=0,
            unit_price=1.0,
            min_order_qty=1,
            packaging="Test",
            category="Test",
            family="Test",
            datasheet_url=None,
            parameters={},
            price_breaks=[],
        )

        self.assertTrue(in_stock.is_in_stock)
        self.assertFalse(out_of_stock.is_in_stock)


class TestDigiKeyComponentSearch(unittest.TestCase):
    """Test component search functionality."""

    @patch.object(DigiKeyAPIClient, "search_products")
    @patch.object(DigiKeyAPIClient, "_get_access_token")
    def test_search_components(self, mock_token, mock_search):
        """Test searching for components."""
        # Mock token
        mock_token.return_value = "test_token"

        # Mock search results
        mock_search.return_value = {
            "Products": [
                {
                    "DigiKeyPartNumber": "TEST-123",
                    "ManufacturerPartNumber": "MPN-123",
                    "Manufacturer": {"Value": "TestCorp"},
                    "Description": {"Value": "Test Component"},
                    "QuantityAvailable": 1000,
                    "QuantityOnHand": 1000,
                    "UnitPrice": 1.50,
                    "MinimumOrderQuantity": 1,
                    "Packaging": {"Value": "Cut Tape"},
                    "Category": {"Value": "Capacitors"},
                    "Family": {"Value": "Ceramic"},
                    "DatasheetUrl": "http://example.com/datasheet.pdf",
                    "Parameters": [],
                    "PriceBreaks": [],
                }
            ]
        }

        # Search without cache
        searcher = DigiKeyComponentSearch(use_cache=False)
        results = searcher.search_components("capacitor", max_results=5)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].manufacturer_part_number, "MPN-123")
        self.assertEqual(results[0].manufacturer, "TestCorp")
        self.assertTrue(results[0].is_in_stock)

    def test_parse_product(self):
        """Test parsing product data."""
        product_data = {
            "DigiKeyPartNumber": "296-1234-ND",
            "ManufacturerPartNumber": "LM358N",
            "Manufacturer": {"Value": "Texas Instruments"},
            "Description": {"Value": "IC OPAMP GP 2 CIRCUIT 8DIP"},
            "QuantityAvailable": 5432,
            "QuantityOnHand": 5432,
            "UnitPrice": 0.45,
            "MinimumOrderQuantity": 1,
            "Packaging": {"Value": "Tube"},
            "Category": {"Value": "Integrated Circuits (ICs)"},
            "Family": {"Value": "Linear - Amplifiers"},
            "DatasheetUrl": "http://www.ti.com/datasheet.pdf",
            "Parameters": [
                {"Parameter": "Package / Case", "Value": "8-DIP"},
                {"Parameter": "Voltage - Supply", "Value": "3V ~ 32V"},
            ],
            "PriceBreaks": [
                {"BreakQuantity": 1, "UnitPrice": 0.45, "TotalPrice": 0.45},
                {"BreakQuantity": 10, "UnitPrice": 0.40, "TotalPrice": 4.00},
            ],
        }

        searcher = DigiKeyComponentSearch(use_cache=False)
        component = searcher._parse_product(product_data)

        self.assertEqual(component.digikey_part_number, "296-1234-ND")
        self.assertEqual(component.manufacturer_part_number, "LM358N")
        self.assertEqual(component.manufacturer, "Texas Instruments")
        self.assertEqual(component.quantity_available, 5432)
        self.assertEqual(component.unit_price, 0.45)
        self.assertEqual(len(component.price_breaks), 2)
        self.assertEqual(component.parameters["Package / Case"], "8-DIP")


if __name__ == "__main__":
    unittest.main()
