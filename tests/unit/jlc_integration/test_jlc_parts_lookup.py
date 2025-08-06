#!/usr/bin/env python3
"""
Unit tests for JLC Parts Integration

Tests both API-based and web scraping approaches for component lookup.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from circuit_synth.manufacturing.jlcpcb import (
    JlcPartsInterface,
    _calculate_manufacturability_score,
    enhance_component_with_jlc_data,
    recommend_jlc_component,
)


class TestJlcPartsInterface:
    """Test cases for JLC Parts API interface."""

    def test_init_with_credentials(self):
        """Test initialization with API credentials."""
        interface = JlcPartsInterface("test_key", "test_secret")
        assert interface.key == "test_key"
        assert interface.secret == "test_secret"
        assert interface.token is None
        assert interface.lastPage is None

    def test_init_without_credentials(self):
        """Test initialization without credentials uses environment variables."""
        with patch.dict(
            "os.environ", {"JLCPCB_KEY": "env_key", "JLCPCB_SECRET": "env_secret"}
        ):
            interface = JlcPartsInterface()
            assert interface.key == "env_key"
            assert interface.secret == "env_secret"

    def test_init_missing_credentials(self):
        """Test initialization with missing credentials."""
        with patch.dict("os.environ", {}, clear=True):
            interface = JlcPartsInterface()
            assert interface.key is None
            assert interface.secret is None

    @patch("requests.post")
    def test_obtain_token_success(self, mock_post):
        """Test successful token acquisition."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 200, "data": "test_token_123"}
        mock_post.return_value = mock_response

        interface = JlcPartsInterface("test_key", "test_secret")
        interface._obtain_token()

        assert interface.token == "test_token_123"
        mock_post.assert_called_once()

        # Verify request structure
        call_args = mock_post.call_args
        assert call_args[1]["json"]["appKey"] == "test_key"
        assert call_args[1]["json"]["appSecret"] == "test_secret"

    @patch("requests.post")
    def test_obtain_token_http_error(self, mock_post):
        """Test token acquisition with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "unauthorized"}
        mock_post.return_value = mock_response

        interface = JlcPartsInterface("test_key", "test_secret")

        with pytest.raises(RuntimeError, match="Cannot obtain token"):
            interface._obtain_token()

    @patch("requests.post")
    def test_obtain_token_api_error(self, mock_post):
        """Test token acquisition with API error response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 400,
            "message": "Invalid credentials",
        }
        mock_post.return_value = mock_response

        interface = JlcPartsInterface("test_key", "test_secret")

        with pytest.raises(RuntimeError, match="Cannot obtain token"):
            interface._obtain_token()

    @patch("requests.post")
    def test_get_component_page_success(self, mock_post):
        """Test successful component page retrieval."""
        # Mock token request
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {"code": 200, "data": "test_token"}

        # Mock component data request
        data_response = Mock()
        data_response.json.return_value = {
            "data": {
                "lastKey": "next_page_key",
                "componentInfos": [
                    {
                        "lcscPart": "C123456",
                        "mfrPart": "STM32G030C8T6",
                        "manufacturer": "STMicroelectronics",
                        "stock": 10000,
                        "price": "$1.50",
                    }
                ],
            }
        }

        mock_post.side_effect = [token_response, data_response]

        interface = JlcPartsInterface("test_key", "test_secret")
        components = interface.get_component_page()

        assert len(components) == 1
        assert components[0]["lcscPart"] == "C123456"
        assert components[0]["mfrPart"] == "STM32G030C8T6"
        assert interface.lastPage == "next_page_key"

    def test_search_components_no_credentials(self):
        """Test component search without credentials returns empty list."""
        interface = JlcPartsInterface()
        results = interface.search_components(["STM32G0"])
        assert results == []

    @patch.object(JlcPartsInterface, "get_component_page")
    def test_search_components_with_results(self, mock_get_page):
        """Test component search with matching results."""
        # Mock component data
        mock_components = [
            {
                "lcscPart": "C123456",
                "mfrPart": "STM32G030C8T6",
                "manufacturer": "STMicroelectronics",
                "description": "ARM Cortex-M0+ MCU",
                "package": "LQFP-48",
                "stock": 10000,
                "price": "$1.50",
            },
            {
                "lcscPart": "C789012",
                "mfrPart": "STM32F103C8T6",
                "manufacturer": "STMicroelectronics",
                "description": "ARM Cortex-M3 MCU",
                "package": "LQFP-48",
                "stock": 5000,
                "price": "$2.00",
            },
        ]

        # First call returns components, second returns None (end of data)
        mock_get_page.side_effect = [mock_components, None]

        interface = JlcPartsInterface("test_key", "test_secret")
        results = interface.search_components(["STM32G0"], max_results=10)

        # Should only match the STM32G0 component
        assert len(results) == 1
        assert results[0]["manufacturer_part"] == "STM32G030C8T6"
        assert results[0]["stock"] == 10000

    @patch.object(JlcPartsInterface, "search_components")
    def test_get_most_available_part(self, mock_search):
        """Test finding component with highest stock."""
        mock_search.return_value = [
            {"manufacturer_part": "STM32G030F6P6", "stock": 50000},
            {"manufacturer_part": "STM32G030C8T6", "stock": 75000},
            {"manufacturer_part": "STM32G031G8U6", "stock": 25000},
        ]

        interface = JlcPartsInterface("test_key", "test_secret")
        best_component = interface.get_most_available_part(["STM32G0"])

        assert best_component["manufacturer_part"] == "STM32G030C8T6"
        assert best_component["stock"] == 75000


