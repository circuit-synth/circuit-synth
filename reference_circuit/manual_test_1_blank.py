#!/usr/bin/env python3
"""
Manual Test 1: Generate a blank schematic
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from circuit_synth import *

@circuit(name="blank_test")
def blank_test():
    """A blank schematic circuit."""
    pass

def main():
    print("Manual Test 1: Blank Schematic")
    print("=" * 40)
    
    # Generate blank schematic
    circuit = blank_test()
    circuit.generate_kicad_project(project_name="manual_blank")
    
    # Check result
    schematic_path = Path("manual_blank/manual_blank.kicad_sch")
    if schematic_path.exists():
        with open(schematic_path, 'r') as f:
            content = f.read()
        
        print(f"✅ Generated: {schematic_path}")
        print(f"📊 File size: {len(content)} characters")
        print(f"📊 Symbol count: {content.count('(symbol')}")
        print("\n📄 File content:")
        print(content)
    else:
        print("❌ Failed to generate schematic")

if __name__ == "__main__":
    main()