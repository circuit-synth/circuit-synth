#!/usr/bin/env python3
"""
Demo script for Test Plan Generation
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from circuit_synth.ai_integration.claude.agents.test_plan_agent import (
    TestPlanGenerator,
    create_test_plan_from_circuit,
)


def main():
    """Demonstrate test plan generation"""
    
    print("=" * 80)
    print("Circuit-Synth Test Plan Generator Demo")
    print("=" * 80)
    
    # Path to example circuit
    circuit_file = Path(__file__).parent / "test_plan_demo_circuit.json"
    
    if not circuit_file.exists():
        print(f"Error: Circuit file not found: {circuit_file}")
        return
    
    print(f"\n📋 Generating test plan for: {circuit_file.name}")
    print("-" * 80)
    
    # Generate markdown test plan
    print("\n1. Generating Markdown Test Plan...")
    markdown_plan = create_test_plan_from_circuit(
        str(circuit_file),
        output_format="markdown",
        test_categories=["functional", "performance", "safety", "manufacturing"]
    )
    
    # Save markdown plan
    output_file = Path(__file__).parent / "test_plan_output.md"
    with open(output_file, "w") as f:
        f.write(markdown_plan)
    
    print(f"   ✅ Saved to: {output_file}")
    
    # Show preview
    print("\n📄 Test Plan Preview (first 50 lines):")
    print("-" * 80)
    lines = markdown_plan.split("\n")[:50]
    for line in lines:
        print(line)
    print("... (truncated)")
    
    # Generate JSON test plan
    print("\n2. Generating JSON Test Plan...")
    json_plan = create_test_plan_from_circuit(
        str(circuit_file),
        output_format="json",
        test_categories=["functional", "safety"]
    )
    
    # Save JSON plan
    json_output = Path(__file__).parent / "test_plan_output.json"
    with open(json_output, "w") as f:
        f.write(json_plan)
    
    print(f"   ✅ Saved to: {json_output}")
    
    # Demonstrate direct API usage
    print("\n3. Using TestPlanGenerator API directly...")
    generator = TestPlanGenerator()
    
    # Show available equipment
    print("\n   Available Test Equipment:")
    for eq_id, equipment in generator.equipment_db.items():
        print(f"   - {equipment.name} ({eq_id})")
    
    print("\n✨ Test plan generation complete!")
    print(f"\nGenerated files:")
    print(f"  - {output_file}")
    print(f"  - {json_output}")


if __name__ == "__main__":
    main()