#!/usr/bin/env python3
"""
Smarton AI Plugin Manager for Circuit-Synth

Command-line tool to manage the Smarton AI KiCad plugin integration.
"""

import argparse
import sys
import json
from pathlib import Path

from circuit_synth.plugins.smarton_ai_bridge import get_smarton_ai_bridge


def cmd_status(args):
    """Show the status of Smarton AI plugin integration."""
    bridge = get_smarton_ai_bridge()
    status = bridge.get_plugin_status()
    
    print("Smarton AI Plugin Status:")
    print("=" * 40)
    print(f"Platform: {status['platform']}")
    print(f"Plugin path: {status['plugin_path']}")
    print(f"Plugin exists: {'✓' if status['plugin_exists'] else '✗'}")
    print(f"KiCad plugin directory: {status['kicad_plugin_dir']}")
    print(f"Plugin installed: {'✓' if status['plugin_installed'] else '✗'}")
    
    if args.json:
        print("\nJSON Output:")
        print(json.dumps(status, indent=2))


def cmd_install(args):
    """Install the Smarton AI plugin to KiCad."""
    bridge = get_smarton_ai_bridge()
    
    if bridge.is_plugin_installed():
        print("Smarton AI plugin is already installed.")
        if not args.force:
            return
        print("Forcing reinstallation...")
    
    print("Installing Smarton AI plugin...")
    if bridge.install_plugin():
        print("✓ Smarton AI plugin installed successfully!")
        print("\nNext steps:")
        print("1. Restart KiCad")
        print("2. Open PCB editor")
        print("3. Look for 'Basic Operation' and 'Chat' plugins in the Tools menu")
    else:
        print("✗ Failed to install Smarton AI plugin")
        sys.exit(1)


def cmd_generate(args):
    """Generate circuit with AI hints."""
    bridge = get_smarton_ai_bridge()
    
    result = bridge.generate_circuit_with_ai_hints(args.description)
    
    print("AI-Generated Circuit:")
    print("=" * 50)
    print(result["circuit_code"])
    
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(result["circuit_code"])
        print(f"\nCircuit saved to: {output_path}")


def main():
    """Main entry point for the Smarton AI manager."""
    parser = argparse.ArgumentParser(
        description="Manage Smarton AI KiCad plugin integration"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show plugin status")
    status_parser.add_argument("--json", action="store_true", 
                              help="Output status as JSON")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install plugin to KiCad")
    install_parser.add_argument("--force", action="store_true",
                               help="Force reinstallation if already installed")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", 
                                           help="Generate circuit with AI hints")
    generate_parser.add_argument("description", 
                                help="Natural language circuit description")
    generate_parser.add_argument("-o", "--output", 
                                help="Output file for generated circuit")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Route to appropriate command handler
    command_handlers = {
        "status": cmd_status,
        "install": cmd_install,
        "generate": cmd_generate
    }
    
    handler = command_handlers.get(args.command)
    if handler:
        try:
            handler(args)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()