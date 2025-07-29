#!/usr/bin/env python3
"""
Unit tests for JLC Web Scraper

Tests web scraping functionality for component lookup without API keys.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from bs4 import BeautifulSoup
from circuit_synth.jlc_integration import (
    JlcWebScraper,
    search_jlc_components_web,
    get_component_availability_web,
    enhance_component_with_web_data
)


class TestJlcWebScraper:
    """Test cases for JLC Web Scraper."""
    
    def test_init_default_delay(self):
        """Test initialization with default delay."""
        scraper = JlcWebScraper()
        assert scraper.delay_seconds == 1.0
        assert scraper.session is not None
    
    def test_init_custom_delay(self):
        """Test initialization with custom delay."""
        scraper = JlcWebScraper(delay_seconds=2.5)
        assert scraper.delay_seconds == 2.5
    
    @patch('requests.Session.get')
    @patch('time.sleep')
    def test_search_components_success(self, mock_sleep, mock_get):
        """Test successful component search."""
        # Mock HTML response with component data
        mock_html = """
        <html>
            <body>
                <script>
                    var componentInfos = [
                        {
                            "lcscPart": "C123456",
                            "mfrPart": "STM32G030C8T6",
                            "stock": 75000,
                            "price": "$1.50"
                        }
                    ];
                </script>
                <table>
                    <tr><th>Part</th><th>Description</th><th>Mfr</th><th>Package</th><th>Stock</th></tr>
                    <tr><td>STM32G030C8T6</td><td>ARM MCU</td><td>ST</td><td>LQFP-48</td><td>75,000</td></tr>
                </table>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        scraper = JlcWebScraper(delay_seconds=0.1)
        results = scraper.search_components("STM32G0", max_results=10)
        
        # Verify request was made with proper URL
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0]
        assert "componentSearch" in call_args[0]
        assert "STM32G0" in call_args[0]
        
        # Verify delay was applied
        mock_sleep.assert_called_once_with(0.1)
    
    @patch('requests.Session.get')
    def test_search_components_request_error(self, mock_get):
        """Test component search with request error."""
        mock_get.side_effect = requests.RequestException("Network error")
        
        scraper = JlcWebScraper()
        results = scraper.search_components("STM32G0")
        
        assert results == []
    
    @patch('requests.Session.get')
    def test_search_components_http_error(self, mock_get):
        """Test component search with HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        scraper = JlcWebScraper()
        results = scraper.search_components("STM32G0")
        
        assert results == []
    
    def test_parse_html_table_valid_data(self):
        """Test parsing HTML table with valid component data."""
        html = """
        <table>
            <tr><th>Part Number</th><th>Description</th><th>Manufacturer</th><th>Package</th><th>Stock</th><th>Price</th></tr>
            <tr><td>STM32G030C8T6</td><td>ARM Cortex-M0+ MCU</td><td>STMicroelectronics</td><td>LQFP-48</td><td>75,000</td><td>$1.50</td></tr>
            <tr><td>STM32G031G8U6</td><td>ARM Cortex-M0+ MCU</td><td>STMicroelectronics</td><td>QFN-28</td><td>25,000</td><td>$1.20</td></tr>
        </table>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        scraper = JlcWebScraper()
        components = scraper._parse_html_table(soup, max_results=10)
        
        assert len(components) == 2
        assert components[0]["part_number"] == "STM32G030C8T6"
        assert components[0]["stock"] == 75000
        assert components[1]["part_number"] == "STM32G031G8U6"  
        assert components[1]["stock"] == 25000
    
    def test_parse_html_table_empty(self):
        """Test parsing empty HTML table."""
        html = "<table></table>"
        
        soup = BeautifulSoup(html, 'html.parser')
        scraper = JlcWebScraper()
        components = scraper._parse_html_table(soup, max_results=10)
        
        assert components == []
    
    def test_parse_table_row_valid(self):
        """Test parsing valid table row."""
        html = "<tr><td>STM32G030C8T6</td><td>ARM MCU</td><td>ST</td><td>LQFP-48</td><td>75,000</td><td>$1.50</td></tr>"
        soup = BeautifulSoup(html, 'html.parser')
        cells = soup.find('tr').find_all('td')
        
        scraper = JlcWebScraper()
        component = scraper._parse_table_row(cells)
        
        assert component is not None
        assert component["part_number"] == "STM32G030C8T6"
        assert component["description"] == "ARM MCU"
        assert component["manufacturer"] == "ST"
        assert component["package"] == "LQFP-48"
        assert component["stock"] == 75000
        assert component["price"] == "$1.50"
    
    def test_parse_table_row_insufficient_cells(self):
        """Test parsing table row with insufficient cells."""
        html = "<tr><td>STM32G030C8T6</td><td>ARM MCU</td></tr>"
        soup = BeautifulSoup(html, 'html.parser')
        cells = soup.find('tr').find_all('td')
        
        scraper = JlcWebScraper()
        component = scraper._parse_table_row(cells)
        
        assert component is None
    
    def test_extract_number_with_commas(self):
        """Test number extraction from formatted text."""
        scraper = JlcWebScraper()
        
        assert scraper._extract_number("75,000") == 75000
        assert scraper._extract_number("1,234,567") == 1234567
        assert scraper._extract_number("100") == 100
        assert scraper._extract_number("No stock") == 0
        assert scraper._extract_number("") == 0
    
    @patch.object(JlcWebScraper, 'search_components')
    def test_get_most_available_component(self, mock_search):
        """Test finding component with highest stock."""
        mock_search.return_value = [
            {"part_number": "STM32G030F6P6", "stock": 50000},
            {"part_number": "STM32G030C8T6", "stock": 75000},
            {"part_number": "STM32G031G8U6", "stock": 25000}
        ]
        
        scraper = JlcWebScraper()
        best_component = scraper.get_most_available_component("STM32G0")
        
        assert best_component["part_number"] == "STM32G030C8T6"
        assert best_component["stock"] == 75000
    
    @patch.object(JlcWebScraper, 'search_components')
    def test_get_most_available_component_no_stock(self, mock_search):
        """Test finding component when none have stock."""
        mock_search.return_value = [
            {"part_number": "STM32G030F6P6", "stock": 0},
            {"part_number": "STM32G030C8T6", "stock": 0}
        ]
        
        scraper = JlcWebScraper()
        best_component = scraper.get_most_available_component("STM32G0")
        
        # Should return first component if none have stock
        assert best_component["part_number"] == "STM32G030F6P6"
    
    @patch.object(JlcWebScraper, 'search_components')
    def test_get_most_available_component_empty_results(self, mock_search):
        """Test finding component with empty search results."""
        mock_search.return_value = []
        
        scraper = JlcWebScraper()
        best_component = scraper.get_most_available_component("STM32G0")
        
        assert best_component is None


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    @patch.object(JlcWebScraper, 'search_components')
    def test_search_jlc_components_web(self, mock_search):
        """Test web search convenience function."""
        mock_search.return_value = [{"part_number": "STM32G030C8T6"}]
        
        results = search_jlc_components_web("STM32G0", max_results=5)
        
        assert len(results) == 1
        assert results[0]["part_number"] == "STM32G030C8T6"
    
    @patch.object(JlcWebScraper, 'get_most_available_component')  
    def test_get_component_availability_web(self, mock_get_best):
        """Test availability check convenience function."""
        mock_get_best.return_value = {"part_number": "STM32G030C8T6", "stock": 75000}
        
        result = get_component_availability_web("STM32G0")
        
        assert result["part_number"] == "STM32G030C8T6"
        assert result["stock"] == 75000
    
    def test_enhance_component_with_web_data(self):
        """Test component enhancement with web-scraped data."""
        with patch('circuit_synth.jlc_integration.jlc_web_scraper.get_component_availability_web') as mock_get:
            mock_get.return_value = {
                "part_number": "STM32G030C8T6",
                "stock": 75000,
                "price": "$1.50"
            }
            
            result = enhance_component_with_web_data("MCU_ST_STM32G0:STM32G030C8T6", "")
            
            assert result["original_symbol"] == "MCU_ST_STM32G0:STM32G030C8T6"
            assert result["web_scraped_data"]["part_number"] == "STM32G030C8T6"
            assert result["data_source"] == "web_scraping"
            assert result["search_term_used"] == "STM32G030C8T6"


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @patch('requests.Session.get')
    def test_search_components_malformed_html(self, mock_get):
        """Test handling of malformed HTML."""
        mock_response = Mock()
        mock_response.text = "<html><body><table><tr><td>Broken HTML"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        scraper = JlcWebScraper()
        results = scraper.search_components("STM32G0")
        
        # Should handle malformed HTML gracefully
        assert isinstance(results, list)
    
    @patch('requests.Session.get')
    def test_search_components_timeout(self, mock_get):
        """Test handling of request timeout."""
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        scraper = JlcWebScraper()
        results = scraper.search_components("STM32G0")
        
        assert results == []
    
    def test_parse_table_row_exception(self):
        """Test table row parsing with exception."""
        # Create mock cells that will cause an exception
        mock_cells = [Mock() for _ in range(6)]
        mock_cells[0].get_text.side_effect = Exception("Parse error")
        
        scraper = JlcWebScraper()
        component = scraper._parse_table_row(mock_cells)
        
        assert component is None


