//! Example of creating a hierarchical circuit design
//!
//! This demonstrates how to create complex circuits with subcircuits.

use rust_kicad_schematic_writer::{
    CircuitData, Component, Net, PinConnection, Pin, Position,
    RustSchematicWriter, SchematicConfig,
};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Creating a hierarchical circuit design...\n");

    // Create main circuit with subcircuits
    let main_circuit = create_hierarchical_circuit();
    
    // Configure schematic generation
    let config = SchematicConfig {
        paper_size: "A3".to_string(),
        title: "Hierarchical Design Example".to_string(),
        ..Default::default()
    };

    // Create the schematic writer
    let mut writer = RustSchematicWriter::new(main_circuit.clone(), config);
    
    // Generate hierarchical labels
    let labels = writer.generate_hierarchical_labels()?;
    
    // Display hierarchy information
    println!("Circuit hierarchy:");
    print_circuit_hierarchy(&main_circuit, 0);
    
    println!("\nGenerated {} hierarchical labels", labels.len());
    
    // Write to file
    writer.write_to_file("examples/output/hierarchical_design.kicad_sch")?;
    
    println!("\n✅ Hierarchical schematic created: examples/output/hierarchical_design.kicad_sch");
    
    Ok(())
}

fn print_circuit_hierarchy(circuit: &CircuitData, indent: usize) {
    let prefix = "  ".repeat(indent);
    println!("{}📁 {} ({} components, {} nets)", 
             prefix, circuit.name, circuit.components.len(), circuit.nets.len());
    
    for subcircuit in &circuit.subcircuits {
        print_circuit_hierarchy(subcircuit, indent + 1);
    }
}

fn create_hierarchical_circuit() -> CircuitData {
    CircuitData {
        name: "main_board".to_string(),
        components: vec![
            create_connector("J1", Position { x: 50.0, y: 100.0 }),
        ],
        nets: vec![
            Net {
                name: "POWER".to_string(),
                connected_pins: vec![
                    PinConnection {
                        component_ref: "J1".to_string(),
                        pin_id: "1".to_string(),
                    },
                ],
            },
        ],
        subcircuits: vec![
            create_power_supply_subcircuit(),
            create_mcu_subcircuit(),
        ],
    }
}

fn create_power_supply_subcircuit() -> CircuitData {
    CircuitData {
        name: "power_supply".to_string(),
        components: vec![
            Component {
                reference: "U1".to_string(),
                lib_id: "Regulator_Linear:LM7805_TO220".to_string(),
                value: "LM7805".to_string(),
                position: Position { x: 100.0, y: 100.0 },
                rotation: 0.0,
                pins: vec![
                    Pin {
                        number: "1".to_string(),
                        name: "VI".to_string(),
                        x: -3.81, y: 0.0,
                        orientation: 180.0,
                    },
                    Pin {
                        number: "2".to_string(),
                        name: "GND".to_string(),
                        x: 0.0, y: -3.81,
                        orientation: 90.0,
                    },
                    Pin {
                        number: "3".to_string(),
                        name: "VO".to_string(),
                        x: 3.81, y: 0.0,
                        orientation: 0.0,
                    },
                ],
            },
        ],
        nets: vec![
            Net {
                name: "VIN".to_string(),
                connected_pins: vec![
                    PinConnection {
                        component_ref: "U1".to_string(),
                        pin_id: "1".to_string(),
                    },
                ],
            },
            Net {
                name: "5V".to_string(),
                connected_pins: vec![
                    PinConnection {
                        component_ref: "U1".to_string(),
                        pin_id: "3".to_string(),
                    },
                ],
            },
        ],
        subcircuits: Vec::new(),
    }
}

fn create_mcu_subcircuit() -> CircuitData {
    CircuitData {
        name: "microcontroller".to_string(),
        components: vec![
            Component {
                reference: "U2".to_string(),
                lib_id: "MCU_Microchip_ATmega:ATmega328P-PU".to_string(),
                value: "ATmega328P".to_string(),
                position: Position { x: 150.0, y: 100.0 },
                rotation: 0.0,
                pins: vec![
                    Pin {
                        number: "7".to_string(),
                        name: "VCC".to_string(),
                        x: -12.7, y: 10.16,
                        orientation: 180.0,
                    },
                    Pin {
                        number: "8".to_string(),
                        name: "GND".to_string(),
                        x: -12.7, y: -10.16,
                        orientation: 180.0,
                    },
                ],
            },
        ],
        nets: vec![
            Net {
                name: "VCC".to_string(),
                connected_pins: vec![
                    PinConnection {
                        component_ref: "U2".to_string(),
                        pin_id: "7".to_string(),
                    },
                ],
            },
        ],
        subcircuits: Vec::new(),
    }
}

fn create_connector(reference: &str, position: Position) -> Component {
    Component {
        reference: reference.to_string(),
        lib_id: "Connector:Conn_01x02_Pin".to_string(),
        value: "Power".to_string(),
        position,
        rotation: 0.0,
        pins: vec![
            Pin {
                number: "1".to_string(),
                name: "Pin_1".to_string(),
                x: 0.0, y: 0.0,
                orientation: 180.0,
            },
            Pin {
                number: "2".to_string(),
                name: "Pin_2".to_string(),
                x: 0.0, y: -2.54,
                orientation: 180.0,
            },
        ],
    }
}