#!/usr/bin/env python3
"""
AI Design Assistant Manager for Circuit-Synth

Command-line tool to manage AI-powered design assistance and plugin integration.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

from circuit_synth.plugins.ai_design_bridge import get_ai_design_bridge


def cmd_status(args):
    """Show the status of AI design plugin integration."""
    bridge = get_ai_design_bridge()
    status = bridge.get_plugin_status()

    print("Circuit-Synth AI Design Assistant Status:")
    print("=" * 50)
    print(f"Platform: {status['platform']}")
    print(f"Plugin path: {status['plugin_path']}")
    print(f"Plugin exists: {'✓' if status['plugin_exists'] else '✗'}")
    print(f"KiCad plugin directory: {status['kicad_plugin_dir']}")
    print(f"Plugin installed: {'✓' if status['plugin_installed'] else '✗'}")

    if args.json:
        print("\nJSON Output:")
        print(json.dumps(status, indent=2))


def cmd_install(args):
    """Install the AI design plugin to KiCad."""
    bridge = get_ai_design_bridge()

    if bridge.is_plugin_installed():
        print("Circuit-Synth AI design plugin is already installed.")
        if not args.force:
            return
        print("Forcing reinstallation...")

    print("Installing Circuit-Synth AI design plugin...")
    if bridge.install_plugin():
        print("✓ Circuit-Synth AI design plugin installed successfully!")
        print("\nNext steps:")
        print("1. Restart KiCad")
        print("2. Open schematic or PCB editor")
        print("3. Look for 'Circuit-Synth AI' plugin in the Tools menu")
    else:
        print("✗ Failed to install AI design plugin")
        sys.exit(1)


def cmd_generate(args):
    """Generate circuit with AI assistance."""
    bridge = get_ai_design_bridge()

    # Parse optional constraints from command line
    constraints = {}
    if args.low_power:
        constraints["low_power"] = True
    if args.cost_sensitive:
        constraints["cost_sensitive"] = True
    if args.high_frequency:
        constraints["high_frequency"] = True

    result = bridge.generate_circuit_with_ai_assistance(args.description, constraints)

    print("AI-Assisted Circuit Template:")
    print("=" * 60)
    print(result["circuit_code"])

    # Show AI recommendations
    if args.show_recommendations:
        print("\nAI Design Recommendations:")
        print("-" * 40)
        recommendations = result["ai_recommendations"]

        if recommendations.get("design_recommendations"):
            print("\n🎯 Design Recommendations:")
            for rec in recommendations["design_recommendations"]:
                print(f"  • {rec}")

        if recommendations.get("suggested_components"):
            print("\n🔧 Suggested Components:")
            for comp in recommendations["suggested_components"]:
                print(f"  • {comp['type']}: {comp['suggestion']}")
                print(f"    Reasoning: {comp['reasoning']}")

        if recommendations.get("optimization_tips"):
            print("\n⚡ Optimization Tips:")
            for tip in recommendations["optimization_tips"]:
                print(f"  • {tip}")

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(result["circuit_code"])
        print(f"\nCircuit template saved to: {output_path}")


def cmd_analyze(args):
    """Analyze an existing circuit with AI assistance."""
    bridge = get_ai_design_bridge()
    circuit_file = Path(args.circuit_file)

    print(f"Analyzing circuit: {circuit_file}")
    analysis = bridge.analyze_existing_circuit(circuit_file)

    if "error" in analysis:
        print(f"✗ Error: {analysis['error']}")
        sys.exit(1)

    print("\nAI Circuit Analysis Results:")
    print("=" * 50)

    if analysis.get("suggestions"):
        print("\n💡 Suggestions:")
        for suggestion in analysis["suggestions"]:
            print(f"  • {suggestion}")

    if analysis.get("warnings"):
        print("\n⚠️  Warnings:")
        for warning in analysis["warnings"]:
            print(f"  • {warning}")

    if analysis.get("optimizations"):
        print("\n🚀 Optimizations:")
        for optimization in analysis["optimizations"]:
            print(f"  • {optimization}")

    if args.json:
        print("\nJSON Output:")
        print(json.dumps(analysis, indent=2))


def main():
    """Main entry point for the AI design manager."""
    parser = argparse.ArgumentParser(
        description="Manage Circuit-Synth AI design assistance",
        epilog="""
Examples:
  %(prog)s status                    # Show plugin status
  %(prog)s install                   # Install KiCad plugin
  %(prog)s generate "LED blinker circuit"  # Generate circuit template
  %(prog)s analyze circuit.py        # Analyze existing circuit
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show plugin status")
    status_parser.add_argument(
        "--json", action="store_true", help="Output status as JSON"
    )

    # Install command
    install_parser = subparsers.add_parser("install", help="Install plugin to KiCad")
    install_parser.add_argument(
        "--force", action="store_true", help="Force reinstallation if already installed"
    )

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate", help="Generate circuit template with AI assistance"
    )
    generate_parser.add_argument(
        "description", help="Natural language circuit description"
    )
    generate_parser.add_argument(
        "-o", "--output", help="Output file for generated circuit template"
    )
    generate_parser.add_argument(
        "--show-recommendations",
        action="store_true",
        help="Show detailed AI recommendations",
    )

    # Design constraints
    generate_parser.add_argument(
        "--low-power", action="store_true", help="Optimize for low power consumption"
    )
    generate_parser.add_argument(
        "--cost-sensitive",
        action="store_true",
        help="Optimize for cost (use JLCPCB parts)",
    )
    generate_parser.add_argument(
        "--high-frequency",
        action="store_true",
        help="Design for high frequency applications",
    )

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze existing circuit with AI assistance"
    )
    analyze_parser.add_argument(
        "circuit_file", help="Path to circuit file (Python or KiCad schematic)"
    )
    analyze_parser.add_argument(
        "--json", action="store_true", help="Output analysis as JSON"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Route to appropriate command handler
    command_handlers = {
        "status": cmd_status,
        "install": cmd_install,
        "generate": cmd_generate,
        "analyze": cmd_analyze,
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
