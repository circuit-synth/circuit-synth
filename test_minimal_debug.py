#!/usr/bin/env python3
"""
Minimal debug test - simplest possible case to trace execution.
"""

import tempfile
import logging
from pathlib import Path

# Enable DEBUG logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

import kicad_sch_api as ksa
from circuit_synth import Component, Net, circuit
from kicad_sch_api.core.types import Point

print("\n" + "="*80)
print("MINIMAL DEBUG TEST - STARTING")
print("="*80)

with tempfile.TemporaryDirectory() as tmpdir:
    import os
    original_dir = os.getcwd()

    # Change to tmpdir
    os.chdir(tmpdir)
    print(f"\n📁 Working in temporary directory: {tmpdir}")

    # =========================================================================
    # STEP 1: Generate initial circuit
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 1: Generate initial circuit with R1=10k")
    print("="*80)

    @circuit(name="minimal_test")
    def initial_circuit():
        r1 = Component("Device:R", ref="R1", value="10k")
        vcc = Net("VCC")
        gnd = Net("GND")
        r1[1] += vcc
        r1[2] += gnd
        return r1

    c = initial_circuit()
    print(f"📊 Circuit created: {c.name}")
    print(f"📊 Components: {[comp.ref for comp in c.components]}")

    print("\n🔧 Calling generate_kicad_project(force_regenerate=True)...")
    c.generate_kicad_project("minimal_test", force_regenerate=True, generate_pcb=False)
    print("✅ Initial generation completed")

    # Find schematic path
    sch_path = Path(tmpdir) / "minimal_test" / "minimal_test.kicad_sch"
    print(f"\n📁 Schematic path: {sch_path}")
    print(f"   Exists: {sch_path.exists()}")

    if not sch_path.exists():
        print("❌ ERROR: Schematic file not created!")
        os.chdir(original_dir)
        exit(1)

    # Verify initial value
    sch = ksa.Schematic.load(str(sch_path))
    r1 = sch.components.get("R1")
    print(f"\n✅ Initial R1 value: {r1.value}")
    print(f"   Initial R1 position: ({r1.position.x}, {r1.position.y})")

    # =========================================================================
    # STEP 2: Move component manually
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 2: Move R1 to new position (simulating manual KiCad edit)")
    print("="*80)

    new_pos = Point(180.0, 120.0)
    r1.position = new_pos
    sch.save(str(sch_path), preserve_format=True)
    print(f"✅ R1 moved to: ({new_pos.x}, {new_pos.y})")

    # =========================================================================
    # STEP 3: Re-generate with updated value (UPDATE MODE)
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 3: Re-generate with R1=22k (UPDATE MODE - force_regenerate=False)")
    print("="*80)

    @circuit(name="minimal_test")
    def updated_circuit():
        r1 = Component("Device:R", ref="R1", value="22k")  # Changed value!
        vcc = Net("VCC")
        gnd = Net("GND")
        r1[1] += vcc
        r1[2] += gnd
        return r1

    c2 = updated_circuit()
    print(f"\n📊 Updated circuit created: {c2.name}")
    print(f"📊 Components: {[comp.ref for comp in c2.components]}")
    print(f"📊 R1 value in circuit: {c2.components[0].value}")

    print("\n🔧 Calling generate_kicad_project(force_regenerate=False)...")
    print("   (This should preserve position AND update value)")

    try:
        c2.generate_kicad_project("minimal_test", force_regenerate=False, generate_pcb=False)
        print("✅ Update generation returned")
    except Exception as e:
        print(f"❌ ERROR during update: {e}")
        import traceback
        traceback.print_exc()
        os.chdir(original_dir)
        exit(1)

    # =========================================================================
    # STEP 4: Verify results
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 4: Verify results")
    print("="*80)

    # Reload schematic and check
    sch_after = ksa.Schematic.load(str(sch_path))
    r1_after = sch_after.components.get("R1")

    print(f"\n📊 FINAL RESULTS:")
    print(f"   R1 value: {r1_after.value}")
    print(f"   R1 position: ({r1_after.position.x}, {r1_after.position.y})")

    print(f"\n🔍 ANALYSIS:")
    position_preserved = abs(r1_after.position.x - new_pos.x) < 0.01
    value_updated = r1_after.value == "22k"

    print(f"   Position preserved? {position_preserved}")
    print(f"   Value updated? {value_updated}")

    # =========================================================================
    # FINAL VERDICT
    # =========================================================================
    print("\n" + "="*80)
    if position_preserved and value_updated:
        print("✅✅✅ SUCCESS! Both position preserved AND value updated!")
        print("="*80)
        exit_code = 0
    elif position_preserved:
        print("⚠️ PARTIAL: Position preserved but value NOT updated")
        print(f"   Expected value: '22k', Got: '{r1_after.value}'")
        print("="*80)
        exit_code = 1
    else:
        print("❌ FAILURE: Neither position nor value correct")
        print("="*80)
        exit_code = 2

    # Restore original directory
    os.chdir(original_dir)
    exit(exit_code)
