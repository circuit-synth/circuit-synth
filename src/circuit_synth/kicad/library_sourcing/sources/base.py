"""
Base class for library sources
"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional

from ..models import ComponentSearchResult, SearchQuery


class BaseLibrarySource(ABC):
    """Base class for all library sources"""

    def __init__(self):
        self.last_check: Optional[float] = None
        self._available: Optional[bool] = None

    @abstractmethod
    async def search(self, query: SearchQuery) -> List[ComponentSearchResult]:
        """Search for components matching the query"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this source is currently available"""
        pass

    async def health_check(self) -> bool:
        """Perform health check on the source"""
        try:
            # Basic availability test
            return self.is_available()
        except Exception:
            return False

    def get_source_info(self) -> dict:
        """Get information about this source"""
        return {
            "name": self.__class__.__name__,
            "available": self.is_available(),
            "last_check": self.last_check,
        }
