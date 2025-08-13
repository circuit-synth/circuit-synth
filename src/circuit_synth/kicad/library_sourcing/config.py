"""
Configuration management for library sourcing
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .models import LibrarySource, SourceConfig


class LibrarySourceConfig:
    """Manages configuration for library sources"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.cwd() / ".circuit-synth"
        self.config_file = self.config_dir / "library_sources.json"
        self.config_dir.mkdir(exist_ok=True)

        # Load or create default config
        self.config = self._load_or_create_config()

    def _load_or_create_config(self) -> Dict[str, Any]:
        """Load existing config or create default"""

        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass

        # Create default config
        default_config = {
            "sources": {
                "local_kicad": {"enabled": True, "priority": 1},
                "http_library": {"enabled": True, "priority": 2},
                "snapeda": {
                    "enabled": False,  # Requires API key
                    "priority": 3,
                    "api_key": None,
                    "free_tier": True,
                },
                "digikey": {
                    "enabled": False,  # Requires API credentials
                    "priority": 4,
                    "api_key": None,
                    "client_id": None,
                },
            },
            "cache": {
                "enabled": True,
                "ttl_seconds": 3600,
                "directory": ".cache/kicad-library-sourcing",
            },
            "search": {
                "max_results_per_source": 10,
                "timeout_seconds": 30,
                "fallback_threshold": 3,  # Trigger API search if < 3 local results
            },
        }

        self.save_config(default_config)
        return default_config

    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""

        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
            self.config = config
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get_source_config(self, source: LibrarySource) -> SourceConfig:
        """Get configuration for a specific source"""

        source_key = source.value
        source_data = self.config.get("sources", {}).get(source_key, {})

        return SourceConfig(
            source=source,
            enabled=source_data.get("enabled", False),
            priority=source_data.get("priority", 99),
            api_key=source_data.get("api_key"),
            access_token=source_data.get("access_token"),
            base_url=source_data.get("base_url"),
            timeout=self.config.get("search", {}).get("timeout_seconds", 30),
            cache_ttl=self.config.get("cache", {}).get("ttl_seconds", 3600),
        )

    def update_api_credentials(self, source: LibrarySource, **credentials):
        """Update API credentials for a source"""

        source_key = source.value
        if "sources" not in self.config:
            self.config["sources"] = {}
        if source_key not in self.config["sources"]:
            self.config["sources"][source_key] = {}

        # Update credentials
        self.config["sources"][source_key].update(credentials)
        self.config["sources"][source_key]["enabled"] = True

        self.save_config(self.config)

    def is_source_configured(self, source: LibrarySource) -> bool:
        """Check if source is properly configured"""

        if source == LibrarySource.LOCAL_KICAD:
            return True  # Always available

        source_data = self.config.get("sources", {}).get(source.value, {})

        if source == LibrarySource.SNAPEDA:
            return source_data.get("enabled", False)  # Can use free tier

        if source == LibrarySource.DIGIKEY_API:
            return (
                source_data.get("enabled", False)
                and source_data.get("api_key")
                and source_data.get("client_id")
            )

        if source == LibrarySource.HTTP_LIBRARY:
            return source_data.get("enabled", False)  # Depends on .kicad_httplib files

        return False

    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration"""
        return self.config.get(
            "cache",
            {
                "enabled": True,
                "ttl_seconds": 3600,
                "directory": ".cache/kicad-library-sourcing",
            },
        )

    def setup_wizard(self) -> str:
        """Generate setup instructions for user"""

        instructions = []
        instructions.append("# KiCad Library Sourcing Setup")
        instructions.append("")

        # Check current status
        local_ok = self.is_source_configured(LibrarySource.LOCAL_KICAD)
        snapeda_ok = self.is_source_configured(LibrarySource.SNAPEDA)
        digikey_ok = self.is_source_configured(LibrarySource.DIGIKEY_API)

        instructions.append("## Current Status")
        instructions.append(
            f"- Local KiCad: {'✅ Ready' if local_ok else '❌ Not found'}"
        )
        instructions.append(
            f"- SnapEDA: {'✅ Configured' if snapeda_ok else '⚙️ Setup needed'}"
        )
        instructions.append(
            f"- DigiKey: {'✅ Configured' if digikey_ok else '⚙️ Setup needed'}"
        )
        instructions.append("")

        if not snapeda_ok:
            instructions.append("## SnapEDA Setup (Optional)")
            instructions.append("1. Visit https://www.snapeda.com/api/")
            instructions.append("2. Sign up for free account")
            instructions.append("3. Get API key from dashboard")
            instructions.append("4. Run: `cs-setup-snapeda-api YOUR_API_KEY`")
            instructions.append("")

        if not digikey_ok:
            instructions.append("## DigiKey Setup (Optional)")
            instructions.append("1. Visit https://developer.digikey.com/")
            instructions.append("2. Create developer account")
            instructions.append("3. Create new application to get API key + Client ID")
            instructions.append(
                "4. Run: `cs-setup-digikey-api YOUR_API_KEY YOUR_CLIENT_ID`"
            )
            instructions.append("")

        instructions.append("## Usage")
        instructions.append("- `/find-symbol STM32F4` - Search with automatic fallback")
        instructions.append("- `/find-footprint LQFP` - Search with automatic fallback")
        instructions.append(
            "- Results show source: `[Local]`, `[SnapEDA]`, `[DigiKey]`"
        )

        return "\n".join(instructions)