class TestRecommendationFunctions:
    """Test cases for component recommendation functions."""

    @patch.object(JlcPartsInterface, "get_most_available_part")
    def test_recommend_jlc_component_success(self, mock_get_part):
        """Test successful component recommendation."""
        mock_get_part.return_value = {
            "manufacturer_part": "STM32G030C8T6",
            "stock": 75000,
            "price": "$1.50",
        }

        result = recommend_jlc_component("STM32G0", "LQFP")

        assert result["manufacturer_part"] == "STM32G030C8T6"
        assert result["stock"] == 75000
        mock_get_part.assert_called_once_with(["STM32G0", "LQFP"])

    @patch.object(JlcPartsInterface, "get_most_available_part")
    def test_recommend_jlc_component_no_package(self, mock_get_part):
        """Test component recommendation without package preference."""
        mock_get_part.return_value = {"manufacturer_part": "STM32G030C8T6"}

        recommend_jlc_component("STM32G0")

        mock_get_part.assert_called_once_with(["STM32G0"])

    @patch.object(JlcPartsInterface, "get_most_available_part")
    def test_recommend_jlc_component_error(self, mock_get_part):
        """Test component recommendation with error."""
        mock_get_part.side_effect = Exception("API Error")

        result = recommend_jlc_component("STM32G0")

        assert result is None

    def test_enhance_component_with_jlc_data(self):
        """Test component enhancement with JLC data."""
        with patch(
            "circuit_synth.manufacturing.jlcpcb.jlc_parts_lookup.recommend_jlc_component"
        ) as mock_recommend:
            mock_recommend.return_value = {
                "manufacturer_part": "STM32G030C8T6",
                "stock": 75000,
            }

            result = enhance_component_with_jlc_data("MCU_ST_STM32G0:STM32G030C8T6", "")

            assert result["original_symbol"] == "MCU_ST_STM32G0:STM32G030C8T6"
            assert result["jlc_recommendation"]["manufacturer_part"] == "STM32G030C8T6"
            assert "manufacturability_score" in result
            mock_recommend.assert_called_once_with("STM32G030C8T6")


class TestManufacturabilityScoring:
    """Test cases for manufacturability scoring logic."""

    def test_calculate_manufacturability_score_no_data(self):
        """Test scoring with no component data."""
        score = _calculate_manufacturability_score(None)
        assert score == 0.0

    def test_calculate_manufacturability_score_high_stock(self):
        """Test scoring with high stock component."""
        component_data = {"stock": 15000, "library_type": "standard"}
        score = _calculate_manufacturability_score(component_data)
        assert score == 1.0

    def test_calculate_manufacturability_score_medium_stock(self):
        """Test scoring with medium stock component."""
        component_data = {"stock": 5000, "library_type": "standard"}
        score = _calculate_manufacturability_score(component_data)
        assert score == 0.8

    def test_calculate_manufacturability_score_basic_part_bonus(self):
        """Test scoring with basic part bonus."""
        component_data = {"stock": 5000, "library_type": "basic"}
        score = _calculate_manufacturability_score(component_data)
        assert score == 1.0  # 0.8 + 0.2 bonus, capped at 1.0

    def test_calculate_manufacturability_score_low_stock(self):
        """Test scoring with low stock component."""
        component_data = {"stock": 50, "library_type": "standard"}
        score = _calculate_manufacturability_score(component_data)
        assert score == 0.4  # 10-99 range gives 0.4 score

    def test_calculate_manufacturability_score_zero_stock(self):
        """Test scoring with zero stock component."""
        component_data = {"stock": 0, "library_type": "standard"}
        score = _calculate_manufacturability_score(component_data)
        assert score == 0.0


class TestIntegrationScenarios:
    """Integration test scenarios for real-world usage."""

    def test_full_component_lookup_workflow(self):
        """Test complete workflow from symbol to recommendation."""
        with patch.object(
            JlcPartsInterface, "get_most_available_part"
        ) as mock_get_part:
            mock_get_part.return_value = {
                "lcsc_part": "C123456",
                "manufacturer_part": "STM32G030C8T6",
                "manufacturer": "STMicroelectronics",
                "stock": 75000,
                "price": "$1.50",
                "library_type": "basic",
            }

            # Test the full workflow
            enhanced_data = enhance_component_with_jlc_data(
                "MCU_ST_STM32G0:STM32G030C8T6", ""
            )

            # Verify all expected fields are present
            assert enhanced_data["original_symbol"] == "MCU_ST_STM32G0:STM32G030C8T6"
            assert enhanced_data["jlc_recommendation"]["stock"] == 75000
            assert (
                enhanced_data["manufacturability_score"] == 1.0
            )  # High stock + basic part

    def test_error_handling_throughout_pipeline(self):
        """Test error handling in the complete pipeline."""
        with patch.object(
            JlcPartsInterface, "get_most_available_part"
        ) as mock_get_part:
            mock_get_part.side_effect = Exception("Network error")

            # Should handle errors gracefully
            enhanced_data = enhance_component_with_jlc_data("Device:R", "10K")

            assert enhanced_data["original_symbol"] == "Device:R"
            assert enhanced_data["jlc_recommendation"] is None
            assert enhanced_data["manufacturability_score"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
