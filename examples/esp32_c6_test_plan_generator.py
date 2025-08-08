#!/usr/bin/env python3
"""
Generate comprehensive test plan for ESP32-C6 Development Board
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from circuit_synth.ai_integration.claude.agents.test_plan_agent import (
    TestPlanGenerator,
    create_test_plan_from_circuit,
)


def main():
    """Generate test plan for ESP32-C6 Dev Board"""
    
    print("=" * 80)
    print("ESP32-C6 Development Board - Test Plan Generation")
    print("=" * 80)
    
    # Path to ESP32-C6 circuit JSON
    circuit_file = Path(__file__).parent.parent / "demos/02_esp32_devboard/ESP32_C6_Dev_Board.json"
    
    if not circuit_file.exists():
        print(f"Error: Circuit file not found: {circuit_file}")
        return
    
    print(f"\n📋 Analyzing circuit: {circuit_file.name}")
    print("-" * 80)
    
    # Load and analyze circuit
    with open(circuit_file, "r") as f:
        circuit_data = json.load(f)
    
    generator = TestPlanGenerator()
    
    # Analyze circuit
    print("\n🔍 Circuit Analysis:")
    analysis = generator.analyze_circuit(circuit_data)
    print(f"   - Power Rails: {len(analysis['power_rails'])}")
    print(f"   - Interfaces: {len(analysis['interfaces'])}")
    print(f"   - Component Types: {', '.join(analysis['component_types'])}")
    
    # Identify test points
    test_points = generator.identify_test_points(analysis)
    print(f"\n📍 Test Points Identified: {len(test_points)}")
    for tp in test_points[:5]:  # Show first 5
        nominal = f"{tp.nominal_value}V" if tp.nominal_value is not None else "N/A"
        print(f"   - {tp.id}: {tp.net_name} ({tp.signal_type}, {nominal})")
    if len(test_points) > 5:
        print(f"   ... and {len(test_points) - 5} more")
    
    # Generate comprehensive test plan
    print("\n📝 Generating Comprehensive Test Plan...")
    
    # All test categories for ESP32 board
    test_categories = ["functional", "performance", "safety", "manufacturing"]
    
    markdown_plan = create_test_plan_from_circuit(
        str(circuit_file),
        output_format="markdown",
        test_categories=test_categories
    )
    
    # Save test plan
    output_dir = Path(__file__).parent.parent / "ESP32_C6_Dev_Board"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "ESP32_C6_Test_Plan.md"
    with open(output_file, "w") as f:
        f.write(markdown_plan)
    
    print(f"   ✅ Markdown plan saved to: {output_file}")
    
    # Generate JSON version for automation
    json_plan = create_test_plan_from_circuit(
        str(circuit_file),
        output_format="json",
        test_categories=test_categories
    )
    
    json_output = output_dir / "ESP32_C6_Test_Plan.json"
    with open(json_output, "w") as f:
        f.write(json_plan)
    
    print(f"   ✅ JSON plan saved to: {json_output}")
    
    # Generate procedures
    procedures = generator.generate_test_procedures(analysis, test_points, test_categories)
    
    # Summary statistics
    print("\n📊 Test Plan Summary:")
    print(f"   - Total Test Procedures: {len(procedures)}")
    print(f"   - Total Test Points: {len(test_points)}")
    print(f"   - Estimated Duration: {sum(p.duration_minutes for p in procedures)} minutes")
    
    # Break down by category
    categories = {}
    for proc in procedures:
        if proc.category not in categories:
            categories[proc.category] = []
        categories[proc.category].append(proc)
    
    print("\n   Test Categories:")
    for category, procs in categories.items():
        duration = sum(p.duration_minutes for p in procs)
        print(f"   - {category.title()}: {len(procs)} tests ({duration} min)")
    
    # Show critical tests
    print("\n🔴 Critical Tests:")
    critical_tests = [
        p for p in procedures 
        if "power" in p.name.lower() or "esd" in p.name.lower() or "safety" in p.category
    ]
    for test in critical_tests[:5]:
        print(f"   - {test.test_id}: {test.name}")
    
    print("\n✨ ESP32-C6 test plan generation complete!")
    print(f"\n📁 Output files:")
    print(f"   - {output_file}")
    print(f"   - {json_output}")
    
    # Show snippet of the plan
    print("\n📄 Test Plan Preview:")
    print("-" * 80)
    lines = markdown_plan.split("\n")[:30]
    for line in lines:
        print(line)
    print("... (see full plan in generated file)")


if __name__ == "__main__":
    main()