"""
Data models for KiCad library sourcing system
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SourcePriority(Enum):
    """Priority levels for library sources"""

    LOCAL = 1  # Local KiCad installation
    DIGIKEY_GITHUB = 2  # DigiKey GitHub open source library
    HTTP = 3  # KiCad HTTP libraries
    SNAPEDA = 4  # SnapEDA API
    DIGIKEY_API = 5  # DigiKey API
    ULTRA = 6  # Ultra Librarian


class LibrarySource(Enum):
    """Available library sources"""

    LOCAL_KICAD = "local_kicad"
    DIGIKEY_GITHUB = "digikey_github"
    HTTP_LIBRARY = "http_library"
    SNAPEDA = "snapeda"
    DIGIKEY_API = "digikey_api"
    ULTRA_LIBRARIAN = "ultra_librarian"


@dataclass
class ComponentSearchResult:
    """Result from component search across sources"""

    # Required fields first
    source: LibrarySource

    # Component identification
    symbol_library: Optional[str] = None
    symbol_name: Optional[str] = None
    footprint_library: Optional[str] = None
    footprint_name: Optional[str] = None
    model_3d: Optional[str] = None

    # Component metadata
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    part_number: Optional[str] = None
    datasheet_url: Optional[str] = None

    # Sourcing information
    availability: bool = True
    price: Optional[float] = None
    stock_level: Optional[int] = None
    supplier_links: List[str] = None

    # Quality metrics
    confidence_score: float = 0.0  # 0.0 to 1.0
    verification_status: Optional[str] = None
    last_updated: Optional[datetime] = None

    # Additional metadata
    tags: List[str] = None
    specifications: Dict[str, Any] = None

    def __post_init__(self):
        if self.supplier_links is None:
            self.supplier_links = []
        if self.tags is None:
            self.tags = []
        if self.specifications is None:
            self.specifications = {}

    @property
    def symbol_ref(self) -> Optional[str]:
        """Get KiCad symbol reference in LibraryName:SymbolName format"""
        if self.symbol_library and self.symbol_name:
            return f"{self.symbol_library}:{self.symbol_name}"
        return None

    @property
    def footprint_ref(self) -> Optional[str]:
        """Get KiCad footprint reference in LibraryName:FootprintName format"""
        if self.footprint_library and self.footprint_name:
            return f"{self.footprint_library}:{self.footprint_name}"
        return None

    @property
    def is_complete(self) -> bool:
        """Check if result has both symbol and footprint"""
        return bool(self.symbol_ref and self.footprint_ref)


@dataclass
class SearchQuery:
    """Search query for component sourcing"""

    # Primary search terms
    query: str
    component_type: Optional[str] = None  # resistor, capacitor, ic, etc.

    # Filtering criteria
    manufacturer: Optional[str] = None
    part_number: Optional[str] = None
    package: Optional[str] = None

    # Search preferences
    preferred_sources: List[LibrarySource] = None
    require_availability: bool = False
    max_results: int = 10

    # Quality requirements
    min_confidence: float = 0.5
    require_datasheet: bool = False

    def __post_init__(self):
        if self.preferred_sources is None:
            self.preferred_sources = [
                LibrarySource.LOCAL_KICAD,
                LibrarySource.DIGIKEY_GITHUB,
                LibrarySource.HTTP_LIBRARY,
                LibrarySource.SNAPEDA,
                LibrarySource.DIGIKEY_API,
            ]


@dataclass
class SourceConfig:
    """Configuration for a library source"""

    source: LibrarySource
    enabled: bool = True
    priority: int = 1

    # Authentication
    api_key: Optional[str] = None
    access_token: Optional[str] = None

    # Source-specific settings
    base_url: Optional[str] = None
    timeout: int = 30
    cache_ttl: int = 3600  # Cache time-to-live in seconds

    # Rate limiting
    max_requests_per_minute: int = 60

    # Quality filters
    min_confidence_threshold: float = 0.6
