"""
Circuit-Synth: Open Source Circuit Synthesis Framework

A Python framework for programmatic circuit design with KiCad integration.

🤖 **Claude Code Integration Available**
For AI-powered circuit design with specialized agents:

    pip install circuit-synth[claude]
    setup-claude-integration

Or in Python:
    from circuit_synth import setup_claude_integration
    setup_claude_integration()
"""

__version__ = "0.10.12"


def print_version_info():
    """Print circuit-synth version information for debugging"""
    import subprocess
    import os
    from pathlib import Path

    print("=" * 60)
    print("Circuit-Synth Version Information")
    print("=" * 60)

    # Version
    print(f"Version: {__version__}")

    # Source location
    source_path = Path(__file__).parent
    print(f"Source: {source_path}")

    # Check if installed via pip or running from local source
    if "site-packages" in str(source_path):
        print("Install Type: pip/uv package")
    else:
        print("Install Type: local/editable source")

    # Git information (if available)
    try:
        git_dir = source_path.parent.parent  # Go up to repo root

        # Get current commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=git_dir,
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            commit_hash = result.stdout.strip()[:8]
            print(f"Git Commit: {commit_hash}")

            # Check if there's a tag at this commit
            tag_result = subprocess.run(
                ["git", "describe", "--exact-match", "--tags", "HEAD"],
                cwd=git_dir,
                capture_output=True,
                text=True,
                timeout=2
            )
            if tag_result.returncode == 0:
                print(f"Git Tag: {tag_result.stdout.strip()}")

            # Check for uncommitted changes
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=git_dir,
                capture_output=True,
                text=True,
                timeout=2
            )
            if status_result.returncode == 0:
                if status_result.stdout.strip():
                    print("Git Status: DIRTY (uncommitted changes)")
                else:
                    print("Git Status: CLEAN")
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        print("Git Info: Not available")

    print("=" * 60)


# Plugin integration
from .ai_integration.plugins import AIDesignBridge

# Dependency injection imports
# Exception imports
# Core imports
from .core import (
    Circuit,
    CircuitSynthError,
    Component,
    ComponentError,
    DependencyContainer,
    IDependencyContainer,
    Net,
    Pin,
    ServiceLocator,
    ValidationError,
    circuit,
)

# Annotation imports
from .core.annotations import (
    Graphic,
    Table,
    TextBox,
    TextProperty,
    add_image,
    add_table,
    add_text,
    add_text_box,
)
from .core.enhanced_netlist_exporter import EnhancedNetlistExporter

# KiCad integration and validation
from .core.kicad_validator import (
    KiCadValidationError,
    get_kicad_paths,
    require_kicad,
    validate_kicad_installation,
)
from .core.netlist_exporter import NetlistExporter

# Reference manager and netlist exporters
from .core.reference_manager import ReferenceManager

# Removed unused interface abstractions and unified integration


# Claude Code integration (optional)
def setup_claude_integration():
    """Setup Claude Code integration for professional circuit design"""
    try:
        from .ai_integration.claude import initialize_claude_integration

        initialize_claude_integration()
    except ImportError as e:
        print("⚠️  Claude Code integration not available.")
        print(
            "   For AI-powered circuit design, install with: pip install circuit-synth[claude]"
        )
        print(f"   Error: {e}")


# KiCad API imports
from .kicad.core import Junction, Label, Schematic, SchematicSymbol, Wire

__all__ = [
    # Core
    "Circuit",
    "Component",
    "Net",
    "Pin",
    "circuit",
    # Annotations
    "TextProperty",
    "TextBox",
    "Table",
    "Graphic",
    "add_text",
    "add_text_box",
    "add_table",
    "add_image",
    # Exceptions
    "ComponentError",
    "ValidationError",
    "CircuitSynthError",
    # Dependency injection
    "DependencyContainer",
    "ServiceLocator",
    "IDependencyContainer",
    # Removed unused interface abstractions
    # KiCad API
    "Schematic",
    "SchematicSymbol",
    "Wire",
    "Junction",
    "Label",
    # Reference manager and exporters
    "ReferenceManager",
    "NetlistExporter",
    "EnhancedNetlistExporter",
    # KiCad integration and validation
    "validate_kicad_installation",
    "require_kicad",
    "get_kicad_paths",
    "KiCadValidationError",
    # Claude Code integration
    "setup_claude_integration",
    # Version utilities
    "print_version_info",
]
