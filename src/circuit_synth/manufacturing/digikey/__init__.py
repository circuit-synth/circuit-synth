"""
DigiKey Integration for Circuit-Synth

Provides component search, pricing, and availability data from DigiKey's
extensive electronic components catalog. Supports direct API integration
with caching for optimal performance.

Features:
- Real-time component availability and pricing
- Parametric search and filtering
- Alternative component suggestions
- OAuth2 authentication with token caching
- Response caching for improved performance
"""

from .api_client import DigiKeyAPIClient, DigiKeyConfig, quick_search
from .cache import (
    DigiKeyCache,
    cached_digikey_product,
    cached_digikey_search,
    get_digikey_cache,
)
from .component_search import (
    DigiKeyComponent,
    DigiKeyComponentSearch,
    search_digikey_components,
)
from .config_manager import DigiKeyConfigManager, configure_digikey_cli

__all__ = [
    # API Client
    "DigiKeyAPIClient",
    "DigiKeyConfig",
    "quick_search",
    # Caching
    "DigiKeyCache",
    "get_digikey_cache",
    "cached_digikey_search",
    "cached_digikey_product",
    # Component Search
    "DigiKeyComponent",
    "DigiKeyComponentSearch",
    "search_digikey_components",
    # Configuration
    "DigiKeyConfigManager",
    "configure_digikey_cli",
]
