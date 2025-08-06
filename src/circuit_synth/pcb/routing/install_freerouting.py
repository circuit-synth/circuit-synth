#!/usr/bin/env python3
"""
Freerouting Installation Helper Script

This script helps download and set up Freerouting for use with Circuit Synth.

Author: Circuit Synth Team
Date: 2025-06-23
"""

import os
import platform
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path


def get_platform_info():
    """Get platform information"""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        system = "macos"

    if machine in ["x86_64", "amd64"]:
        machine = "x64"

    return system, machine


def check_java():
    """Check if Java is installed"""
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Java is installed")
            print(f"  {result.stderr.strip().split(chr(10))[0]}")
            return True
    except FileNotFoundError:
        pass

    print("✗ Java is not installed")
    print("  Please install Java 21 JRE from:")
    print("  https://www.oracle.com/java/technologies/downloads/")
    return False


def get_download_url(version="2.1.0"):
    """Get the appropriate download URL for the platform"""
    system, machine = get_platform_info()

    base_url = (
        f"https://github.com/freerouting/freerouting/releases/download/v{version}"
    )

    urls = {
        ("windows", "x64"): f"{base_url}/freerouting-{version}-windows-x64.msi",
        ("linux", "x64"): f"{base_url}/freerouting-{version}-linux-x64.zip",
        ("macos", "x64"): f"{base_url}/freerouting-{version}-macos-x64.dmg",
    }

    # JAR file as fallback
    jar_url = f"{base_url}/freerouting-{version}.jar"

    return urls.get((system, machine), jar_url), system


def download_file(url, destination):
    """Download a file with progress indicator"""
    print(f"Downloading from: {url}")

    def download_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(downloaded * 100 / total_size, 100)
        bar_length = 40
        filled_length = int(bar_length * percent // 100)
        bar = "█" * filled_length + "-" * (bar_length - filled_length)
        sys.stdout.write(f"\r|{bar}| {percent:.1f}% ")
        sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, destination, reporthook=download_progress)
        print("\n✓ Download complete")
        return True
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return False


def install_freerouting(install_dir=None):
    """Main installation function"""
    print("Freerouting Installation Helper")
    print("=" * 50)

    # Check Java first
    if not check_java():
        print("\nPlease install Java first, then run this script again.")
        return False

    # Determine installation directory
    if install_dir is None:
        if platform.system() == "Windows":
            install_dir = Path.home() / "AppData" / "Local" / "freerouting"
        else:
            install_dir = Path.home() / "freerouting"
    else:
        install_dir = Path(install_dir)

    install_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nInstallation directory: {install_dir}")

    # Get download URL
    url, system = get_download_url()
    filename = url.split("/")[-1]
    download_path = install_dir / filename

    # Check if already downloaded
    if download_path.exists():
        print(f"✓ {filename} already exists")
        response = input("Download again? (y/N): ").lower()
        if response != "y":
            print("\nUsing existing file.")
            return str(download_path)

    # Download Freerouting
    print(f"\nDownloading Freerouting v2.1.0...")
    if not download_file(url, str(download_path)):
        return False

    # Platform-specific installation
    if filename.endswith(".jar"):
        print("\n✓ JAR file downloaded successfully")
        print(f"  Location: {download_path}")
        print("\nTo run Freerouting:")
        print(f"  java -jar {download_path}")

        # Create convenience script
        if platform.system() != "Windows":
            script_path = install_dir / "freerouting.sh"
            with open(script_path, "w") as f:
                f.write(f'#!/bin/bash\njava -jar {download_path} "$@"\n')
            os.chmod(script_path, 0o755)
            print(f"\n✓ Created launch script: {script_path}")
        else:
            script_path = install_dir / "freerouting.bat"
            with open(script_path, "w") as f:
                f.write(f"@echo off\njava -jar {download_path} %*\n")
            print(f"\n✓ Created launch script: {script_path}")

    elif filename.endswith(".zip"):
        print("\nExtracting ZIP file...")
        with zipfile.ZipFile(download_path, "r") as zip_ref:
            zip_ref.extractall(install_dir)
        print("✓ Extraction complete")

    elif filename.endswith(".dmg"):
        print("\n✓ DMG downloaded successfully")
        print("  Please open the DMG file and drag Freerouting to Applications")
        print(f"  Location: {download_path}")

    elif filename.endswith(".msi"):
        print("\n✓ MSI installer downloaded successfully")
        print("  Please run the installer to complete installation")
        print(f"  Location: {download_path}")
        response = input("\nRun installer now? (Y/n): ").lower()
        if response != "n":
            subprocess.run(["msiexec", "/i", str(download_path)])

    # Update Circuit Synth configuration
    print("\n" + "=" * 50)
    print("Installation complete!")
    print("\nTo use with Circuit Synth, the runner will automatically find Freerouting")
    print("in the following locations:")
    print(f"  - {install_dir / 'freerouting.jar'}")
    print(f"  - {install_dir / 'freerouting-2.1.0.jar'}")

    if platform.system() != "Windows":
        print(f"  - {install_dir / 'freerouting.sh'}")

    return str(download_path)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Install Freerouting for Circuit Synth"
    )
    parser.add_argument(
        "-d", "--directory", help="Installation directory (default: ~/freerouting)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check if Freerouting is installed",
    )

    args = parser.parse_args()

    if args.check_only:
        # Just check installation
        # FreeroutingRunner functionality removed with kicad_api cleanup
        class FreeroutingRunner:
            def is_installed(self):
                return False

        runner = FreeroutingRunner()
        if runner.config.freerouting_jar:
            print(f"✓ Freerouting found at: {runner.config.freerouting_jar}")
            return 0
        else:
            print("✗ Freerouting not found")
            print("  Run without --check-only to install")
            return 1

    # Run installation
    result = install_freerouting(args.directory)
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
