"""
Tests for Fast JLCPCB Search Implementation
"""

import time
import unittest
from unittest.mock import MagicMock, patch

from circuit_synth.manufacturing.jlcpcb.fast_search import (
    FastJLCSearch,
    FastSearchResult,
    fast_jlc_search,
    find_cheapest_jlc,
    find_most_available_jlc,
)


class TestFastJLCSearch(unittest.TestCase):
    """Test the fast JLCPCB search functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.searcher = FastJLCSearch(cache_hours=0)  # Disable caching for tests

        # Mock search results
        self.mock_results = [
            {
                "lcsc_part": "C123456",
                "manufacturer_part": "STM32G431KBT6",
                "description": "STM32G4 ARM Cortex-M4 MCU",
                "stock": 5000,
                "price": 3.50,
                "package": "LQFP-32",
                "library_type": "Extended",
            },
            {
                "lcsc_part": "C234567",
                "manufacturer_part": "STM32G474RET6",
                "description": "STM32G4 ARM Cortex-M4 MCU 512KB",
                "stock": 2000,
                "price": 5.20,
                "package": "LQFP-64",
                "library_type": "Extended",
            },
            {
                "lcsc_part": "C345678",
                "manufacturer_part": "GRM188R71H104KA93D",
                "description": "0.1uF ±10% 50V X7R 0603",
                "stock": 50000,
                "price": 0.008,
                "package": "0603",
                "library_type": "Basic",
            },
        ]

    @patch.object(FastJLCSearch, "_perform_search")
    def test_basic_search(self, mock_perform):
        """Test basic search functionality."""
        # Setup mock
        mock_perform.return_value = [
            self.searcher._convert_to_fast_result(r, "STM32G4")
            for r in self.mock_results[:2]
        ]

        # Perform search
        results = self.searcher.search("STM32G4", max_results=5)

        # Assertions
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].part_number, "C123456")
        self.assertIn("STM32G4", results[0].description)

    @patch.object(FastJLCSearch, "_perform_search")
    def test_stock_filtering(self, mock_perform):
        """Test that stock filtering works correctly."""
        # Setup mock
        mock_perform.return_value = [
            self.searcher._convert_to_fast_result(r, "STM32") for r in self.mock_results
        ]

        # Search with stock filter
        results = self.searcher.search("STM32", min_stock=3000)

        # Should only return items with stock >= 3000
        self.assertEqual(len(results), 2)  # Only first item and capacitor
        for result in results:
            self.assertGreaterEqual(result.stock, 3000)

    @patch.object(FastJLCSearch, "_perform_search")
    def test_price_sorting(self, mock_perform):
        """Test that price sorting works correctly."""
        # Setup mock
        mock_perform.return_value = [
            self.searcher._convert_to_fast_result(r, "component")
            for r in self.mock_results
        ]

        # Search sorted by price
        results = self.searcher.search("component", sort_by="price")

        # Check prices are in ascending order
        prices = [r.price for r in results]
        self.assertEqual(prices, sorted(prices))

    @patch.object(FastJLCSearch, "_perform_search")
    def test_find_cheapest(self, mock_perform):
        """Test finding the cheapest component."""
        # Setup mock
        mock_perform.return_value = [
            self.searcher._convert_to_fast_result(r, "capacitor")
            for r in self.mock_results
        ]

        # Find cheapest
        result = self.searcher.find_cheapest("capacitor", min_stock=100)

        # Should return the capacitor (cheapest)
        self.assertIsNotNone(result)
        self.assertEqual(result.part_number, "C345678")
        self.assertEqual(result.price, 0.008)

    @patch.object(FastJLCSearch, "_perform_search")
    def test_find_most_available(self, mock_perform):
        """Test finding component with highest stock."""
        # Setup mock
        mock_perform.return_value = [
            self.searcher._convert_to_fast_result(r, "component")
            for r in self.mock_results
        ]

        # Find most available
        result = self.searcher.find_most_available("component")

        # Should return the capacitor (highest stock)
        self.assertIsNotNone(result)
        self.assertEqual(result.part_number, "C345678")
        self.assertEqual(result.stock, 50000)

    def test_match_score_calculation(self):
        """Test that match scores are calculated correctly."""
        # Exact match
        score = self.searcher._calculate_match_score(
            "STM32G431KBT6 MCU", "STM32G431KBT6", "STM32G431KBT6"
        )
        self.assertEqual(score, 1.0)

        # Partial match
        score = self.searcher._calculate_match_score(
            "STM32G4 ARM Cortex-M4", "STM32G474", "STM32G4"
        )
        self.assertGreater(score, 0.5)

        # Poor match
        score = self.searcher._calculate_match_score(
            "Capacitor 0603", "C12345", "resistor"
        )
        self.assertLess(score, 0.3)

    def test_basic_part_preference(self):
        """Test that basic parts get preference boost."""
        results = [
            FastSearchResult(
                part_number="C1",
                manufacturer_part="P1",
                description="Extended part",
                stock=1000,
                price=1.0,
                package="0603",
                basic_part=False,
                match_score=0.5,
            ),
            FastSearchResult(
                part_number="C2",
                manufacturer_part="P2",
                description="Basic part",
                stock=1000,
                price=1.0,
                package="0603",
                basic_part=True,
                match_score=0.5,
            ),
        ]

        # Apply filters with basic preference
        filtered = self.searcher._apply_filters(results, min_stock=0, prefer_basic=True)

        # Basic part should have higher score
        self.assertGreater(filtered[1].match_score, filtered[0].match_score)

    def test_query_building_from_specs(self):
        """Test building search query from specifications."""
        # Resistor specs
        query = self.searcher._build_query_from_specs(
            "resistor", {"value": "10k", "package": "0603", "tolerance": "1%"}
        )
        self.assertEqual(query, "10k 0603 1%")

        # Capacitor specs
        query = self.searcher._build_query_from_specs(
            "capacitor", {"value": "0.1uF", "package": "0603", "voltage": "25"}
        )
        self.assertEqual(query, "0.1uF 0603 25V")

    @patch("circuit_synth.manufacturing.jlcpcb.fast_search.get_fast_searcher")
    def test_convenience_functions(self, mock_get_searcher):
        """Test the convenience functions work correctly."""
        mock_searcher = MagicMock()
        mock_get_searcher.return_value = mock_searcher

        # Test fast_jlc_search
        fast_jlc_search("test", min_stock=100)
        mock_searcher.search.assert_called_once_with(
            "test", min_stock=100, max_results=10
        )

        # Test find_cheapest_jlc
        find_cheapest_jlc("test", min_stock=200)
        mock_searcher.find_cheapest.assert_called_once_with("test", 200)

        # Test find_most_available_jlc
        find_most_available_jlc("test")
        mock_searcher.find_most_available.assert_called_once_with("test")

    def test_performance(self):
        """Test that searches complete quickly."""
        with patch.object(self.searcher, "_perform_search") as mock_perform:
            # Mock instant return
            mock_perform.return_value = []

            start = time.time()
            self.searcher.search("test")
            elapsed = time.time() - start

            # Should complete in under 100ms (excluding actual web requests)
            self.assertLess(elapsed, 0.1)


class TestFastSearchResult(unittest.TestCase):
    """Test the FastSearchResult data class."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = FastSearchResult(
            part_number="C123",
            manufacturer_part="TEST123",
            description="Test component",
            stock=1000,
            price=1.23,
            package="0603",
            basic_part=True,
            match_score=0.75,
        )

        d = result.to_dict()

        self.assertEqual(d["part_number"], "C123")
        self.assertEqual(d["price"], 1.23)
        self.assertEqual(d["basic_part"], True)
        self.assertEqual(d["match_score"], 0.75)


if __name__ == "__main__":
    unittest.main()
