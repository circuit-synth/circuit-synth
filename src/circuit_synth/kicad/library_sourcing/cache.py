"""
Caching system for library sourcing results
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import ComponentSearchResult, LibrarySource, SearchQuery


class LibraryCache:
    """File-based cache for component search results"""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.cwd() / ".cache" / "kicad-library-sourcing"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = 3600  # 1 hour

    def get(self, query: SearchQuery) -> Optional[List[ComponentSearchResult]]:
        """Get cached results for query"""

        cache_key = self._get_cache_key(query)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r") as f:
                cached_data = json.load(f)

            # Check if cache is still valid
            cache_time = datetime.fromisoformat(cached_data["timestamp"])
            if datetime.now() - cache_time > timedelta(seconds=self.default_ttl):
                cache_file.unlink()  # Remove expired cache
                return None

            # Deserialize results
            results = []
            for result_data in cached_data["results"]:
                result = self._deserialize_result(result_data)
                results.append(result)

            return results

        except Exception as e:
            # Invalid cache file, remove it
            cache_file.unlink(missing_ok=True)
            return None

    def set(self, query: SearchQuery, results: List[ComponentSearchResult]):
        """Cache results for query"""

        cache_key = self._get_cache_key(query)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            # Serialize results
            serialized_results = []
            for result in results:
                serialized_results.append(self._serialize_result(result))

            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "query": {
                    "query": query.query,
                    "component_type": query.component_type,
                    "manufacturer": query.manufacturer,
                    "part_number": query.part_number,
                },
                "results": serialized_results,
            }

            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to cache results: {e}")

    def _get_cache_key(self, query: SearchQuery) -> str:
        """Generate cache key from query"""

        components = [
            query.query.lower(),
            query.component_type or "",
            query.manufacturer or "",
            query.part_number or "",
        ]

        # Create hash-like key from components
        cache_key = "_".join(components).replace(" ", "_").replace("/", "_")

        # Remove special characters
        cache_key = "".join(c for c in cache_key if c.isalnum() or c in "_-")

        return cache_key[:100]  # Limit length

    def _serialize_result(self, result: ComponentSearchResult) -> Dict[str, Any]:
        """Serialize ComponentSearchResult to dict"""

        return {
            "symbol_library": result.symbol_library,
            "symbol_name": result.symbol_name,
            "footprint_library": result.footprint_library,
            "footprint_name": result.footprint_name,
            "model_3d": result.model_3d,
            "description": result.description,
            "manufacturer": result.manufacturer,
            "part_number": result.part_number,
            "datasheet_url": result.datasheet_url,
            "source": result.source.value,
            "availability": result.availability,
            "price": result.price,
            "stock_level": result.stock_level,
            "supplier_links": result.supplier_links,
            "confidence_score": result.confidence_score,
            "verification_status": result.verification_status,
            "last_updated": (
                result.last_updated.isoformat() if result.last_updated else None
            ),
            "tags": result.tags,
            "specifications": result.specifications,
        }

    def _deserialize_result(self, data: Dict[str, Any]) -> ComponentSearchResult:
        """Deserialize dict to ComponentSearchResult"""

        return ComponentSearchResult(
            symbol_library=data.get("symbol_library"),
            symbol_name=data.get("symbol_name"),
            footprint_library=data.get("footprint_library"),
            footprint_name=data.get("footprint_name"),
            model_3d=data.get("model_3d"),
            description=data.get("description"),
            manufacturer=data.get("manufacturer"),
            part_number=data.get("part_number"),
            datasheet_url=data.get("datasheet_url"),
            source=LibrarySource(data.get("source")),
            availability=data.get("availability", True),
            price=data.get("price"),
            stock_level=data.get("stock_level"),
            supplier_links=data.get("supplier_links", []),
            confidence_score=data.get("confidence_score", 0.0),
            verification_status=data.get("verification_status"),
            last_updated=(
                datetime.fromisoformat(data["last_updated"])
                if data.get("last_updated")
                else None
            ),
            tags=data.get("tags", []),
            specifications=data.get("specifications", {}),
        )

    def clear_expired(self):
        """Remove expired cache entries"""

        current_time = datetime.now()

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r") as f:
                    cached_data = json.load(f)

                cache_time = datetime.fromisoformat(cached_data["timestamp"])
                if current_time - cache_time > timedelta(seconds=self.default_ttl):
                    cache_file.unlink()

            except Exception:
                # Invalid cache file, remove it
                cache_file.unlink(missing_ok=True)

    def clear_all(self):
        """Clear all cached results"""

        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink(missing_ok=True)