class TestIntegrationScenarios:
    """Integration test scenarios for web scraping workflow."""
    
    @patch.object(JlcWebScraper, 'search_components')
    def test_full_web_scraping_workflow(self, mock_search):
        """Test complete web scraping workflow."""
        mock_search.return_value = [
            {
                "part_number": "STM32G030C8T6",
                "description": "ARM Cortex-M0+ MCU",
                "manufacturer": "STMicroelectronics",
                "stock": 75000,
                "price": "$1.50"
            }
        ]
        
        # Test the full workflow
        enhanced_data = enhance_component_with_web_data(
            "MCU_ST_STM32G0:STM32G030C8T6",
            ""
        )
        
        # Verify all expected fields are present
        assert enhanced_data["original_symbol"] == "MCU_ST_STM32G0:STM32G030C8T6"
        assert enhanced_data["web_scraped_data"]["stock"] == 75000
        assert enhanced_data["data_source"] == "web_scraping"
    
    @patch.object(JlcWebScraper, 'get_most_available_component')
    def test_error_handling_in_pipeline(self, mock_get_best):
        """Test error handling throughout the web scraping pipeline."""
        mock_get_best.side_effect = Exception("Scraping error")
        
        # Should handle errors gracefully
        enhanced_data = enhance_component_with_web_data("Device:R", "10K")
        
        assert enhanced_data["original_symbol"] == "Device:R"
        assert enhanced_data["web_scraped_data"] is None
        assert enhanced_data["data_source"] == "web_scraping"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])