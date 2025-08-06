//! Integration tests for rust_kicad_schematic_writer
//!
//! These tests verify end-to-end functionality of the library.

use rust_kicad_schematic_writer::{
    schematic_api::*, 
    CircuitData, Component, Net, PinConnection, Pin, Position,
    RustSchematicWriter, SchematicConfig, HierarchicalLabel,
};
use std::fs;
use tempfile::TempDir;

#[test]
fn test_minimal_schematic_creation() {
    let schematic = create_minimal_schematic();
    
    // Verify it's a valid S-expression
    assert!(schematic.starts_with("(kicad_sch"));
    assert!(schematic.contains("(paper \"A4\")"));
    assert!(schematic.contains("(generator \"circuit_synth\")"));
}

#[test]
fn test_various_paper_sizes() {
    let sizes = vec!["A4", "A3", "A2", "A1", "A0", "Letter", "Legal"];
    
    for size in sizes {
        let schematic = create_empty_schematic(size);
        assert!(schematic.contains(&format!("(paper \"{}\")", size)));
    }
}

#[test]
fn test_file_writing() -> Result<(), Box<dyn std::error::Error>> {
    let temp_dir = TempDir::new()?;
    let file_path = temp_dir.path().join("test.kicad_sch");
    
    // Create a simple circuit
    let circuit = create_test_circuit();
    let config = SchematicConfig::default();
    
    let writer = RustSchematicWriter::new(circuit, config);
    writer.write_to_file(file_path.to_str().unwrap())?;
    
    // Verify file was created and contains expected content
    let content = fs::read_to_string(&file_path)?;
    assert!(content.starts_with("(kicad_sch"));
    assert!(content.contains("(symbol"));
    
    Ok(())
}

#[test]
fn test_hierarchical_label_generation() -> Result<(), Box<dyn std::error::Error>> {
    let circuit = create_test_circuit();
    let config = SchematicConfig::default();
    
    let mut writer = RustSchematicWriter::new(circuit, config);
    let labels = writer.generate_hierarchical_labels()?;
    
    // Should generate labels for each net with connections
    assert!(!labels.is_empty());
    
    // Verify label properties
    for label in labels {
        assert!(!label.name.is_empty());
        assert!(!label.uuid.is_empty());
        // Labels should be grid-aligned (KiCad uses 1.27mm grid)
        let x_aligned = (label.position.x % 1.27).abs() < 0.01;
        let y_aligned = (label.position.y % 1.27).abs() < 0.01;
        assert!(x_aligned || y_aligned);
    }
    
    Ok(())
}

#[test]
fn test_hierarchical_circuit() -> Result<(), Box<dyn std::error::Error>> {
    let main_circuit = CircuitData {
        name: "main".to_string(),
        components: vec![create_test_component("U1")],
        nets: vec![create_test_net("VCC")],
        subcircuits: vec![
            CircuitData {
                name: "subcircuit1".to_string(),
                components: vec![create_test_component("R1")],
                nets: vec![create_test_net("NET1")],
                subcircuits: Vec::new(),
            },
            CircuitData {
                name: "subcircuit2".to_string(),
                components: vec![create_test_component("C1")],
                nets: vec![create_test_net("NET2")],
                subcircuits: Vec::new(),
            },
        ],
    };
    
    let config = SchematicConfig::default();
    let mut writer = RustSchematicWriter::new(main_circuit, config);
    
    // Generate labels for hierarchical design
    let labels = writer.generate_hierarchical_labels()?;
    
    // Should handle hierarchical structure
    assert!(!labels.is_empty());
    
    Ok(())
}

#[test]
fn test_schematic_sexp_generation() -> Result<(), Box<dyn std::error::Error>> {
    let circuit = create_test_circuit();
    let config = SchematicConfig {
        paper_size: "A3".to_string(),
        title: "Test Schematic".to_string(),
        company: "Test Company".to_string(),
        ..Default::default()
    };
    
    let writer = RustSchematicWriter::new(circuit, config);
    let sexp = writer.generate_schematic_sexp()?;
    
    // Verify S-expression structure
    assert!(sexp.starts_with("(kicad_sch"));
    assert!(sexp.contains("(version"));
    assert!(sexp.contains("(generator"));
    assert!(sexp.contains("(paper \"A3\")"));
    assert!(sexp.contains("(lib_symbols)"));
    assert!(sexp.contains("(symbol"));
    
    // Verify it's properly formatted (no dotted pairs)
    assert!(!sexp.contains(" . "));
    
    Ok(())
}

