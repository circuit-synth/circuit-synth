//! Rust KiCad Schematic Writer
//!
//! A high-performance Rust implementation for generating KiCad schematic files
//! with comprehensive hierarchical label generation.

use log::{info, debug};

pub mod types;
pub mod hierarchical_labels;
pub mod s_expression;

pub mod python_bindings;

pub use types::*;
pub use hierarchical_labels::*;
pub use s_expression::*;

pub use python_bindings::*;

/// Main schematic writer that handles the complete generation pipeline
#[derive(Debug, Clone)]
pub struct RustSchematicWriter {
    /// Circuit data containing components, nets, and connections
    pub circuit_data: CircuitData,
    /// Configuration for schematic generation
    pub config: SchematicConfig,
    /// Generated hierarchical labels
    pub hierarchical_labels: Vec<HierarchicalLabel>,
}

impl RustSchematicWriter {
    /// Create a new schematic writer instance
    pub fn new(circuit_data: CircuitData, config: SchematicConfig) -> Self {
        info!("🚀 Initializing Rust KiCad Schematic Writer");
        info!("📊 Circuit stats: {} components, {} nets", 
              circuit_data.components.len(), 
              circuit_data.nets.len());
        
        Self {
            circuit_data,
            config,
            hierarchical_labels: Vec::new(),
        }
    }

    /// Generate hierarchical labels for all nets in the circuit (with full hierarchical support)
    pub fn generate_hierarchical_labels(&mut self) -> Result<Vec<HierarchicalLabel>, SchematicError> {
        info!("🚀 Starting ENHANCED Rust hierarchical label generation");
        
        // Log circuit structure details
        let hierarchy_stats = self.circuit_data.get_hierarchy_stats();
        info!("🏗️  RUST: Circuit hierarchy analysis:");
        info!("    - Circuit name: '{}'", self.circuit_data.name);
        info!("    - Is hierarchical: {}", self.circuit_data.is_hierarchical());
        info!("    - Max depth: {} levels", hierarchy_stats.max_depth);
        info!("    - Total subcircuits: {}", hierarchy_stats.total_subcircuits);
        info!("    - Local components: {}", self.circuit_data.components.len());
        info!("    - Local nets: {}", self.circuit_data.nets.len());
        info!("    - Total components (all levels): {}", hierarchy_stats.total_components);
        info!("    - Total nets (all levels): {}", hierarchy_stats.total_nets);

        // Log subcircuit structure if hierarchical
        if self.circuit_data.is_hierarchical() {
            info!("🔍 RUST: Subcircuit structure:");
            for (i, subcircuit) in self.circuit_data.subcircuits.iter().enumerate() {
                info!("  Subcircuit #{}: '{}' with {} components, {} nets",
                      i + 1, subcircuit.name, subcircuit.components.len(), subcircuit.nets.len());
                
                // Log components in each subcircuit
                for (j, component) in subcircuit.components.iter().enumerate() {
                    info!("    Component #{}: {} ({}) with {} pins",
                          j + 1, component.reference, component.lib_id, component.pins.len());
                }
                
                // Log nets in each subcircuit
                for (j, net) in subcircuit.nets.iter().enumerate() {
                    info!("    Net #{}: '{}' with {} connections",
                          j + 1, net.name, net.connected_pins.len());
                }
            }
        }

        // Use the hierarchical label generator
        let mut generator = HierarchicalLabelGenerator::new(LabelGeneratorConfig::default());
        let labels = generator.generate_labels(&self.circuit_data)?;

        self.hierarchical_labels = labels.clone();
        
        info!("✨ RUST: Generated {} hierarchical labels successfully using enhanced hierarchical processing", labels.len());
        info!("🎉 RUST: Enhanced hierarchical label generation complete!");

        Ok(labels)
    }

