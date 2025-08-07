//! Example of creating a circuit with components and nets
//!
//! This demonstrates the full API for building complex circuits.

use rust_kicad_schematic_writer::{
    CircuitData, Component, Net, PinConnection, Pin, Position,
    RustSchematicWriter, SchematicConfig,
};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Creating a circuit with components and nets...\n");

    // Create a simple voltage divider circuit
    let circuit = create_voltage_divider_circuit();
    
    // Configure schematic generation
    let config = SchematicConfig {
        paper_size: "A4".to_string(),
        title: "Voltage Divider Example".to_string(),
        company: "Example Corp".to_string(),
        ..Default::default()
    };

    // Create the schematic writer
    let mut writer = RustSchematicWriter::new(circuit, config);
    
    // Generate hierarchical labels for nets
    let labels = writer.generate_hierarchical_labels()?;
    println!("Generated {} hierarchical labels:", labels.len());
    for label in &labels {
        println!("  - {} at ({:.2}, {:.2})", label.name, label.position.x, label.position.y);
    }

    // Write to file
    writer.write_to_file("examples/output/voltage_divider.kicad_sch")?;
    
    println!("\n✅ Circuit schematic created: examples/output/voltage_divider.kicad_sch");
    
    Ok(())
}

fn create_voltage_divider_circuit() -> CircuitData {
    CircuitData {
        name: "voltage_divider".to_string(),
        components: vec![
            Component {
                reference: "R1".to_string(),
                lib_id: "Device:R".to_string(),
                value: "10k".to_string(),
                position: Position { x: 100.0, y: 50.0 },
                rotation: 90.0,
                pins: vec![
                    Pin {
                        number: "1".to_string(),
                        name: "~".to_string(),
                        x: 0.0,
                        y: -3.81,
                        orientation: 90.0,
                    },
                    Pin {
                        number: "2".to_string(),
                        name: "~".to_string(),
                        x: 0.0,
                        y: 3.81,
                        orientation: 270.0,
                    },
                ],
            },
            Component {
                reference: "R2".to_string(),
                lib_id: "Device:R".to_string(),
                value: "10k".to_string(),
                position: Position { x: 100.0, y: 100.0 },
                rotation: 90.0,
                pins: vec![
                    Pin {
                        number: "1".to_string(),
                        name: "~".to_string(),
                        x: 0.0,
                        y: -3.81,
                        orientation: 90.0,
                    },
                    Pin {
                        number: "2".to_string(),
                        name: "~".to_string(),
                        x: 0.0,
                        y: 3.81,
                        orientation: 270.0,
                    },
                ],
            },
        ],
        nets: vec![
            Net {
                name: "VIN".to_string(),
                connected_pins: vec![
                    PinConnection {
                        component_ref: "R1".to_string(),
                        pin_id: "1".to_string(),
                    },
                ],
            },
            Net {
                name: "VOUT".to_string(),
                connected_pins: vec![
                    PinConnection {
                        component_ref: "R1".to_string(),
                        pin_id: "2".to_string(),
                    },
                    PinConnection {
                        component_ref: "R2".to_string(),
                        pin_id: "1".to_string(),
                    },
                ],
            },
            Net {
                name: "GND".to_string(),
                connected_pins: vec![
                    PinConnection {
                        component_ref: "R2".to_string(),
                        pin_id: "2".to_string(),
                    },
                ],
            },
        ],
        subcircuits: Vec::new(),
    }
}