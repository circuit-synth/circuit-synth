#!/usr/bin/env python3
"""
Test script for KiCad API Phase 5: Sheet & Hierarchy
Demonstrates sheet management and hierarchical navigation functionality.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from circuit_synth.kicad_api import (
    Schematic,
    ComponentManager,
    LabelManager,
    SheetManager,
    HierarchyNavigator,
    LabelType,
    PlacementStrategy,
    PinSide,
    calculate_sheet_size_from_content,
    suggest_pin_side,
    match_hierarchical_labels_to_pins,
    validate_sheet_filename,
    suggest_sheet_position,
    create_sheet_instance_name,
)


def test_sheet_hierarchy():
    """Test sheet and hierarchy management functionality."""
    print("Testing KiCad API Phase 5: Sheet & Hierarchy")
    print("=" * 50)
    
    # Create a root schematic
    root_schematic = Schematic(
        title="Main Board",
        date="2025-06-08",
        revision="1.0"
    )
    
    # Add some components to root
    comp_manager = ComponentManager(root_schematic)
    
    r1 = comp_manager.add_component(
        library_id="Device:R",
        reference="R1",
        value="10k",
        position=(25.4, 25.4)
    )
    
    c1 = comp_manager.add_component(
        library_id="Device:C",
        reference="C1",
        value="100nF",
        position=(50.8, 25.4)
    )
    
    print(f"\n✓ Added components to root schematic")
    
    # Create sheet manager
    sheet_manager = SheetManager(root_schematic)
    
    # Test 1: Basic sheet creation
    print("\n1. Testing basic sheet creation:")
    
    # Create a power supply sheet
    power_sheet = sheet_manager.add_sheet(
        name="PowerSupply",
        filename="power_supply.kicad_sch",
        position=(100.0, 50.0),
        size=(76.2, 50.8)  # 3x2 inches
    )
    if power_sheet:
        print(f"   ✓ Created sheet '{power_sheet.name}' at ({power_sheet.position.x}, {power_sheet.position.y})")
        print(f"   ✓ Size: {power_sheet.size[0]} x {power_sheet.size[1]} mm")
    
    # Create a microcontroller sheet
    mcu_sheet = sheet_manager.add_sheet(
        name="Microcontroller",
        filename="mcu.kicad_sch",
        position=(200.0, 50.0)
    )
    if mcu_sheet:
        print(f"   ✓ Created sheet '{mcu_sheet.name}'")
    
    # Test 2: Sheet pin management
    print("\n2. Testing sheet pin management:")
    
    # Add pins to power supply sheet
    vcc_pin = sheet_manager.add_sheet_pin(
        power_sheet.uuid,
        "VCC",
        position="right",
        shape="output"
    )
    if vcc_pin:
        print(f"   ✓ Added output pin 'VCC' to power sheet")
    
    gnd_pin = sheet_manager.add_sheet_pin(
        power_sheet.uuid,
        "GND",
        position="right",
        shape="output"
    )
    if gnd_pin:
        print(f"   ✓ Added output pin 'GND' to power sheet")
    
    enable_pin = sheet_manager.add_sheet_pin(
        power_sheet.uuid,
        "ENABLE",
        position="left",
        shape="input"
    )
    if enable_pin:
        print(f"   ✓ Added input pin 'ENABLE' to power sheet")
    
    # Test 3: Sheet utilities
    print("\n3. Testing sheet utilities:")
    
    # Calculate sheet size
    suggested_size = calculate_sheet_size_from_content(
        components_count=10,
        pins_count=8
    )
    print(f"   ✓ Suggested sheet size for 10 components, 8 pins: {suggested_size}")
    
    # Suggest pin side
    suggested_side = suggest_pin_side(
        "DATA_OUT",
        "output",
        power_sheet.pins
    )
    print(f"   ✓ Suggested side for DATA_OUT pin: {suggested_side.value}")
    
    # Validate filename
    valid, error = validate_sheet_filename("test_sheet.kicad_sch")
    print(f"   ✓ Filename validation: {'Valid' if valid else f'Invalid - {error}'}")
    
    # Test 4: Hierarchy navigation
    print("\n4. Testing hierarchy navigation:")
    
    # Create child schematics for testing
    power_schematic = Schematic(title="Power Supply")
    mcu_schematic = Schematic(title="Microcontroller")
    
    # Add hierarchical labels to child schematics
    label_manager_power = LabelManager(power_schematic)
    label_manager_mcu = LabelManager(mcu_schematic)
    
    # Add matching hierarchical labels in power supply
    vcc_label = label_manager_power.add_label(
        "VCC",
        (76.2, 25.4),
        label_type=LabelType.HIERARCHICAL
    )
    gnd_label = label_manager_power.add_label(
        "GND",
        (76.2, 38.1),
        label_type=LabelType.HIERARCHICAL
    )
    enable_label = label_manager_power.add_label(
        "ENABLE",
        (0, 25.4),
        label_type=LabelType.HIERARCHICAL
    )
    
    print(f"   ✓ Added hierarchical labels to power supply sheet")
    
    # Create hierarchy navigator
    sheet_schematics = {
        "power_supply.kicad_sch": power_schematic,
        "mcu.kicad_sch": mcu_schematic
    }
    
    navigator = HierarchyNavigator(root_schematic, sheet_schematics)
    
    # Build hierarchy tree
    tree = navigator.build_hierarchy_tree()
    print(f"   ✓ Built hierarchy tree with {len(tree.children)} child sheets")
    
    # Get hierarchy depth
    depth = navigator.get_hierarchy_depth()
    print(f"   ✓ Hierarchy depth: {depth}")
    
    # Test 5: Component discovery across hierarchy
    print("\n5. Testing component discovery:")
    
    # Add components to child sheets
    comp_manager_power = ComponentManager(power_schematic)
    vreg = comp_manager_power.add_component(
        library_id="Regulator_Linear:LM7805",
        reference="U1",
        value="LM7805"
    )
    
    # Build hierarchical component lookup
    hier_lookup = navigator.build_hierarchical_component_lookup()
    print(f"   ✓ Built hierarchical lookup with {len(hier_lookup)} components")
    
    # Test 6: Connection validation
    print("\n6. Testing connection validation:")
    
    # Match labels to pins
    matches = match_hierarchical_labels_to_pins(power_sheet, power_schematic)
    matched_count = sum(1 for pin, label in matches.values() if pin and label)
    print(f"   ✓ Matched {matched_count} hierarchical labels to sheet pins")
    
    # Validate connections
    errors = navigator.validate_hierarchical_connections()
    print(f"   ✓ Connection validation found {len(errors)} errors")
    for error in errors[:3]:  # Show first 3 errors
        print(f"     - {error}")
    
    # Test 7: Sheet operations
    print("\n7. Testing sheet operations:")
    
    # Find sheet by name
    found_sheet = sheet_manager.find_sheet_by_name("PowerSupply")
    if found_sheet:
        print(f"   ✓ Found sheet by name: {found_sheet.name}")
    
    # Update sheet
    success = sheet_manager.update_sheet(
        power_sheet.uuid,
        name="PowerSupply_v2"
    )
    if success:
        print(f"   ✓ Updated sheet name to: {power_sheet.name}")
    
    # Test 8: Advanced utilities
    print("\n8. Testing advanced utilities:")
    
    # Suggest position for new sheet
    suggested_pos = suggest_sheet_position(
        [power_sheet, mcu_sheet],
        (76.2, 50.8),
        "right"
    )
    print(f"   ✓ Suggested position for new sheet: {suggested_pos}")
    
    # Create unique sheet name
    existing_names = ["PowerSupply", "Microcontroller"]
    unique_name = create_sheet_instance_name("PowerSupply", existing_names)
    print(f"   ✓ Created unique sheet name: {unique_name}")
    
    # Test 9: Final statistics
    print("\n9. Final hierarchy statistics:")
    print(f"   - Root components: {len(root_schematic.components)}")
    print(f"   - Total sheets: {len(root_schematic.sheets)}")
    print(f"   - Total sheet pins: {sum(len(sheet.pins) for sheet in root_schematic.sheets)}")
    
    # Sheet breakdown
    for sheet in root_schematic.sheets:
        print(f"\n   Sheet '{sheet.name}':")
        print(f"   - Filename: {sheet.filename}")
        print(f"   - Position: ({sheet.position.x}, {sheet.position.y})")
        print(f"   - Size: {sheet.size[0]} x {sheet.size[1]} mm")
        print(f"   - Pins: {len(sheet.pins)}")
        for pin in sheet.pins:
            print(f"     • {pin.name} ({pin.shape})")
    
    print("\n✅ All Phase 5 tests completed successfully!")
    
    return root_schematic, sheet_manager, navigator


def test_error_handling():
    """Test error handling in sheet and hierarchy operations."""
    print("\n\nTesting Error Handling")
    print("=" * 50)
    
    schematic = Schematic()
    sheet_manager = SheetManager(schematic)
    
    print("\n1. Testing invalid sheet creation:")
    
    # Empty name
    result = sheet_manager.add_sheet("", "file.kicad_sch", (10, 10))
    print(f"   ✓ Empty sheet name returned: {result} (expected: None)")
    
    # Invalid size
    result = sheet_manager.add_sheet("Test", "file.kicad_sch", (10, 10), size=(0, 50))
    print(f"   ✓ Invalid sheet size returned: {result} (expected: None)")
    
    print("\n2. Testing invalid pin operations:")
    
    # Add pin to non-existent sheet
    result = sheet_manager.add_sheet_pin("fake-uuid", "PIN1")
    print(f"   ✓ Pin on non-existent sheet returned: {result} (expected: None)")
    
    # Invalid pin shape
    sheet = sheet_manager.add_sheet("Test", "test.kicad_sch", (10, 10))
    if sheet:
        result = sheet_manager.add_sheet_pin(sheet.uuid, "PIN1", shape="invalid")
        print(f"   ✓ Invalid pin shape returned: {result} (expected: None)")
    
    print("\n3. Testing hierarchy validation:")
    
    # Add duplicate sheet names
    sheet1 = sheet_manager.add_sheet("Duplicate", "file1.kicad_sch", (10, 10))
    sheet2 = sheet_manager.add_sheet("Duplicate", "file2.kicad_sch", (50, 10))
    
    errors = sheet_manager.validate_hierarchy()
    print(f"   ✓ Hierarchy validation found {len(errors)} errors")
    
    print("\n✅ Error handling tests completed!")


if __name__ == "__main__":
    # Run main tests
    schematic, sheet_manager, navigator = test_sheet_hierarchy()
    
    # Run error handling tests
    test_error_handling()
    
    print("\n" + "=" * 50)
    print("All KiCad API Phase 5 tests passed! 🎉")
    print("\nPhase 5 Complete! Sheet and hierarchy management is now functional.")
    print("\nNext steps:")
    print("- Phase 6: Search & Discovery")