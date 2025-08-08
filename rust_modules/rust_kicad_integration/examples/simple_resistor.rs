//! Simple example using the schematic_api to add a resistor
//!
//! This demonstrates the simplest way to add a component to a schematic.

use rust_kicad_schematic_writer::schematic_api::{
    create_schematic_with_components, SimpleComponent
};
use std::fs;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Creating a schematic with a simple resistor...\n");

    // Create a simple resistor component
    let resistor = SimpleComponent {
        reference: "R1".to_string(),
        lib_id: "Device:R".to_string(),
        value: "10k".to_string(),
        x: 121.92,
        y: 73.66,
        rotation: 0.0,
    };

    // Generate the schematic with the resistor
    let schematic = create_schematic_with_components("A4", vec![resistor]);
    
    // Save to file
    let output_file = "simple_resistor.kicad_sch";
    fs::write(output_file, schematic)?;
    
    println!("✅ Created schematic: {}", output_file);
    println!("   Contains: R1 (10k resistor) at position (121.92, 73.66)");
    println!("\nOpen in KiCad to verify the component placement matches the reference.");
    
    Ok(())
}