"""
KiCad integration configuration and feature flags.

This module manages the transition between legacy KiCad integration
and the new kicad-sch-api based implementation.
"""

import os
from typing import Optional


class KiCadConfig:
    """Configuration manager for KiCad integration features."""
    
    # Feature flags for migration
    USE_MODERN_SCH_API = "USE_MODERN_SCH_API"
    
    @classmethod
    def use_modern_sch_api(cls) -> bool:
        """
        Check if modern kicad-sch-api should be used instead of legacy implementation.
        
        Returns:
            bool: True if modern API should be used, False for legacy
            
        Environment Variables:
            USE_MODERN_SCH_API: "true" to enable modern API, "false" for legacy
                               Defaults to "false" for backward compatibility
        """
        env_value = os.environ.get(cls.USE_MODERN_SCH_API, "false").lower()
        return env_value in ("true", "1", "yes", "on")
    
    @classmethod
    def set_modern_sch_api(cls, enabled: bool) -> None:
        """
        Set the modern schematic API flag.
        
        Args:
            enabled: True to enable modern API, False for legacy
        """
        os.environ[cls.USE_MODERN_SCH_API] = "true" if enabled else "false"
    
    @classmethod
    def get_sch_generator_type(cls) -> str:
        """
        Get the current schematic generator type.
        
        Returns:
            str: "modern" or "legacy"
        """
        return "modern" if cls.use_modern_sch_api() else "legacy"


def is_kicad_sch_api_available() -> bool:
    """
    Check if kicad-sch-api is available for import.
    
    Returns:
        bool: True if kicad-sch-api can be imported
    """
    try:
        import kicad_sch_api
        return True
    except ImportError:
        return False


def get_recommended_generator() -> str:
    """
    Get the recommended generator based on availability and configuration.
    
    Returns:
        str: "modern" if kicad-sch-api is available and enabled, "legacy" otherwise
    """
    if KiCadConfig.use_modern_sch_api() and is_kicad_sch_api_available():
        return "modern"
    return "legacy"


def validate_modern_api_requirements() -> Optional[str]:
    """
    Validate that modern API requirements are met.
    
    Returns:
        Optional[str]: Error message if requirements not met, None if valid
    """
    if not KiCadConfig.use_modern_sch_api():
        return None  # Not using modern API, no validation needed
    
    if not is_kicad_sch_api_available():
        return (
            "Modern schematic API is enabled but kicad-sch-api package is not available. "
            "Install with: pip install kicad-sch-api>=0.1.1"
        )
    
    # Check version if possible
    try:
        import kicad_sch_api
        version = getattr(kicad_sch_api, '__version__', None)
        if version:
            from packaging import version as ver
            # Note: kicad-sch-api 0.1.1 incorrectly reports version as 0.0.2
            # So we only warn for very old versions
            if ver.parse(version) < ver.parse('0.0.1'):
                return (
                    f"kicad-sch-api version {version} is too old. "
                    "Upgrade with: pip install kicad-sch-api>=0.1.1"
                )
    except ImportError:
        # packaging not available, skip version check
        pass
    except Exception:
        # Any other version checking error, skip
        pass
    
    return None