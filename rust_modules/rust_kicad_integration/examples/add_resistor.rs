//! Example of adding a resistor component to a KiCad schematic
//!
//! This example demonstrates how to add a single resistor component
//! matching the reference schematic format.

use rust_kicad_schematic_writer::{
    Component, Pin, Position, CircuitData, 
    RustSchematicWriter, SchematicConfig,
};
use std::fs;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Creating a schematic with a resistor component...\n");

    // Create a resistor component matching the reference schematic
    let resistor = Component {
        reference: "R1".to_string(),
        lib_id: "Device:R".to_string(),
        value: "10k".to_string(),
        position: Position { 
            x: 121.92,  // Same position as reference
            y: 73.66,
        },
        rotation: 0.0,  // 0 degrees (vertical orientation)
        pins: vec![
            Pin {
                number: "1".to_string(),
                name: "~".to_string(),
                x: 0.0,
                y: 3.81,   // Top pin for vertical resistor
                orientation: 270.0,  // Pointing up
            },
            Pin {
                number: "2".to_string(),
                name: "~".to_string(),
                x: 0.0,
                y: -3.81,  // Bottom pin for vertical resistor
                orientation: 90.0,   // Pointing down
            },
        ],
    };

    // Create circuit data with the resistor
    let circuit = CircuitData {
        name: "resistor_example".to_string(),
        components: vec![resistor],
        nets: vec![], // No nets connected yet
        subcircuits: vec![],
    };

    // Configure schematic generation
    let config = SchematicConfig {
        paper_size: "A4".to_string(),
        title: "Resistor Example".to_string(),
        ..Default::default()
    };

    // Create the schematic writer
    let writer = RustSchematicWriter::new(circuit, config);
    
    // Generate the S-expression
    let schematic_content = writer.generate_schematic_sexp()?;
    
    // Write to file
    let output_file = "resistor_example.kicad_sch";
    fs::write(output_file, &schematic_content)?;
    
    println!("✅ Schematic created: {}", output_file);
    println!("   Component: R1 (10k resistor)");
    println!("   Position: (121.92, 73.66)");
    println!("   Footprint: Device:R");
    println!("\nYou can open this file in KiCad to verify the resistor placement.");
    
    Ok(())
}