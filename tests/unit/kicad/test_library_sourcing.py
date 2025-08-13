"""
Tests for KiCad library sourcing system
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from circuit_synth.kicad.library_sourcing.cache import LibraryCache
from circuit_synth.kicad.library_sourcing.config import LibrarySourceConfig
from circuit_synth.kicad.library_sourcing.models import (
    ComponentSearchResult,
    LibrarySource,
    SearchQuery,
)
from circuit_synth.kicad.library_sourcing.orchestrator import LibraryOrchestrator


class TestLibraryCache:
    """Test library caching functionality"""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache = LibraryCache(self.temp_dir)

    def test_cache_set_and_get(self):
        """Test basic cache operations"""

        query = SearchQuery(query="STM32F4")
        results = [
            ComponentSearchResult(
                symbol_library="MCU_ST_STM32F4",
                symbol_name="STM32F407VETx",
                source=LibrarySource.LOCAL_KICAD,
                confidence_score=0.9,
            )
        ]

        # Cache results
        self.cache.set(query, results)

        # Retrieve results
        cached_results = self.cache.get(query)

        assert cached_results is not None
        assert len(cached_results) == 1
        assert cached_results[0].symbol_name == "STM32F407VETx"
        assert cached_results[0].source == LibrarySource.LOCAL_KICAD

    def test_cache_expiry(self):
        """Test cache expiration"""

        query = SearchQuery(query="test")
        results = [ComponentSearchResult(source=LibrarySource.LOCAL_KICAD)]

        # Set very short TTL
        self.cache.default_ttl = 0.1
        self.cache.set(query, results)

        # Should be cached immediately
        assert self.cache.get(query) is not None

        # Wait for expiry
        import time

        time.sleep(0.2)

        # Should be expired
        assert self.cache.get(query) is None


class TestLibrarySourceConfig:
    """Test configuration management"""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = LibrarySourceConfig(self.temp_dir)

    def test_default_config_creation(self):
        """Test default configuration is created properly"""

        config_data = self.config.config

        assert "sources" in config_data
        assert "local_kicad" in config_data["sources"]
        assert config_data["sources"]["local_kicad"]["enabled"] is True
        assert config_data["sources"]["snapeda"]["enabled"] is False  # Requires API key

    def test_api_credential_update(self):
        """Test updating API credentials"""

        # Update SnapEDA credentials
        self.config.update_api_credentials(
            LibrarySource.SNAPEDA, api_key="test_key_123"
        )

        # Check configuration was updated
        source_config = self.config.get_source_config(LibrarySource.SNAPEDA)
        assert source_config.enabled is True
        assert source_config.api_key == "test_key_123"

    def test_source_configuration_check(self):
        """Test source configuration validation"""

        # Local KiCad should always be configured
        assert self.config.is_source_configured(LibrarySource.LOCAL_KICAD) is True

        # SnapEDA should not be configured initially
        assert self.config.is_source_configured(LibrarySource.SNAPEDA) is False

        # DigiKey should not be configured initially
        assert self.config.is_source_configured(LibrarySource.DIGIKEY) is False


class TestLibraryOrchestrator:
    """Test library orchestration functionality"""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.orchestrator = LibraryOrchestrator(cache_dir=self.temp_dir)

    @pytest.mark.asyncio
    async def test_search_with_cache(self):
        """Test search with caching"""

        query = SearchQuery(query="STM32F4")

        # Mock local source to return results
        mock_result = ComponentSearchResult(
            symbol_library="MCU_ST_STM32F4",
            symbol_name="STM32F407VETx",
            source=LibrarySource.LOCAL_KICAD,
            confidence_score=0.9,
        )

        with patch.object(
            self.orchestrator.sources[LibrarySource.LOCAL_KICAD], "search"
        ) as mock_search:
            mock_search.return_value = [mock_result]

            # First search
            results1 = await self.orchestrator.search_component(query)
            assert len(results1) == 1
            assert results1[0].symbol_name == "STM32F407VETx"

            # Second search should use cache
            results2 = await self.orchestrator.search_component(query)
            assert len(results2) == 1
            assert results2[0].symbol_name == "STM32F407VETx"

            # Local source should only be called once
            mock_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_search(self):
        """Test fallback search when local results insufficient"""

        # Mock local results (only 1 result)
        local_results = [("MCU_ST_STM32F4", "STM32F407VETx")]

        with patch.object(self.orchestrator, "search_component") as mock_search:
            mock_search.return_value = [
                ComponentSearchResult(
                    symbol_library="External_MCU",
                    symbol_name="STM32F407VG",
                    source=LibrarySource.SNAPEDA,
                    confidence_score=0.8,
                )
            ]

            # Should trigger API search due to insufficient local results
            api_results = await self.orchestrator.search_as_fallback(
                "STM32F4", local_results
            )

            assert len(api_results) == 1
            assert api_results[0].source == LibrarySource.SNAPEDA
            mock_search.assert_called_once()

    def test_source_status(self):
        """Test source status reporting"""

        status = self.orchestrator.get_source_status()

        assert LibrarySource.LOCAL_KICAD in status
        assert LibrarySource.SNAPEDA in status
        assert LibrarySource.DIGIKEY in status

        # Check status structure
        local_status = status[LibrarySource.LOCAL_KICAD]
        assert "enabled" in local_status
        assert "priority" in local_status
        assert "status" in local_status


class TestSearchQuery:
    """Test search query model"""

    def test_default_preferred_sources(self):
        """Test default preferred sources"""

        query = SearchQuery(query="test")

        expected_sources = [
            LibrarySource.LOCAL_KICAD,
            LibrarySource.HTTP_LIBRARY,
            LibrarySource.SNAPEDA,
            LibrarySource.DIGIKEY,
        ]

        assert query.preferred_sources == expected_sources

    def test_custom_preferences(self):
        """Test custom source preferences"""

        query = SearchQuery(
            query="test",
            preferred_sources=[LibrarySource.LOCAL_KICAD, LibrarySource.SNAPEDA],
        )

        assert len(query.preferred_sources) == 2
        assert LibrarySource.DIGIKEY not in query.preferred_sources


class TestComponentSearchResult:
    """Test component search result model"""

    def test_symbol_ref_property(self):
        """Test symbol reference formatting"""

        result = ComponentSearchResult(
            symbol_library="MCU_ST_STM32F4",
            symbol_name="STM32F407VETx",
            source=LibrarySource.LOCAL_KICAD,
        )

        assert result.symbol_ref == "MCU_ST_STM32F4:STM32F407VETx"

    def test_footprint_ref_property(self):
        """Test footprint reference formatting"""

        result = ComponentSearchResult(
            footprint_library="Package_QFP",
            footprint_name="LQFP-100_14x14mm_P0.5mm",
            source=LibrarySource.LOCAL_KICAD,
        )

        assert result.footprint_ref == "Package_QFP:LQFP-100_14x14mm_P0.5mm"

    def test_is_complete_property(self):
        """Test completeness check"""

        # Complete result
        complete_result = ComponentSearchResult(
            symbol_library="MCU_ST_STM32F4",
            symbol_name="STM32F407VETx",
            footprint_library="Package_QFP",
            footprint_name="LQFP-100_14x14mm_P0.5mm",
            source=LibrarySource.LOCAL_KICAD,
        )
        assert complete_result.is_complete is True

        # Incomplete result (missing footprint)
        incomplete_result = ComponentSearchResult(
            symbol_library="MCU_ST_STM32F4",
            symbol_name="STM32F407VETx",
            source=LibrarySource.LOCAL_KICAD,
        )
        assert incomplete_result.is_complete is False
