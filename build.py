#!/usr/bin/env python3
"""
Custom build script for circuit-synth

This script copies the example_project template from the repository root
to the package data directory before building the package.

Usage:
    python build.py        # Copy template and build
    python build.py clean  # Remove copied template
"""

import shutil
import sys
from pathlib import Path


def get_paths():
    """Get source and destination paths for template"""
    repo_root = Path(__file__).parent
    source = repo_root / "example_project"
    dest = repo_root / "src" / "circuit_synth" / "data" / "templates" / "example_project"
    return repo_root, source, dest


def copy_template():
    """Copy template from root to package data"""
    repo_root, source, dest = get_paths()

    print(f"📋 Copying template from {source.relative_to(Path.cwd())}")
    print(f"   → to {dest.relative_to(Path.cwd())}")

    if not source.exists():
        print(f"❌ Source template not found: {source}")
        sys.exit(1)

    # Remove destination if it exists
    if dest.exists():
        print(f"🗑️  Removing existing packaged template...")
        shutil.rmtree(dest)

    # Copy the template
    shutil.copytree(source, dest, dirs_exist_ok=True)
    print("✅ Template copied successfully")

    # Also copy .claude/ directory into the template for PyPI builds
    source_claude = repo_root / ".claude"
    dest_claude = dest / ".claude"
    if source_claude.exists():
        if dest_claude.exists():
            shutil.rmtree(dest_claude)
        shutil.copytree(source_claude, dest_claude)
        claude_count = sum(1 for _ in dest_claude.rglob("*") if _.is_file())
        print(f"✅ Copied .claude/ directory ({claude_count} files)")
    else:
        print("⚠️  No .claude/ directory found at repo root")

    # Report file count
    file_count = sum(1 for _ in dest.rglob("*") if _.is_file())
    print(f"📁 Copied {file_count} files total")


def clean_template():
    """Remove the copied template"""
    _, _, dest = get_paths()

    if dest.exists():
        print(f"🗑️  Removing packaged template: {dest.relative_to(Path.cwd())}")
        shutil.rmtree(dest)
        print("✅ Cleaned successfully")
    else:
        print(f"ℹ️  No packaged template to clean")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_template()
    else:
        copy_template()


if __name__ == "__main__":
    main()
