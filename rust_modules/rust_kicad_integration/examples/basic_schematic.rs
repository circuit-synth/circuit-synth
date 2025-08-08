//! Basic example of creating a KiCad schematic file
//!
//! This example demonstrates how to create a simple schematic with a few components.

use rust_kicad_schematic_writer::schematic_api::{create_minimal_schematic, create_empty_schematic};
use std::fs;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Creating basic KiCad schematic examples...\n");

    // Example 1: Create a minimal A4 schematic
    let minimal_schematic = create_minimal_schematic();
    fs::write("examples/output/minimal.kicad_sch", &minimal_schematic)?;
    println!("✅ Created minimal A4 schematic: examples/output/minimal.kicad_sch");
    println!("   Size: {} bytes", minimal_schematic.len());

    // Example 2: Create schematics with different paper sizes
    let paper_sizes = vec!["A4", "A3", "A2", "Letter", "Legal"];
    
    for size in paper_sizes {
        let schematic = create_empty_schematic(size);
        let filename = format!("examples/output/schematic_{}.kicad_sch", size.to_lowercase());
        fs::write(&filename, &schematic)?;
        println!("✅ Created {} schematic: {}", size, filename);
    }

    println!("\n🎉 All schematics created successfully!");
    println!("You can open these files in KiCad to verify they work correctly.");

    Ok(())
}