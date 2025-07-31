#!/usr/bin/env python3
"""
Circuit Creator CLI

Command-line interface for creating and managing pre-made circuits.
Users can create, register, and use custom circuits through this interface.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from ..agents.circuit_creator_agent import (
    circuit_creator,
    create_custom_circuit,
    list_circuits,
    register_circuit,
    use_circuit,
)


def create_circuit_interactive():
    """Interactive circuit creation workflow."""
    print("🎯 Circuit Creator - Interactive Mode")
    print("=" * 50)

    # Gather requirements
    print("\n📋 Circuit Requirements:")
    name = input("Circuit name: ").strip()
    if not name:
        print("❌ Circuit name is required!")
        return

    description = input("Description: ").strip()
    if not description:
        print("❌ Description is required!")
        return

    print(f"\n📂 Available categories:")
    categories = [
        "power",
        "microcontrollers",
        "sensors",
        "interfaces",
        "complete_boards",
        "custom",
    ]
    for i, cat in enumerate(categories, 1):
        print(f"  {i}. {cat}")

    try:
        cat_choice = int(input("Select category (1-6): ").strip()) - 1
        category = categories[cat_choice]
    except (ValueError, IndexError):
        print("❌ Invalid category selection!")
        return

    print(f"\n🔧 Component Requirements:")
    print("Enter component types (one per line, empty line to finish):")
    print("Examples: microcontroller, voltage_regulator, imu, usb_connector, crystal")

    components = []
    while True:
        comp = input(f"Component {len(components) + 1}: ").strip()
        if not comp:
            break
        components.append(comp)

    if not components:
        print("❌ At least one component is required!")
        return

    # Create circuit
    requirements = {
        "name": name,
        "description": description,
        "category": category,
        "components": components,
    }

    print(f"\n🔄 Creating circuit...")
    result = create_custom_circuit(requirements)

    if result["success"]:
        print(f"✅ Circuit created successfully!")
        print(f"📊 Found {len(result['components'])} components")

        # Show component suggestions
        print(f"\n🔍 Component Suggestions:")
        for comp in result["components"]:
            stock_status = (
                "✅" if comp["stock"] > 100 else "⚠️" if comp["stock"] > 0 else "❌"
            )
            print(
                f"  {stock_status} {comp['part_number']}: {comp['description']} (Stock: {comp['stock']})"
            )

        # Show generated code preview
        code_lines = result["circuit_code"].split("\n")
        print(f"\n📝 Generated Code Preview:")
        print("```python")
        for line in code_lines[:20]:  # First 20 lines
            print(line)
        if len(code_lines) > 20:
            print(f"... ({len(code_lines) - 20} more lines)")
        print("```")

        # Ask if user wants to register
        register_choice = (
            input(f"\n💾 Register this circuit for reuse? (y/N): ").strip().lower()
        )
        if register_choice in ["y", "yes"]:
            registration = circuit_creator.register_circuit(
                name, result["circuit_code"], requirements, result["components"]
            )

            if registration["success"]:
                print(f"✅ Circuit registered successfully!")
                print(f"📂 Circuit ID: {registration['circuit_id']}")
                print(f"📄 File: {registration['file_path']}")
                print(f"📚 Documentation: {registration['documentation_path']}")
            else:
                print(
                    f"❌ Registration failed: {registration.get('error', 'Unknown error')}"
                )
        else:
            print(
                f"ℹ️  Circuit created but not registered. You can register it later if needed."
            )

    else:
        print(f"❌ Circuit creation failed: {result['error']}")
        if "details" in result:
            for detail in result["details"]:
                print(f"   • {detail}")


def create_circuit_from_file(file_path: str):
    """Create circuit from JSON requirements file."""
    try:
        with open(file_path, "r") as f:
            requirements = json.load(f)

        print(f"🎯 Creating circuit from {file_path}")
        result = create_custom_circuit(requirements)

        if result["success"]:
            print(f"✅ Circuit '{requirements['name']}' created successfully!")

            # Auto-register if requested
            if requirements.get("auto_register", False):
                registration = circuit_creator.register_circuit(
                    requirements["name"],
                    result["circuit_code"],
                    requirements,
                    result["components"],
                )

                if registration["success"]:
                    print(
                        f"✅ Circuit registered with ID: {registration['circuit_id']}"
                    )
                else:
                    print(
                        f"❌ Registration failed: {registration.get('error', 'Unknown error')}"
                    )
        else:
            print(f"❌ Circuit creation failed: {result['error']}")
            sys.exit(1)

    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {e}")
        sys.exit(1)


def list_circuits_cli(category: str = None):
    """List registered circuits."""
    circuits = list_circuits(category)

    if not circuits:
        category_msg = f" in category '{category}'" if category else ""
        print(f"📭 No circuits found{category_msg}")
        return

    print(f"📚 Registered Circuits")
    if category:
        print(f"   Category: {category}")
    print("=" * 60)

    for circuit in circuits:
        print(f"🔧 {circuit['name']}")
        print(f"   ID: {circuit['id']}")
        print(f"   Description: {circuit['description']}")
        print(f"   Components: {circuit['component_count']}")
        print(f"   Used: {circuit['usage_count']} times")
        print(f"   Created: {circuit['created'][:10]}")
        print()


def use_circuit_cli(circuit_id: str):
    """Use a registered circuit."""
    result = use_circuit(circuit_id)

    if result["success"]:
        circuit_info = result["circuit_info"]
        print(f"✅ Using circuit: {circuit_info['name']}")
        print(f"📄 Description: {circuit_info['description']}")
        print(f"📂 File: {result['file_path']}")

        print(f"\n📋 Usage Instructions:")
        for instruction in result["usage_instructions"]:
            print(f"   • {instruction}")

        print(f"\n🔧 Components ({len(circuit_info.get('components', []))}):")
        for comp in circuit_info.get("components", []):
            print(f"   • {comp['part_number']}: {comp['description']}")

    else:
        print(f"❌ {result['error']}")
        sys.exit(1)


def create_example_requirements_file():
    """Create an example requirements file."""
    example = {
        "name": "STM32 IMU Board",
        "description": "STM32 microcontroller with IMU sensor and USB-C power",
        "category": "complete_boards",
        "components": [
            "microcontroller",
            "imu",
            "usb_connector",
            "voltage_regulator",
            "crystal",
        ],
        "auto_register": True,
        "notes": "This is an example requirements file for the Circuit Creator Agent",
    }

    filename = "example_circuit_requirements.json"
    with open(filename, "w") as f:
        json.dump(example, f, indent=2)

    print(f"✅ Created example requirements file: {filename}")
    print(f"📝 Edit this file and use: circuit-creator --file {filename}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Circuit Creator - Create and manage pre-made circuits",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  circuit-creator --interactive          # Interactive circuit creation
  circuit-creator --file requirements.json    # Create from file
  circuit-creator --list                 # List all circuits
  circuit-creator --list --category sensors   # List circuits in category
  circuit-creator --use power.basic_ldo  # Use a registered circuit
  circuit-creator --example              # Create example requirements file
        """,
    )

    # Action arguments (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive circuit creation"
    )
    action_group.add_argument(
        "--file", "-f", type=str, help="Create circuit from JSON requirements file"
    )
    action_group.add_argument(
        "--list", "-l", action="store_true", help="List registered circuits"
    )
    action_group.add_argument(
        "--use", "-u", type=str, help="Use a registered circuit (provide circuit ID)"
    )
    action_group.add_argument(
        "--example", "-e", action="store_true", help="Create example requirements file"
    )

    # Optional arguments
    parser.add_argument(
        "--category", "-c", type=str, help="Filter by category (for --list)"
    )
    parser.add_argument(
        "--circuits-dir",
        type=str,
        help="Directory for circuit library (default: ./circuits_library)",
    )

    args = parser.parse_args()

    # Set circuits directory if provided
    if args.circuits_dir:
        circuit_creator.circuits_dir = Path(args.circuits_dir)
        circuit_creator.circuits_dir.mkdir(exist_ok=True)
        circuit_creator.registry_file = (
            circuit_creator.circuits_dir / "circuit_registry.json"
        )
        circuit_creator.registry = circuit_creator.load_registry()

    # Execute actions
    try:
        if args.interactive:
            create_circuit_interactive()
        elif args.file:
            create_circuit_from_file(args.file)
        elif args.list:
            list_circuits_cli(args.category)
        elif args.use:
            use_circuit_cli(args.use)
        elif args.example:
            create_example_requirements_file()

    except KeyboardInterrupt:
        print(f"\n\n👋 Circuit Creator interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
