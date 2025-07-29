#!/usr/bin/env python3
"""
JLC Parts Web Scraper for Circuit-Synth

Uses web scraping to get real-time component data from JLCPCB without API keys.
This provides an alternative to the API-based approach.

WARNING: Web scraping should be used responsibly and in compliance with website terms of service.
Consider rate limiting and caching to minimize server load.
"""

import json
import time
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class JlcWebScraper:
    """
    Web scraper for JLCPCB component search without API keys.
    
    Uses the public search interface to get component data.
    """
    
    def __init__(self, delay_seconds: float = 1.0):
        """
        Initialize web scraper.
        
        Args:
            delay_seconds: Delay between requests to be respectful to server
        """
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def search_components(self, search_term: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search for components on JLCPCB website.
        
        Args:
            search_term: Search query (e.g., "STM32G0")
            max_results: Maximum number of results to return
            
        Returns:
            List of component dictionaries with available data
        """
        try:
            # Construct search URL
            encoded_term = quote(search_term)
            url = f"https://jlcpcb.com/parts/componentSearch?searchTxt={encoded_term}"
            
            logger.info(f"Searching JLCPCB for: {search_term}")
            
            # Make request with delay to be respectful
            time.sleep(self.delay_seconds)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse the response
            components = self._parse_search_results(response.text, max_results)
            
            logger.info(f"Found {len(components)} components for '{search_term}'")
            return components
            
        except requests.RequestException as e:
            logger.error(f"Error fetching search results: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
            return []
    
    def _parse_search_results(self, html_content: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Parse HTML content to extract component data.
        
        Args:
            html_content: Raw HTML from search page
            max_results: Maximum components to extract
            
        Returns:
            List of parsed component data
        """
        components = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for component data in script tags (common pattern for dynamic content)
            script_tags = soup.find_all('script')
            
            for script in script_tags:
                if script.string and 'componentInfos' in script.string:
                    # Try to extract JSON data from JavaScript
                    components.extend(self._extract_json_data(script.string, max_results))
                    break
            
            # If no data found in scripts, try parsing HTML table/div structure
            if not components:
                components = self._parse_html_table(soup, max_results)
                
        except Exception as e:
            logger.error(f"Error parsing HTML content: {e}")
            
        return components[:max_results]
    
    def _extract_json_data(self, script_content: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Extract component data from JavaScript variables.
        
        Args:
            script_content: JavaScript code content
            max_results: Maximum components to extract
            
        Returns:
            List of component data dictionaries
        """
        components = []
        
        try:
            # Look for common patterns where component data is stored
            patterns = [
                'componentInfos',
                'searchResults', 
                'partsList',
                'components'
            ]
            
            for pattern in patterns:
                if pattern in script_content:
                    # This is a simplified approach - real implementation would need
                    # more sophisticated JavaScript parsing
                    logger.info(f"Found potential data pattern: {pattern}")
                    break
                    
        except Exception as e:
            logger.error(f"Error extracting JSON data: {e}")
            
        return components
    
    def _parse_html_table(self, soup: BeautifulSoup, max_results: int) -> List[Dict[str, Any]]:
        """
        Parse component data from HTML table structure.
        
        Args:
            soup: BeautifulSoup parsed HTML
            max_results: Maximum components to extract
            
        Returns:
            List of component data dictionaries
        """
        components = []
        
        try:
            # Look for component tables or lists
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header row
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:  # Minimum expected columns
                        component = self._parse_table_row(cells)
                        if component:
                            components.append(component)
                            if len(components) >= max_results:
                                break
                                
        except Exception as e:
            logger.error(f"Error parsing HTML table: {e}")
            
        return components
    
    def _parse_table_row(self, cells) -> Optional[Dict[str, Any]]:
        """
        Parse a single table row to extract component data.
        
        Args:
            cells: List of table cells
            
        Returns:
            Component data dictionary or None
        """
        try:
            # This is a placeholder - actual implementation would need to
            # match the specific HTML structure of JLCPCB results
            if len(cells) >= 5:
                return {
                    "part_number": cells[0].get_text(strip=True),
                    "description": cells[1].get_text(strip=True),
                    "manufacturer": cells[2].get_text(strip=True),
                    "package": cells[3].get_text(strip=True),
                    "stock": self._extract_number(cells[4].get_text(strip=True)),
                    "price": cells[5].get_text(strip=True) if len(cells) > 5 else "N/A"
                }
        except Exception as e:
            logger.debug(f"Error parsing table row: {e}")
            
        return None
    
    def _extract_number(self, text: str) -> int:
        """Extract numeric value from text string."""
        try:
            # Remove commas and other formatting
            clean_text = ''.join(c for c in text if c.isdigit())
            return int(clean_text) if clean_text else 0
        except ValueError:
            return 0
    
    def get_most_available_component(self, search_term: str) -> Optional[Dict[str, Any]]:
        """
        Find the component with highest stock for given search term.
        
        Args:
            search_term: Search query
            
        Returns:
            Component with highest stock or None
        """
        components = self.search_components(search_term, max_results=100)
        
        if not components:
            return None
            
        # Sort by stock (assuming stock field exists)
        components_with_stock = [c for c in components if c.get('stock', 0) > 0]
        if components_with_stock:
            return max(components_with_stock, key=lambda x: x.get('stock', 0))
            
        return components[0] if components else None


def search_jlc_components_web(search_term: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """
    Convenience function to search JLC components via web scraping.
    
    Args:
        search_term: Component to search for
        max_results: Maximum results to return
        
    Returns:
        List of component data dictionaries
    """
    scraper = JlcWebScraper(delay_seconds=1.0)
    return scraper.search_components(search_term, max_results)


def get_component_availability_web(search_term: str) -> Optional[Dict[str, Any]]:
    """
    Get the most available component via web scraping.
    
    Args:
        search_term: Component to search for
        
    Returns:
        Most available component or None
    """
    try:
        scraper = JlcWebScraper(delay_seconds=1.0)
        return scraper.get_most_available_component(search_term)
    except Exception as e:
        logger.error(f"Error getting component availability: {e}")
        return None


# Integration with existing circuit-synth JLC module
def enhance_component_with_web_data(component_symbol: str, component_value: str = "") -> Dict[str, Any]:
    """
    Enhance circuit-synth component with web-scraped JLC data.
    
    Args:
        component_symbol: KiCad symbol name
        component_value: Component value
        
    Returns:
        Enhanced component data with web-scraped recommendations
    """
    # Extract search term from symbol
    if ":" in component_symbol:
        search_term = component_symbol.split(":", 1)[1]
    else:
        search_term = component_symbol
        
    if component_value:
        search_term = f"{search_term} {component_value}"
        
    web_data = get_component_availability_web(search_term)
    
    return {
        "original_symbol": component_symbol,
        "original_value": component_value,
        "web_scraped_data": web_data,
        "search_term_used": search_term,
        "data_source": "web_scraping"
    }


if __name__ == "__main__":
    # Test the web scraper
    logging.basicConfig(level=logging.INFO)
    
    print("Testing JLC web scraper...")
    
    # Test search
    results = search_jlc_components_web("STM32G0", max_results=5)
    print(f"Found {len(results)} components")
    
    for i, component in enumerate(results):
        print(f"{i+1}. {component}")
    
    # Test most available
    best_component = get_component_availability_web("STM32G0")
    if best_component:
        print(f"Most available: {best_component}")
    else:
        print("No components found or scraping needs refinement")