#!/usr/bin/env python3
"""
Interactive Demo: KiCad Schematic Surgical Operations

This script demonstrates the surgical add/remove capabilities
with user interaction and file inspection between each step.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from src.circuit_synth.kicad.schematic.schematic_surgeon import (
    KiCadSchematicSurgeon,
    ComponentInfo,
    HierarchicalLabel,
)

def open_file_with_default_app(file_path):
    """Open file with the default system application"""
    try:
        if sys.platform.startswith('darwin'):  # macOS
            subprocess.run(['open', str(file_path)], check=True)
        elif sys.platform.startswith('linux'):  # Linux
            subprocess.run(['xdg-open', str(file_path)], check=True)
        elif sys.platform.startswith('win'):  # Windows
            os.startfile(str(file_path))
        else:
            print(f"Please manually open: {file_path}")
    except Exception as e:
        print(f"Could not open file automatically: {e}")
        print(f"Please manually open: {file_path}")

def wait_for_user(message="Press Enter to continue..."):
    """Wait for user input with a custom message"""
    print(f"\n{message}")
    input()

def create_initial_schematic(file_path):
    """Create a basic empty KiCad schematic"""
    content = """(kicad_sch (version 20231120) (generator "circuit-synth")
  (uuid "demo-0000-0000-0000-000000000000")
  (paper "A4")
  
  (title_block
    (title "Surgical Operations Demo")
    (date "2025-01-27")
    (company "Circuit-Synth")
    (comment 1 "Interactive demonstration of surgical add/remove operations")
  )
)"""
    
    with open(file_path, 'w') as f:
        f.write(content)

def print_stats(surgeon):
    """Print current schematic statistics"""
    components = surgeon.get_components()
    labels = surgeon.get_hierarchical_labels()  # Returns list of strings
    
    print(f"\n📊 Current Schematic Stats:")
    print(f"   Components: {len(components)}")
    for comp in components:
        print(f"     - {comp.reference}: {comp.symbol} = {comp.value}")
    
    print(f"   Hierarchical Labels: {len(labels)}")
    for label_name in labels:
        print(f"     - {label_name}")
    
    stats = surgeon.get_statistics()
    print(f"   File size: {stats['file_size']} characters")

def main():
    """Main interactive demo"""
    print("🎯 KiCad Schematic Surgical Operations Demo")
    print("=" * 50)
    print("This demo will show you how to surgically modify KiCad schematics.")
    print("You'll be able to inspect the schematic file after each operation.")
    print()
    
    # Create demo directory
    demo_dir = Path.cwd() / "surgical_demo"
    demo_dir.mkdir(exist_ok=True)
    
    schematic_path = demo_dir / "demo.kicad_sch"
    
    try:
        # Step 1: Create initial schematic
        print("Step 1: Creating Initial Empty Schematic")
        print("-" * 40)
        create_initial_schematic(schematic_path)
        
        print(f"✅ Created empty schematic: {schematic_path}")
        print("Opening schematic for inspection...")
        open_file_with_default_app(schematic_path)
        
        wait_for_user("📋 Please check that the empty schematic opens in KiCad. Press Enter when ready...")
        
        # Initialize surgeon
        surgeon = KiCadSchematicSurgeon(schematic_path)
        print_stats(surgeon)
        
        # Step 2: Add first component (Resistor)
        print("\n\nStep 2: Adding First Component (R1 - 10k Resistor)")
        print("-" * 50)
        
        r1 = ComponentInfo(
            symbol="Device:R",
            value="10k", 
            reference="R1",
            position=(50.8, 50.8)  # 2 inches from origin
        )
        
        success = surgeon.add_component(r1, placement="manual")
        print(f"✅ Add R1 result: {success}")
        
        if success:
            surgeon.save()
            print_stats(surgeon)
            print("Opening updated schematic...")
            open_file_with_default_app(schematic_path)
            wait_for_user("📋 Check that R1 (10k resistor) appears in the schematic. Press Enter when ready...")
        else:
            print("❌ Failed to add R1")
            return
        
        # Step 3: Add second component (Capacitor)
        print("\n\nStep 3: Adding Second Component (C1 - 100nF Capacitor)")
        print("-" * 52)
        
        c1 = ComponentInfo(
            symbol="Device:C",
            value="100nF",
            reference="C1",
            position=(76.2, 50.8)  # 1 inch to the right of R1
        )
        
        success = surgeon.add_component(c1, placement="manual")
        print(f"✅ Add C1 result: {success}")
        
        if success:
            surgeon.save()
            print_stats(surgeon)
            print("Opening updated schematic...")
            open_file_with_default_app(schematic_path)
            wait_for_user("📋 Check that C1 (100nF capacitor) appears next to R1. Press Enter when ready...")
        else:
            print("❌ Failed to add C1")
            return
            
        # Step 4: Add third component (Op-Amp)
        print("\n\nStep 4: Adding Third Component (U1 - Op-Amp)")
        print("-" * 42)
        
        u1 = ComponentInfo(
            symbol="Amplifier_Operational:LM358",
            value="LM358",
            reference="U1",
            position=(101.6, 60.96)  # Below and right of other components
        )
        
        success = surgeon.add_component(u1, placement="manual")
        print(f"✅ Add U1 result: {success}")
        
        if success:
            surgeon.save() 
            print_stats(surgeon)
            print("Opening updated schematic...")
            open_file_with_default_app(schematic_path)
            wait_for_user("📋 Check that U1 (LM358 op-amp) appears in the schematic. Press Enter when ready...")
        else:
            print("❌ Failed to add U1")
            return
            
        # Step 5: Add fourth component with auto-placement
        print("\n\nStep 5: Adding Fourth Component with Auto-Placement (R2 - 1k)")
        print("-" * 60)
        
        r2 = ComponentInfo(
            symbol="Device:R",
            value="1k",
            reference="R2"
            # No position specified - will use auto-placement
        )
        
        success = surgeon.add_component(r2, placement="auto")
        print(f"✅ Add R2 result: {success}")
        
        if success:
            surgeon.save()
            print_stats(surgeon)
            print("Opening updated schematic...")
            open_file_with_default_app(schematic_path)
            wait_for_user("📋 Check that R2 (1k resistor) was automatically placed. Press Enter when ready...")
        else:
            print("❌ Failed to add R2")
            return
        
        # Step 6: Add hierarchical labels
        print("\n\nStep 6: Adding Hierarchical Labels for Nets")
        print("-" * 40)
        
        labels_to_add = [
            HierarchicalLabel(name="VCC", position=(25.4, 25.4), shape="input"),
            HierarchicalLabel(name="GND", position=(25.4, 35.56), shape="input"),
            HierarchicalLabel(name="SIGNAL_IN", position=(25.4, 45.72), shape="input"),
            HierarchicalLabel(name="SIGNAL_OUT", position=(127.0, 45.72), shape="output"),
        ]
        
        for label in labels_to_add:
            success = surgeon.add_hierarchical_label(label)
            print(f"✅ Add {label.name} label: {success}")
            
        surgeon.save()
        print_stats(surgeon)
        print("Opening updated schematic...")
        open_file_with_default_app(schematic_path)
        wait_for_user("📋 Check that hierarchical labels (VCC, GND, SIGNAL_IN, SIGNAL_OUT) appear. Press Enter when ready...")
        
        # Step 7: Remove a component
        print("\n\nStep 7: Removing Component (R2)")
        print("-" * 32)
        
        success = surgeon.remove_component("R2")
        print(f"✅ Remove R2 result: {success}")
        
        if success:
            surgeon.save()
            print_stats(surgeon)
            print("Opening updated schematic...")
            open_file_with_default_app(schematic_path)
            wait_for_user("📋 Check that R2 has been removed (should only see R1, C1, U1). Press Enter when ready...")
        else:
            print("❌ Failed to remove R2")
            
        # Step 8: Remove a hierarchical label
        print("\n\nStep 8: Removing Hierarchical Label (SIGNAL_OUT)")
        print("-" * 48)
        
        success = surgeon.remove_hierarchical_label("SIGNAL_OUT")
        print(f"✅ Remove SIGNAL_OUT label: {success}")
        
        if success:
            surgeon.save()
            print_stats(surgeon)
            print("Opening updated schematic...")
            open_file_with_default_app(schematic_path)
            wait_for_user("📋 Check that SIGNAL_OUT label has been removed. Press Enter when ready...")
        else:
            print("❌ Failed to remove SIGNAL_OUT label")
            
        # Step 9: Try to remove non-existent component (should fail gracefully)
        print("\n\nStep 9: Testing Error Handling (Remove Non-Existent Component)")
        print("-" * 62)
        
        success = surgeon.remove_component("R99")  # Doesn't exist
        print(f"✅ Remove non-existent R99: {success} (should be False)")
        
        if not success:
            print("✅ Error handling works correctly - returned False for non-existent component")
        else:
            print("❌ Error handling issue - should return False for non-existent component")
        
        print_stats(surgeon)
        
        # Final summary
        print("\n\n🎉 Demo Complete!")
        print("=" * 50)
        print("Summary of what we demonstrated:")
        print("✅ Created empty KiCad schematic")
        print("✅ Added components with manual positioning")
        print("✅ Added components with auto-placement")
        print("✅ Added hierarchical labels")
        print("✅ Removed components surgically")
        print("✅ Removed hierarchical labels")
        print("✅ Error handling for non-existent components")
        print(f"\n📁 Demo files saved in: {demo_dir}")
        print(f"📄 Final schematic: {schematic_path}")
        
        wait_for_user("Press Enter to finish the demo...")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print(f"\n📁 Demo files are saved in: {demo_dir}")
        print("You can inspect the final schematic file or delete the demo directory when done.")

if __name__ == "__main__":
    main()