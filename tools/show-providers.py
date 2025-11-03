#!/usr/bin/env python3
"""
Display configured AI providers and their status
"""

import sys
import tomllib
from pathlib import Path

# Add parent to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / 'adws'))

from adw_modules.providers import ProviderManager

CONFIG_FILE = REPO_ROOT / 'adws' / 'config.toml'


def main():
    # Load config
    with open(CONFIG_FILE, 'rb') as f:
        config = tomllib.load(f)

    # Initialize provider manager
    provider_manager = ProviderManager(config)

    print("=" * 70)
    print("🔌 Configured AI Providers")
    print("=" * 70)
    print()

    provider_manager.print_status()

    print()
    print("=" * 70)
    print("Available Providers:")
    available = provider_manager.get_available_providers()
    if available:
        for provider in available:
            print(f"  ✓ {provider.name}")
    else:
        print("  ⚠️  No providers available")

    print()
    print("Current default:")
    print(f"  Provider: {config['llm']['provider']}")
    print(f"  Model: {config['llm']['model_default']}")
    print("=" * 70)


if __name__ == '__main__':
    main()
