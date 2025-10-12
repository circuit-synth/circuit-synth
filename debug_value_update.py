#!/usr/bin/env python3
"""
Debug script to understand why value updates are not propagating.
"""

import tempfile
import logging
from pathlib import Path

import kicad_sch_api as ksa
from circuit_synth import Component, Net, circuit
from kicad_sch_api.core.types import Point

# Enable DEBUG logging to see detailed messages
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__name__)

def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to tmpdir so files are created there
        import os
        original_dir = os.getcwd()
        os.chdir(tmpdir)

        print("\n" + "="*80)
        print("STEP 1: Generate initial circuit with R1=10k")
        print("="*80)

        @circuit(name="debug_test")
        def initial_circuit():
            r1 = Component("Device:R", ref="R1", value="10k")
            vcc = Net("VCC")
            gnd = Net("GND")
            r1[1] += vcc
            r1[2] += gnd
            return r1

        c = initial_circuit()
        # Pass just the project name, not a full path
        c.generate_kicad_project("debug_test", force_regenerate=True, generate_pcb=False)

        # Debug: List all files created
        print(f"\\n🔍 DEBUG: Listing files in tmpdir...")
        import os
        for root, dirs, files in os.walk(Path(tmpdir)):
            level = root.replace(str(tmpdir), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            sub_indent = ' ' * 2 * (level + 1)
            for file in files:
                full_path = Path(root) / file
                print(f'{sub_indent}{file} (full: {full_path})')

        # The schematic is in the debug_test subdirectory
        sch_path = Path(tmpdir) / "debug_test" / "debug_test.kicad_sch"
        print(f"\\n📁 Schematic path: {sch_path}")
        print(f"   Exists: {sch_path.exists()}")

        # Check initial value
        sch = ksa.Schematic.load(str(sch_path))
        r1 = sch.components.get("R1")
        print(f"\\n✅ STEP 1 RESULT:")
        print(f"   R1 value: {r1.value}")
        print(f"   R1 position: ({r1.position.x}, {r1.position.y})")

        print("\\n" + "="*80)
        print("STEP 2: Move R1 to new position")
        print("="*80)

        new_pos = Point(180.0, 120.0)
        r1.position = new_pos
        sch.save(str(sch_path), preserve_format=True)
        print(f"\\n✅ STEP 2 RESULT:")
        print(f"   R1 moved to: ({new_pos.x}, {new_pos.y})")

        print("\\n" + "="*80)
        print("STEP 3: Re-generate with R1=22k (UPDATE MODE)")
        print("="*80)

        @circuit(name="debug_test")
        def updated_circuit():
            r1 = Component("Device:R", ref="R1", value="22k")  # Changed value
            vcc = Net("VCC")
            gnd = Net("GND")
            r1[1] += vcc
            r1[2] += gnd
            return r1

        c2 = updated_circuit()
        print("\\n🔄 Calling generate_kicad_project with force_regenerate=False...")
        print(f"   Circuit name: {c2.name}")
        print(f"   Current dir: {os.getcwd()}")
        print(f"   .kicad_pro files: {list(Path('.').glob('**/*.kicad_pro'))}")
        print(f"   .kicad_sch files: {list(Path('.').glob('**/*.kicad_sch'))}")

        try:
            result = c2.generate_kicad_project("debug_test", force_regenerate=False, generate_pcb=False)
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   ERROR: {e}")
            import traceback
            traceback.print_exc()

        print("\\n" + "="*80)
        print("STEP 4: Verify results")
        print("="*80)

        # Reload and check
        sch_after = ksa.Schematic.load(str(sch_path))
        r1_after = sch_after.components.get("R1")

        print(f"\\n📊 FINAL RESULTS:")
        print(f"   R1 value: {r1_after.value}")
        print(f"   R1 position: ({r1_after.position.x}, {r1_after.position.y})")

        print(f"\\n🔍 ANALYSIS:")
        print(f"   Position preserved? {abs(r1_after.position.x - new_pos.x) < 0.01}")
        print(f"   Value updated? {r1_after.value == '22k'}")

        if r1_after.value == "22k" and abs(r1_after.position.x - new_pos.x) < 0.01:
            print("\\n✅✅✅ SUCCESS! Both position preserved AND value updated!")
        elif abs(r1_after.position.x - new_pos.x) < 0.01:
            print("\\n⚠️ PARTIAL: Position preserved but value NOT updated")
        else:
            print("\\n❌ FAILURE: Neither position nor value correct")

        # Restore original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    main()
