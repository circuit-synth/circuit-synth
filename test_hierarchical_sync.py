#!/usr/bin/env python3
"""
Comprehensive test suite for hierarchical synchronization.
Tests various preservation scenarios.
"""

import os
import json
from pathlib import Path
from circuit_synth import Circuit, Component, Net, circuit
from circuit_synth.kicad_api.schematic import SchematicParser

class HierarchicalSyncTester:
    """Test harness for hierarchical synchronization"""
    
    def __init__(self, project_name):
        self.project_name = project_name
        self.project_path = Path(project_name)
        self.changes_made = {}
    
    def track_component_positions(self):
        """Read and track all component positions before update"""
        positions = {}
        
        # Find all .kicad_sch files
        for sch_file in self.project_path.glob("*.kicad_sch"):
            parser = SchematicParser(str(sch_file))
            schematic = parser.parse()
            
            sheet_positions = {}
            for elem in schematic.elements:
                if hasattr(elem, 'lib_id') and hasattr(elem, 'property'):
                    ref = None
                    for prop in elem.property:
                        if prop.name == "Reference":
                            ref = prop.value
                            break
                    
                    if ref and hasattr(elem, 'at'):
                        sheet_positions[ref] = {
                            'x': elem.at.x,
                            'y': elem.at.y,
                            'angle': elem.at.angle if hasattr(elem.at, 'angle') else 0
                        }
            
            positions[sch_file.name] = sheet_positions
        
        return positions
    
    def compare_positions(self, before, after):
        """Compare positions and report preservation status"""
        print("\n📊 POSITION PRESERVATION REPORT:")
        print("=" * 50)
        
        all_preserved = True
        
        for sheet_name, before_positions in before.items():
            print(f"\n📄 Sheet: {sheet_name}")
            after_positions = after.get(sheet_name, {})
            
            for ref, before_pos in before_positions.items():
                after_pos = after_positions.get(ref)
                
                if not after_pos:
                    print(f"  ❌ {ref}: Component missing after update!")
                    all_preserved = False
                elif (before_pos['x'] != after_pos['x'] or 
                      before_pos['y'] != after_pos['y']):
                    print(f"  ❌ {ref}: Position changed!")
                    print(f"     Before: ({before_pos['x']}, {before_pos['y']})")
                    print(f"     After:  ({after_pos['x']}, {after_pos['y']})")
                    all_preserved = False
                else:
                    print(f"  ✅ {ref}: Position preserved at ({before_pos['x']}, {before_pos['y']})")
        
        return all_preserved
    
    def run_test(self, circuit_func):
        """Run a complete preservation test cycle"""
        project_exists = self.project_path.exists()
        
        if not project_exists:
            print(f"🚀 Generating initial project: {self.project_name}")
            circuit_instance = circuit_func()
            circuit_instance.generate_kicad_project(self.project_name, force_regenerate=True)
            print("✅ Initial generation complete")
            print("\n📝 TO TEST PRESERVATION:")
            print("1. Open the project in KiCad")
            print("2. Move some components around")
            print("3. Save and close KiCad")
            print("4. Run this script again")
            return False
        else:
            print(f"🔄 Testing preservation for: {self.project_name}")
            
            # Track positions before update
            before_positions = self.track_component_positions()
            
            # Regenerate with preservation
            circuit_instance = circuit_func()
            circuit_instance.generate_kicad_project(self.project_name, force_regenerate=False)
            
            # Track positions after update
            after_positions = self.track_component_positions()
            
            # Compare and report
            preserved = self.compare_positions(before_positions, after_positions)
            
            if preserved:
                print("\n✅ ALL POSITIONS PRESERVED!")
            else:
                print("\n⚠️  SOME POSITIONS WERE NOT PRESERVED!")
            
            return preserved

# Test circuits
@circuit(name="flat_test")
def flat_test():
    """Single-level circuit for baseline testing"""
    R1 = Component("Device:R", ref="R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    R2 = Component("Device:R", ref="R", value="1k", footprint="Resistor_SMD:R_0603_1608Metric")
    C1 = Component("Device:C", ref="C", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")
    
    VCC = Net("VCC")
    GND = Net("GND")
    
    R1[1] += VCC
    R1[2] += R2[1]
    R2[2] += GND
    C1[1] += R2[1]
    C1[2] += GND

@circuit(name="sub_circuit")
def sub_circuit(vcc, gnd):
    """Subcircuit for hierarchical testing"""
    R1 = Component("Device:R", ref="R", value="4.7k", footprint="Resistor_SMD:R_0603_1608Metric")
    R2 = Component("Device:R", ref="R", value="2.2k", footprint="Resistor_SMD:R_0603_1608Metric")
    
    R1[1] += vcc
    R1[2] += R2[1]
    R2[2] += gnd

@circuit(name="hierarchical_test")
def hierarchical_test():
    """Two-level hierarchical circuit"""
    # Main components
    C1 = Component("Device:C", ref="C", value="10uF", footprint="Capacitor_SMD:C_0805_2012Metric")
    
    # Nets
    VCC = Net("VCC")
    GND = Net("GND")
    
    # Connect main capacitor
    C1[1] += VCC
    C1[2] += GND
    
    # Add subcircuits
    sub1 = sub_circuit(VCC, GND)
    sub2 = sub_circuit(VCC, GND)

def main():
    """Run all tests"""
    print("🧪 HIERARCHICAL SYNCHRONIZATION TEST SUITE")
    print("=" * 60)
    
    # Test 1: Flat circuit
    print("\n📋 Test 1: Flat Circuit Preservation")
    tester1 = HierarchicalSyncTester("flat_preservation_test")
    tester1.run_test(flat_test)
    
    # Test 2: Hierarchical circuit
    print("\n📋 Test 2: Hierarchical Circuit Preservation")
    tester2 = HierarchicalSyncTester("hierarchical_preservation_test")
    tester2.run_test(hierarchical_test)
    
    print("\n✅ Test suite complete!")

if __name__ == "__main__":
    main()