#!/usr/bin/env python3
"""
Cross-platform Python script to set up KiCad symbols for CI testing.
Alternative to setup-ci-symbols.sh for Windows or environments without bash.
"""

import os
import ssl
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

# KiCad symbol libraries to download
SYMBOL_URLS = {
    "Device.kicad_sym": "https://gitlab.com/kicad/libraries/kicad-symbols/-/raw/master/Device.kicad_sym",
    "power.kicad_sym": "https://gitlab.com/kicad/libraries/kicad-symbols/-/raw/master/power.kicad_sym",
    "Regulator_Linear.kicad_sym": "https://gitlab.com/kicad/libraries/kicad-symbols/-/raw/master/Regulator_Linear.kicad_sym",
}


def get_ci_symbols_dir():
    """Get the appropriate directory for CI symbols based on platform."""
    if os.name == "nt":  # Windows
        # Use Windows temp directory
        temp_base = os.environ.get("TEMP", os.environ.get("TMP", tempfile.gettempdir()))
    else:
        # Unix-like (Linux, macOS)
        temp_base = "/tmp"

    symbols_dir = os.path.join(temp_base, "kicad-symbols-ci")
    return Path(symbols_dir)


def download_file(url, output_path):
    """Download a file with error handling."""
    try:
        print(f"⬇️  Downloading {output_path.name}...")

        # Create request with user agent to avoid 403 errors
        req = urllib.request.Request(
            url, headers={"User-Agent": "circuit-synth CI setup"}
        )

        # Create SSL context that's more permissive for CI environments
        ssl_context = ssl.create_default_context()
        # For CI environments with certificate issues, allow unverified connections
        # This is acceptable for downloading public KiCad symbols
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, context=ssl_context) as response:
            if response.status != 200:
                raise urllib.error.HTTPError(
                    url, response.status, f"HTTP {response.status}", None, None
                )

            content = response.read()

        # Write to file
        with open(output_path, "wb") as f:
            f.write(content)

        # Verify file size
        if output_path.stat().st_size == 0:
            raise ValueError("Downloaded file is empty")

        print(
            f"✅ Successfully downloaded {output_path.name} ({output_path.stat().st_size:,} bytes)"
        )
        return True

    except Exception as e:
        print(f"❌ Failed to download {output_path.name}: {e}")
        return False


def verify_symbols(symbols_dir):
    """Test that symbols can be loaded by circuit_synth."""
    try:
        # Set environment variable
        os.environ["KICAD_SYMBOL_DIR"] = str(symbols_dir)

        # Try to import and test
        from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache

        data = SymbolLibCache.get_symbol_data("Device:R")
        print(f'✅ Successfully loaded Device:R symbol with {len(data["pins"])} pins')
        return True

    except ImportError as e:
        print(
            f"⚠️  circuit_synth not installed - symbols downloaded but validation skipped"
        )
        print(f"   This is normal for CI setup phase. Error: {e}")
        return True  # Not an error for CI setup

    except Exception as e:
        print(f"❌ Failed to load symbol: {e}")
        return False


def main():
    """Main setup function."""
    print("🔧 Setting up KiCad symbols for CI testing...")

    # Get symbols directory
    symbols_dir = get_ci_symbols_dir()
    print(f"📁 Using symbols directory: {symbols_dir}")

    # Create directory
    symbols_dir.mkdir(parents=True, exist_ok=True)

    # Download all symbol libraries
    print("📋 Downloading symbol libraries...")
    success_count = 0

    for filename, url in SYMBOL_URLS.items():
        output_path = symbols_dir / filename
        if download_file(url, output_path):
            success_count += 1

    if success_count == 0:
        print("❌ Failed to download any symbol libraries!")
        return 1

    print(f"✅ Downloaded {success_count}/{len(SYMBOL_URLS)} symbol libraries")

    # Set environment variable
    print(f"🔗 Setting KICAD_SYMBOL_DIR={symbols_dir}")
    os.environ["KICAD_SYMBOL_DIR"] = str(symbols_dir)

    # Test symbol loading if possible
    print("🧪 Testing symbol access...")
    if not verify_symbols(symbols_dir):
        return 1

    # Print completion message
    print()
    print("✅ KiCad symbols setup complete for CI")
    print(f"📁 Symbols location: {symbols_dir}")
    print("🔧 Set KICAD_SYMBOL_DIR environment variable to use these symbols")
    print()

    # CI-specific instructions
    ci_detected = any(
        env in os.environ
        for env in ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "TRAVIS", "CIRCLECI"]
    )
    if ci_detected:
        print("🤖 CI Environment Detected")
        print("Add this to your CI configuration:")
        if os.name == "nt":
            print(f"   set KICAD_SYMBOL_DIR={symbols_dir}")
        else:
            print(f'   export KICAD_SYMBOL_DIR="{symbols_dir}"')
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
