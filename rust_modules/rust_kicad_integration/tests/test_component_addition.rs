//! Tests for adding components to schematics
//!
//! These tests verify that components can be properly added to KiCad schematics.

use rust_kicad_schematic_writer::schematic_api::{
    create_schematic_with_components, SimpleComponent
};

#[test]
fn test_add_single_resistor() {
    // Create a resistor matching the reference schematic
    let resistor = SimpleComponent {
        reference: "R1".to_string(),
        lib_id: "Device:R".to_string(),
        value: "10k".to_string(),
        x: 121.92,
        y: 73.66,
        rotation: 0.0,
    };

    // Generate schematic
    let schematic = create_schematic_with_components("A4", vec![resistor]);
    
    // Verify the schematic contains expected elements
    assert!(schematic.contains("(kicad_sch"));
    assert!(schematic.contains("(version 20250114)"));
    assert!(schematic.contains("(paper \"A4\")"));
    assert!(schematic.contains("(lib_id \"Device:R\")"));
    assert!(schematic.contains("(at 121.92 73.66 0.0)"));
    assert!(schematic.contains("\"R1\""));
    assert!(schematic.contains("\"10k\""));
    assert!(schematic.contains("(pin \"1\""));
    assert!(schematic.contains("(pin \"2\""));
}

#[test]
fn test_add_multiple_components() {
    // Create multiple components
    let components = vec![
        SimpleComponent {
            reference: "R1".to_string(),
            lib_id: "Device:R".to_string(),
            value: "10k".to_string(),
            x: 50.0,
            y: 50.0,
            rotation: 0.0,
        },
        SimpleComponent {
            reference: "R2".to_string(),
            lib_id: "Device:R".to_string(),
            value: "22k".to_string(),
            x: 100.0,
            y: 50.0,
            rotation: 90.0,
        },
        SimpleComponent {
            reference: "C1".to_string(),
            lib_id: "Device:C".to_string(),
            value: "100nF".to_string(),
            x: 75.0,
            y: 100.0,
            rotation: 0.0,
        },
    ];

    // Generate schematic
    let schematic = create_schematic_with_components("A3", vec![components[0].clone(), components[1].clone(), components[2].clone()]);
    
    // Verify all components are present
    assert!(schematic.contains("\"R1\""));
    assert!(schematic.contains("\"10k\""));
    assert!(schematic.contains("(at 50.0 50.0 0.0)"));
    
    assert!(schematic.contains("\"R2\""));
    assert!(schematic.contains("\"22k\""));
    assert!(schematic.contains("(at 100.0 50.0 90.0)"));
    
    assert!(schematic.contains("\"C1\""));
    assert!(schematic.contains("\"100nF\""));
    assert!(schematic.contains("(at 75.0 100.0 0.0)"));
    
    // Verify paper size
    assert!(schematic.contains("(paper \"A3\")"));
}

#[test]
fn test_component_with_rotation() {
    // Create a rotated component
    let resistor = SimpleComponent {
        reference: "R1".to_string(),
        lib_id: "Device:R".to_string(),
        value: "1k".to_string(),
        x: 100.0,
        y: 100.0,
        rotation: 270.0, // Rotated 270 degrees
    };

    let schematic = create_schematic_with_components("A4", vec![resistor]);
    
    // Verify rotation is included
    assert!(schematic.contains("(at 100.0 100.0 270.0)"));
}

#[test]
fn test_component_properties_positioning() {
    // Create a component and verify property positioning
    let component = SimpleComponent {
        reference: "U1".to_string(),
        lib_id: "MCU_ST:STM32F103".to_string(),
        value: "STM32F103C8T6".to_string(),
        x: 50.0,
        y: 50.0,
        rotation: 0.0,
    };

    let schematic = create_schematic_with_components("A4", vec![component]);
    
    // Reference should be offset to the right and slightly up
    assert!(schematic.contains("\"Reference\" \"U1\" (at 52.54")); // x + 2.54
    assert!(schematic.contains("48.73")); // y - 1.27
    
    // Value should be offset to the right and slightly down
    assert!(schematic.contains("\"Value\" \"STM32F103C8T6\" (at 52.54")); // x + 2.54
    assert!(schematic.contains("51.27")); // y + 1.27
}