#!/usr/bin/env python3
"""
Cache Clearing Utility for Circuit Synth Testing

"""

import argparse
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import List, Optional

# Add the src directory to the path so we can import circuit_synth
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from circuit_synth.kicad_api.core.symbol_cache import get_symbol_cache
    from circuit_synth.kicad_api.pcb.footprint_library import get_footprint_cache
except ImportError as e:
    print(f"Warning: Could not import Circuit Synth modules: {e}")
    print("This script should be run from the Circuit Synth root directory")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CacheCleaner:
    """Utility class for clearing various cache types"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.cache_locations = self._discover_cache_locations()
    
    def _discover_cache_locations(self) -> dict:
        """Discover all cache locations in the project"""
        locations = {
            'python_symbol_cache': [],
            'python_footprint_cache': [],
            'temp_caches': [],
            'kicad_caches': []
        }
        
        # Common cache directories
        cache_dirs = [
            self.project_root / ".cache",
            self.project_root / "cache",
            self.project_root / "tmp",
            self.project_root / "temp",
            Path.home() / ".cache" / "circuit_synth",
            Path.home() / ".circuit_synth",
        ]
        
        ]
        
        # Look for KiCad project caches
        kicad_cache_patterns = [
            "**/*.kicad_sym-cache",
            "**/*-cache.lib",
            "**/*.bak",
            "**/fp-info-cache",
            "**/*.pretty.cache",
        ]
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                locations['temp_caches'].append(cache_dir)
        
        
        # Find KiCad cache files
        for pattern in kicad_cache_patterns:
            for cache_file in self.project_root.glob(pattern):
                locations['kicad_caches'].append(cache_file)
        
        return locations
    
    def clear_python_caches(self) -> bool:
        """Clear Python-based caches"""
        logger.info("Clearing Python caches...")
        success = True
        
        try:
            # Try to clear symbol cache if available
            try:
                symbol_cache = get_symbol_cache()
                if hasattr(symbol_cache, 'clear_cache'):
                    symbol_cache.clear_cache()
                    logger.info("✓ Python symbol cache cleared")
                elif hasattr(symbol_cache, '_cache'):
                    symbol_cache._cache.clear()
                    logger.info("✓ Python symbol cache cleared (fallback method)")
            except Exception as e:
                logger.warning(f"Could not clear Python symbol cache: {e}")
            
            # Try to clear footprint cache if available
            try:
                footprint_cache = get_footprint_cache()
                if hasattr(footprint_cache, 'clear_cache'):
                    footprint_cache.clear_cache()
                    logger.info("✓ Python footprint cache cleared")
                elif hasattr(footprint_cache, '_cache'):
                    footprint_cache._cache.clear()
                    logger.info("✓ Python footprint cache cleared (fallback method)")
            except Exception as e:
                logger.warning(f"Could not clear Python footprint cache: {e}")
            
            # Clear Python __pycache__ directories
            pycache_dirs = list(self.project_root.glob("**/__pycache__"))
            for pycache_dir in pycache_dirs:
                shutil.rmtree(pycache_dir, ignore_errors=True)
            
            if pycache_dirs:
                logger.info(f"✓ Cleared {len(pycache_dirs)} __pycache__ directories")
            
        except Exception as e:
            logger.error(f"Error clearing Python caches: {e}")
            success = False
        
        return success
    
        success = True
        
        try:
            ]
            
                if cache_dir.exists():
                    if cache_dir.is_file():
                        cache_dir.unlink()
                    else:
                        shutil.rmtree(cache_dir, ignore_errors=True)
            
            
                    try:
                        cache_file.unlink()
                    except Exception as e:
                        logger.warning(f"Could not remove {cache_file}: {e}")
        
        except Exception as e:
            success = False
        
        return success
    
    def clear_kicad_caches(self) -> bool:
        """Clear KiCad-related cache files"""
        logger.info("Clearing KiCad caches...")
        success = True
        
        try:
            for cache_file in self.cache_locations['kicad_caches']:
                try:
                    if cache_file.is_file():
                        cache_file.unlink()
                    else:
                        shutil.rmtree(cache_file, ignore_errors=True)
                    logger.info(f"✓ KiCad cache cleared: {cache_file}")
                except Exception as e:
                    logger.warning(f"Could not clear {cache_file}: {e}")
        
        except Exception as e:
            logger.error(f"Error clearing KiCad caches: {e}")
            success = False
        
        return success
    
    def clear_temp_caches(self) -> bool:
        """Clear temporary cache directories"""
        logger.info("Clearing temporary caches...")
        success = True
        
        try:
            for cache_dir in self.cache_locations['temp_caches']:
                try:
                    if cache_dir.exists():
                        shutil.rmtree(cache_dir, ignore_errors=True)
                        logger.info(f"✓ Temporary cache cleared: {cache_dir}")
                except Exception as e:
                    logger.warning(f"Could not clear {cache_dir}: {e}")
        
        except Exception as e:
            logger.error(f"Error clearing temporary caches: {e}")
            success = False
        
        return success
    
    def clear_all_caches(self) -> bool:
        """Clear all cache types"""
        logger.info("=" * 60)
        logger.info("CLEARING ALL CACHES")
        logger.info("=" * 60)
        
        results = []
        results.append(self.clear_python_caches())
        results.append(self.clear_kicad_caches())
        results.append(self.clear_temp_caches())
        
        success = all(results)
        
        if success:
            logger.info("✅ All caches cleared successfully!")
        else:
            logger.warning("⚠️  Some caches could not be cleared completely")
        
        return success
    
    def list_cache_locations(self):
        """List all discovered cache locations"""
        logger.info("=" * 60)
        logger.info("DISCOVERED CACHE LOCATIONS")
        logger.info("=" * 60)
        
        for cache_type, locations in self.cache_locations.items():
            if locations:
                logger.info(f"\n{cache_type.upper()}:")
                for location in locations:
                    status = "EXISTS" if Path(location).exists() else "NOT FOUND"
                    logger.info(f"  - {location} ({status})")
            else:
                logger.info(f"\n{cache_type.upper()}: No locations found")


def main():
    parser = argparse.ArgumentParser(
        description="Clear Circuit Synth caches for testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python clear_caches.py --all                 # Clear all caches
  python clear_caches.py --list                # List cache locations
  python clear_caches.py --kicad               # Clear only KiCad caches
        """
    )
    
    parser.add_argument('--all', action='store_true',
                       help='Clear all cache types')
    parser.add_argument('--python', action='store_true',
                       help='Clear Python caches')
    parser.add_argument('--kicad', action='store_true',
                       help='Clear KiCad caches')
    parser.add_argument('--temp', action='store_true',
                       help='Clear temporary caches')
    parser.add_argument('--list', action='store_true',
                       help='List all cache locations without clearing')
    parser.add_argument('--project-root', type=Path,
                       default=Path(__file__).parent.parent.parent,
                       help='Project root directory (default: auto-detect)')
    
    args = parser.parse_args()
    
    # Validate project root
    project_root = args.project_root.resolve()
    if not project_root.exists():
        logger.error(f"Project root does not exist: {project_root}")
        return 1
    
    cleaner = CacheCleaner(project_root)
    
    if args.list:
        cleaner.list_cache_locations()
        return 0
    
    # If no specific cache type is specified, default to all
        args.all = True
    
    success = True
    
    if args.all:
        success = cleaner.clear_all_caches()
    else:
        if args.python:
            success &= cleaner.clear_python_caches()
        if args.kicad:
            success &= cleaner.clear_kicad_caches()
        if args.temp:
            success &= cleaner.clear_temp_caches()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())