#[test]
fn test_complex_circuit_generation() -> Result<(), Box<dyn std::error::Error>> {
    // Create a more complex circuit with multiple components and nets
    let circuit = CircuitData {
        name: "complex_circuit".to_string(),
        components: vec![
            create_resistor("R1", Position { x: 50.0, y: 50.0 }),
            create_resistor("R2", Position { x: 100.0, y: 50.0 }),
            create_capacitor("C1", Position { x: 75.0, y: 100.0 }),
        ],
        nets: vec![
            Net {
                name: "VCC".to_string(),
                connected_pins: vec![
                    PinConnection { component_ref: "R1".to_string(), pin_id: "1".to_string() },
                    PinConnection { component_ref: "R2".to_string(), pin_id: "1".to_string() },
                ],
            },
            Net {
                name: "GND".to_string(),
                connected_pins: vec![
                    PinConnection { component_ref: "C1".to_string(), pin_id: "2".to_string() },
                ],
            },
            Net {
                name: "SIGNAL".to_string(),
                connected_pins: vec![
                    PinConnection { component_ref: "R1".to_string(), pin_id: "2".to_string() },
                    PinConnection { component_ref: "C1".to_string(), pin_id: "1".to_string() },
                ],
            },
        ],
        subcircuits: Vec::new(),
    };
    
    let config = SchematicConfig::default();
    let mut writer = RustSchematicWriter::new(circuit, config);
    
    let labels = writer.generate_hierarchical_labels()?;
    assert_eq!(labels.len(), 3); // One label per net
    
    let sexp = writer.generate_schematic_sexp()?;
    assert!(sexp.contains("R1"));
    assert!(sexp.contains("R2"));
    assert!(sexp.contains("C1"));
    
    Ok(())
}

// Helper functions for creating test data

fn create_test_circuit() -> CircuitData {
    CircuitData {
        name: "test_circuit".to_string(),
        components: vec![create_test_component("U1")],
        nets: vec![create_test_net("TEST_NET")],
        subcircuits: Vec::new(),
    }
}

fn create_test_component(reference: &str) -> Component {
    Component {
        reference: reference.to_string(),
        lib_id: "Device:R".to_string(),
        value: "1k".to_string(),
        position: Position { x: 100.0, y: 100.0 },
        rotation: 0.0,
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
    }
}

fn create_test_net(name: &str) -> Net {
    Net {
        name: name.to_string(),
        connected_pins: vec![
            PinConnection {
                component_ref: "U1".to_string(),
                pin_id: "1".to_string(),
            },
        ],
    }
}

fn create_resistor(reference: &str, position: Position) -> Component {
    Component {
        reference: reference.to_string(),
        lib_id: "Device:R".to_string(),
        value: "10k".to_string(),
        position,
        rotation: 0.0,
        pins: vec![
            Pin {
                number: "1".to_string(),
                name: "~".to_string(),
                x: -3.81,
                y: 0.0,
                orientation: 180.0,
            },
            Pin {
                number: "2".to_string(),
                name: "~".to_string(),
                x: 3.81,
                y: 0.0,
                orientation: 0.0,
            },
        ],
    }
}

fn create_capacitor(reference: &str, position: Position) -> Component {
    Component {
        reference: reference.to_string(),
        lib_id: "Device:C".to_string(),
        value: "100nF".to_string(),
        position,
        rotation: 0.0,
        pins: vec![
            Pin {
                number: "1".to_string(),
                name: "~".to_string(),
                x: 0.0,
                y: -1.27,
                orientation: 90.0,
            },
            Pin {
                number: "2".to_string(),
                name: "~".to_string(),
                x: 0.0,
                y: 1.27,
                orientation: 270.0,
            },
        ],
    }
}