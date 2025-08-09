"""
JLC Parts Integration for Circuit-Synth

Provides component recommendations and manufacturability analysis based on
JLC PCB parts availability and pricing data. Supports both API-based and
web scraping approaches for maximum flexibility.
"""

from .cache import JLCPCBCache, cached_jlcpcb_search, get_jlcpcb_cache
from .fast_search import (
    FastJLCSearch,
    FastSearchResult,
    fast_jlc_search,
    find_cheapest_jlc,
    find_most_available_jlc,
    get_fast_searcher,
)
from .jlc_parts_lookup import (
    JlcPartsInterface,
    _calculate_manufacturability_score,
    enhance_component_with_jlc_data,
    get_component_alternatives,
    recommend_jlc_component,
)
from .jlc_web_scraper import (
    JlcWebScraper,
    enhance_component_with_web_data,
    get_component_availability_web,
    search_jlc_components_web,
)
from .smart_component_finder import (
    ComponentRecommendation,
    SmartComponentFinder,
    find_component,
    find_components,
    print_component_recommendation,
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
    "print_component_recommendation",
    # Caching system
    "JLCPCBCache",
    "get_jlcpcb_cache",
    "cached_jlcpcb_search",
    # Fast search interface
    "FastJLCSearch",
    "FastSearchResult",
    "fast_jlc_search",
    "find_cheapest_jlc",
    "find_most_available_jlc",
    "get_fast_searcher",
]
