"""
JLC Parts Integration for Circuit-Synth

Provides component recommendations and manufacturability analysis based on 
JLC PCB parts availability and pricing data. Supports both API-based and 
web scraping approaches for maximum flexibility.
"""

from .jlc_parts_lookup import (
    JlcPartsInterface,
    recommend_jlc_component,
    get_component_alternatives,
    enhance_component_with_jlc_data,
    _calculate_manufacturability_score
)

from .jlc_web_scraper import (
    JlcWebScraper,
    search_jlc_components_web,
    get_component_availability_web,
    enhance_component_with_web_data
)

from .smart_component_finder import (
    SmartComponentFinder,
    ComponentRecommendation,
    find_component,
    find_components,
    print_component_recommendation
)

__all__ = [
    # API-based interface
    "JlcPartsInterface",
    "recommend_jlc_component", 
    "get_component_alternatives",
    "enhance_component_with_jlc_data",
    "_calculate_manufacturability_score",
    
    # Web scraping interface
    "JlcWebScraper",
    "search_jlc_components_web",
    "get_component_availability_web", 
    "enhance_component_with_web_data",
    
    # Smart component finder
    "SmartComponentFinder",
    "ComponentRecommendation", 
    "find_component",
    "find_components",
    "print_component_recommendation"
]