    /// Calculate the position for a hierarchical label based on component and pin using rust_pin_calculator
    fn calculate_label_position(&self, component: &Component, pin_id: &str) -> Result<Position, SchematicError> {
        info!("🦀 FIXED LABEL POSITION CALCULATION for {}.{}", component.reference, pin_id);
        info!("  📍 Component position: ({:.2}, {:.2})", component.position.x, component.position.y);
        info!("  🔄 Component rotation: {:.1}°", component.rotation);
        
        // Get pin information from component library data
        let pin_data = component.pins.iter()
            .find(|p| p.number == pin_id || p.name == pin_id)
            .ok_or_else(|| SchematicError::PinNotFound(pin_id.to_string()))?;

        info!("  📌 Pin data from Python: number={}, name={:?}, world_position=({}, {}), orientation={}°",
               pin_data.number, pin_data.name, pin_data.x, pin_data.y, pin_data.orientation);

        // CRITICAL FIX: The pin data from Python already contains the world position!
        // The Python code calculated: component_position + pin_offset = world_position
        // So pin_data.x and pin_data.y are already the world coordinates, not local offsets!
        
        let pin_world_x = pin_data.x;
        let pin_world_y = pin_data.y;
        
        info!("  🌍 Using pin world position directly: ({:.2}, {:.2})", pin_world_x, pin_world_y);

        // Calculate label offset based on pin orientation
        // Use the pin orientation to position the label away from the pin
        let pin_angle_rad = pin_data.orientation.to_radians();
        let label_offset = 2.54; // 100mil (2.54mm) offset from pin
        
        // Calculate offset vector pointing away from the pin
        let offset_x = label_offset * pin_angle_rad.cos();
        let offset_y = label_offset * pin_angle_rad.sin();
        
        info!("  ➡️  Label offset calculation:");
        info!("    - Pin orientation: {:.1}°", pin_data.orientation);
        info!("    - Offset distance: {:.2}mm", label_offset);
        info!("    - Offset vector: ({:.2}, {:.2})", offset_x, offset_y);
        
        // Apply offset to get final label position
        let label_x = pin_world_x + offset_x;
        let label_y = pin_world_y + offset_y;
        
        info!("  🏷️  Label position before grid snap: ({:.2}, {:.2})", label_x, label_y);

        // Snap to grid for proper KiCad alignment
        let grid_size = 1.27; // KiCad 50mil grid
        let snapped_x = (label_x / grid_size).round() * grid_size;
        let snapped_y = (label_y / grid_size).round() * grid_size;

        info!("  📐 Grid snapping: ({:.2}, {:.2}) -> ({:.2}, {:.2})",
               label_x, label_y, snapped_x, snapped_y);

        let final_position = Position {
            x: snapped_x,
            y: snapped_y,
        };
        
        info!("  🎯 FINAL FIXED LABEL POSITION: ({:.2}, {:.2})", final_position.x, final_position.y);

        Ok(final_position)
    }

    /// Determine the orientation for a hierarchical label
    fn determine_label_orientation(&self, component: &Component, pin_id: &str) -> Result<f64, SchematicError> {
        let pin_data = component.pins.iter()
            .find(|p| p.number == pin_id || p.name == pin_id)
            .ok_or_else(|| SchematicError::PinNotFound(pin_id.to_string()))?;

        // Calculate label orientation based on pin orientation and component rotation
        let pin_angle = pin_data.orientation;
        let label_angle = (pin_angle + 180.0) % 360.0; // Opposite direction from pin
        let global_angle = (label_angle + component.rotation) % 360.0;

        debug!("🧮 Orientation calculation: pin={}°, label={}°, component_rotation={}°, global={}°", 
               pin_angle, label_angle, component.rotation, global_angle);

        Ok(global_angle)
    }

    /// Generate the complete KiCad schematic S-expression
    pub fn generate_schematic_sexp(&self) -> Result<String, SchematicError> {
        info!("🔄 Converting to KiCad S-expression format using lexpr");
        
        let result = generate_schematic_sexp(&self.circuit_data, &self.hierarchical_labels, &self.config)?;
        
        info!("✅ S-expression generation completed, {} characters", result.len());
        
        Ok(result)
    }

