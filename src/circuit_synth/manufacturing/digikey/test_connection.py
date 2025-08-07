#!/usr/bin/env python3
"""
Test DigiKey API Connection

Simple script to verify DigiKey API credentials and connection.
"""

import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def test_digikey_connection():
    """Test DigiKey API connection and credentials."""
    print("\n" + "=" * 60)
    print("Testing DigiKey API Connection")
    print("=" * 60)

    # Try to import and configure
    try:
        from .api_client import DigiKeyAPIClient, DigiKeyConfig
        from .config_manager import DigiKeyConfigManager
    except ImportError:
        from api_client import DigiKeyAPIClient, DigiKeyConfig
        from config_manager import DigiKeyConfigManager

    # Check configuration sources
    print("\nChecking configuration sources...")

    # Check for config file
    config_paths = DigiKeyConfigManager.get_config_paths()
    config_file_found = False
    for path in config_paths:
        if path.exists():
            print(f"✅ Config file found: {path}")
            config_file_found = True
            break

    if not config_file_found:
        print("ℹ️  No config file found")

    # Check environment variables
    import os

    if os.environ.get("DIGIKEY_CLIENT_ID"):
        print("✅ Environment variable DIGIKEY_CLIENT_ID is set")
    else:
        print("ℹ️  Environment variable DIGIKEY_CLIENT_ID not set")

    if os.environ.get("DIGIKEY_CLIENT_SECRET"):
        print("✅ Environment variable DIGIKEY_CLIENT_SECRET is set")
    else:
        print("ℹ️  Environment variable DIGIKEY_CLIENT_SECRET not set")

    # Try to get configuration
    print("\nAttempting to load configuration...")
    try:
        config_dict = DigiKeyConfigManager.get_config()
        print("✅ Configuration loaded successfully")

        # Show config (without secret)
        print(f"\nConfiguration:")
        print(
            f"  Client ID: {config_dict['client_id'][:10]}..."
            if len(config_dict["client_id"]) > 10
            else f"  Client ID: {config_dict['client_id']}"
        )
        print(f"  Sandbox Mode: {config_dict.get('sandbox_mode', False)}")

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print(
            "\nRun 'python -m circuit_synth.manufacturing.digikey.config_manager' to set up credentials"
        )
        return False

    # Try to create client
    print("\nCreating API client...")
    try:
        config = DigiKeyConfig.from_environment()
        client = DigiKeyAPIClient(config)
        print("✅ API client created successfully")
    except Exception as e:
        print(f"❌ Failed to create API client: {e}")
        return False

    # Try to get access token
    print("\nTesting OAuth authentication...")
    try:
        token = client._get_access_token()
        if token:
            print("✅ Successfully obtained access token")
            print(f"  Token (first 10 chars): {token[:10]}...")
        else:
            print("❌ Failed to obtain access token")
            return False
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\nPossible issues:")
        print("1. Invalid Client ID or Client Secret")
        print("2. Network connection problems")
        print("3. DigiKey API service issues")
        return False

    # Try a simple search
    print("\nTesting API search...")
    try:
        results = client.search_products("1N4148", record_count=1)
        if results and "Products" in results:
            product_count = len(results["Products"])
            print(f"✅ Search successful! Found {product_count} product(s)")

            if product_count > 0:
                product = results["Products"][0]
                print(f"\nSample result:")
                print(f"  Part: {product.get('ManufacturerPartNumber', 'N/A')}")
                print(
                    f"  Description: {product.get('Description', {}).get('Value', 'N/A')}"
                )
                print(f"  Stock: {product.get('QuantityOnHand', 0)}")
        else:
            print("⚠️  Search returned no results (might be sandbox mode)")

    except Exception as e:
        print(f"❌ Search failed: {e}")
        return False

    # Check cache
    print("\nChecking cache system...")
    cache_dir = config.cache_dir
    if cache_dir and cache_dir.exists():
        print(f"✅ Cache directory exists: {cache_dir}")

        # Count cache files
        search_cache = cache_dir / "searches"
        product_cache = cache_dir / "products"

        if search_cache.exists():
            search_count = len(list(search_cache.glob("*.json")))
            print(f"  Search cache: {search_count} files")

        if product_cache.exists():
            product_count = len(list(product_cache.glob("*.json")))
            print(f"  Product cache: {product_count} files")
    else:
        print(f"ℹ️  Cache directory not yet created: {cache_dir}")

    print("\n" + "=" * 60)
    print("✅ DigiKey API connection test PASSED!")
    print("=" * 60)
    print("\nYour DigiKey integration is ready to use.")
    print("\nTry running: python examples/digikey_example.py")

    return True


def main():
    """Main entry point."""
    success = test_digikey_connection()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
