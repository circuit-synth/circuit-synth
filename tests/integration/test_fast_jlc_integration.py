"""
Integration tests for Fast JLCPCB Search
Tests the complete flow including web scraping and caching.
"""

import time

import pytest

from circuit_synth.manufacturing.jlcpcb import (
    FastJLCSearch,
    fast_jlc_search,
    find_cheapest_jlc,
    find_most_available_jlc,
)


@pytest.mark.skip(reason="JLCPCB API may be unavailable or rate-limited")
def test_real_search_stm32():
    """Test searching for STM32 microcontrollers."""
    try:
        results = fast_jlc_search("STM32F103", min_stock=100, max_results=5)
    except Exception as e:
        pytest.skip(f"JLCPCB search failed: {e}")

    # Should find some results
    if not results:
        pytest.skip("No results returned from JLCPCB")
    assert len(results) > 0

    # Check result structure
    first = results[0]
    assert first.part_number.startswith("C")
    assert first.stock > 100
    assert first.price > 0
    assert "STM32" in first.description.upper()


@pytest.mark.skip(reason="JLCPCB API may be unavailable or rate-limited")
def test_real_search_passive():
    """Test searching for passive components."""
    try:
        results = fast_jlc_search("10k 0603", min_stock=1000, max_results=3)
    except Exception as e:
        pytest.skip(f"JLCPCB search failed: {e}")

    # Should find resistors
    if not results:
        pytest.skip("No results returned from JLCPCB")
    assert len(results) > 0

    # Check it found resistors
    for result in results:
        desc_lower = result.description.lower()
        assert any(term in desc_lower for term in ["resistor", "ohm", "10k", "10kω"])


@pytest.mark.skip(reason="JLCPCB API may be unavailable or rate-limited")
def test_caching_performance():
    """Test that caching improves performance."""
    searcher = FastJLCSearch(cache_hours=1)

    # First search (cache miss)
    start = time.time()
    results1 = searcher.search("LM358", max_results=3)
    first_time = time.time() - start

    # Second search (cache hit)
    start = time.time()
    results2 = searcher.search("LM358", max_results=3)
    second_time = time.time() - start

    # Cache should make second search much faster
    assert second_time < first_time * 0.5  # At least 2x faster

    # Results should be identical
    assert len(results1) == len(results2)
    if results1:
        assert results1[0].part_number == results2[0].part_number


def test_find_cheapest():
    """Test finding cheapest component."""
    result = find_cheapest_jlc("0.1uF 0603", min_stock=5000)

    if result:
        # Should be a capacitor
        assert (
            "F" in result.description.upper()
            or "capacitor" in result.description.lower()
        )
        assert result.stock >= 5000
        # 0.1uF caps should be cheap
        assert result.price < 0.1


def test_find_most_available():
    """Test finding component with highest stock."""
    result = find_most_available_jlc("100nF")

    if result:
        # Common capacitor should have high stock
        assert result.stock > 10000
        assert "nF" in result.description or "F" in result.description.upper()


def test_search_sorting():
    """Test different sorting options."""
    searcher = FastJLCSearch(cache_hours=0)  # Disable cache for this test

    # Sort by price
    price_sorted = searcher.search("resistor 1k", sort_by="price", max_results=5)
    if len(price_sorted) > 1:
        prices = [r.price for r in price_sorted]
        assert prices == sorted(prices)

    # Sort by stock
    stock_sorted = searcher.search("resistor 1k", sort_by="stock", max_results=5)
    if len(stock_sorted) > 1:
        stocks = [r.stock for r in stock_sorted]
        assert stocks == sorted(stocks, reverse=True)


def test_basic_part_preference():
    """Test that basic parts get preference."""
    results = fast_jlc_search("capacitor", prefer_basic=True, max_results=10)

    if results:
        # Count basic vs extended
        basic_count = sum(1 for r in results if r.basic_part)
        extended_count = len(results) - basic_count

        # If we have both types, basic should appear first (higher scores)
        if basic_count > 0 and extended_count > 0:
            basic_scores = [r.match_score for r in results if r.basic_part]
            extended_scores = [r.match_score for r in results if not r.basic_part]
            # Average score of basic parts should be higher
            assert sum(basic_scores) / len(basic_scores) > sum(extended_scores) / len(
                extended_scores
            )


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