    /// Write the schematic to a file
    pub fn write_to_file(&self, path: &str) -> Result<(), SchematicError> {
        let content = self.generate_schematic_sexp()?;
        std::fs::write(path, content)
            .map_err(|e| SchematicError::IoError(format!("Failed to write file {}: {}", path, e)))?;
        
        info!("📁 Schematic written to: {}", path);
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hierarchical_label_generation() {
        // Create test circuit data
        let circuit_data = create_test_circuit_data();
        let config = SchematicConfig::default();
        
        let mut writer = RustSchematicWriter::new(circuit_data, config);
        let labels = writer.generate_hierarchical_labels().unwrap();
        
        // Should generate labels for each pin connection
        assert!(!labels.is_empty());
        
        // Each label should have a valid UUID
        for label in &labels {
            assert!(!label.uuid.is_empty());
            assert!(Uuid::parse_str(&label.uuid).is_ok());
        }
    }

    #[test]
    fn test_six_hierarchical_labels_like_reference_design() {
        // Create test circuit data similar to the reference design with 6 pins
        let circuit_data = create_reference_design_circuit_data();
        let config = SchematicConfig::default();
        
        let mut writer = RustSchematicWriter::new(circuit_data, config);
        let labels = writer.generate_hierarchical_labels().unwrap();
        
        // Verify we get exactly 6 labels as expected from the reference design
        assert_eq!(labels.len(), 6, "Should generate exactly 6 hierarchical labels like the reference design");
        
        // Verify label names match the expected pin names
        let label_names: Vec<&String> = labels.iter().map(|l| &l.name).collect();
        assert!(label_names.contains(&&"VBAT".to_string()));
        assert!(label_names.contains(&&"PC13".to_string()));
        assert!(label_names.contains(&&"PA0".to_string()));
        assert!(label_names.contains(&&"PA1".to_string()));
        assert!(label_names.contains(&&"PA2".to_string()));
        assert!(label_names.contains(&&"PA3".to_string()));
        
        println!("✅ Successfully generated {} hierarchical labels:", labels.len());
        for label in &labels {
            println!("  - {} at ({:.2}, {:.2}) orientation {:.0}°",
                     label.name, label.position.x, label.position.y, label.orientation);
            println!("    Grid alignment check: x % 1.27 = {:.6}, y % 1.27 = {:.6}",
                     label.position.x % 1.27, label.position.y % 1.27);
        }
        
        // Verify all labels have proper positioning (snapped to grid)
        for label in &labels {
            let x_remainder = label.position.x % 1.27;
            let y_remainder = label.position.y % 1.27;
            
            // Check if remainder is close to 0 or close to 1.27 (floating point precision)
            let x_aligned = x_remainder < 0.01 || (1.27 - x_remainder) < 0.01;
            let y_aligned = y_remainder < 0.01 || (1.27 - y_remainder) < 0.01;
            
            assert!(x_aligned,
                    "Label {} position x={:.6} should be grid-aligned (x % 1.27 = {:.6})",
                    label.name, label.position.x, x_remainder);
            assert!(y_aligned,
                    "Label {} position y={:.6} should be grid-aligned (y % 1.27 = {:.6})",
                    label.name, label.position.y, y_remainder);
        }
    }

    fn create_reference_design_circuit_data() -> CircuitData {
        CircuitData {
            name: "reference_design_circuit".to_string(),
            components: vec![
                Component {
                    reference: "U1".to_string(),
                    lib_id: "MCU_ST_STM32F1:STM32F103C8Tx".to_string(),
                    value: "STM32F103C8Tx".to_string(),
                    position: Position { x: 100.0, y: 100.0 },
                    rotation: 0.0,
                    pins: vec![
                        Pin {
                            number: "1".to_string(),
                            name: "VBAT".to_string(),
                            x: -12.7,
                            y: 17.78,
                            orientation: 180.0,
                        },
                        Pin {
                            number: "2".to_string(),
                            name: "PC13".to_string(),
                            x: -12.7,
                            y: 15.24,
                            orientation: 180.0,
                        },
                        Pin {
                            number: "5".to_string(),
                            name: "PA0".to_string(),
                            x: -12.7,
                            y: 7.62,
                            orientation: 180.0,
                        },
                        Pin {
                            number: "6".to_string(),
                            name: "PA1".to_string(),
                            x: -12.7,
                            y: 5.08,
                            orientation: 180.0,
                        },
                        Pin {
                            number: "7".to_string(),
                            name: "PA2".to_string(),
                            x: -12.7,
                            y: 2.54,
                            orientation: 180.0,
                        },
                        Pin {
                            number: "8".to_string(),
                            name: "PA3".to_string(),
                            x: -12.7,
                            y: 0.0,
                            orientation: 180.0,
                        },
                    ],
                },
            ],
            nets: vec![
                Net {
                    name: "VBAT".to_string(),
                    connected_pins: vec![
                        PinConnection {
                            component_ref: "U1".to_string(),
                            pin_id: "1".to_string(),
                        },
                    ],
                },
                Net {
                    name: "PC13".to_string(),
                    connected_pins: vec![
                        PinConnection {
                            component_ref: "U1".to_string(),
                            pin_id: "2".to_string(),
                        },
                    ],
                },
                Net {
                    name: "PA0".to_string(),
                    connected_pins: vec![
                        PinConnection {
                            component_ref: "U1".to_string(),
                            pin_id: "5".to_string(),
                        },
                    ],
                },
                Net {
                    name: "PA1".to_string(),
                    connected_pins: vec![
                        PinConnection {
                            component_ref: "U1".to_string(),
                            pin_id: "6".to_string(),
                        },
                    ],
                },
                Net {
                    name: "PA2".to_string(),
                    connected_pins: vec![
                        PinConnection {
                            component_ref: "U1".to_string(),
                            pin_id: "7".to_string(),
                        },
                    ],
                },
                Net {
                    name: "PA3".to_string(),
                    connected_pins: vec![
                        PinConnection {
                            component_ref: "U1".to_string(),
                            pin_id: "8".to_string(),
                        },
                    ],
                },
            ],
        }
    }

    fn create_test_circuit_data() -> CircuitData {
        CircuitData {
            name: "test_circuit".to_string(),
            components: vec![
                Component {
                    reference: "R1".to_string(),
                    lib_id: "Device:R".to_string(),
                    value: "1k".to_string(),
                    position: Position { x: 100.0, y: 100.0 },
                    rotation: 0.0,
                    pins: vec![
                        Pin {
                            number: "1".to_string(),
                            name: "~".to_string(),
                            x: 0.0,
                            y: 3.81,
                            orientation: 270.0,
                        },
                        Pin {
                            number: "2".to_string(),
                            name: "~".to_string(),
                            x: 0.0,
                            y: -3.81,
                            orientation: 90.0,
                        },
                    ],
                },
            ],
            nets: vec![
                Net {
                    name: "VCC".to_string(),
                    connected_pins: vec![
                        PinConnection {
                            component_ref: "R1".to_string(),
                            pin_id: "1".to_string(),
                        },
                    ],
                },
            ],
        }
    }
}
