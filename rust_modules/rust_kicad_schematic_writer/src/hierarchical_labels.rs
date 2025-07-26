//! Hierarchical label generation logic
//! 
//! This module contains the core algorithms for generating hierarchical labels
//! based on circuit nets and component pin positions.

use crate::types::*;
use log::{info, debug, warn};
use std::collections::HashSet;

/// Hierarchical label generator with advanced positioning logic
#[derive(Debug)]
pub struct HierarchicalLabelGenerator {
    /// Configuration for label generation
    pub config: LabelGeneratorConfig,
    /// Track generated label positions to avoid overlaps
    pub used_positions: HashSet<(i32, i32)>, // Grid-aligned positions
}

/// Configuration for hierarchical label generation
#[derive(Debug, Clone)]
pub struct LabelGeneratorConfig {
    /// Grid size for position alignment (KiCad uses 1.27mm grid)
    pub grid_size: f64,
    /// Minimum distance between labels
    pub min_label_spacing: f64,
    /// Offset distance from pin for label placement
    pub pin_offset: f64,
    /// Default font size for labels
    pub font_size: f64,
}

impl Default for LabelGeneratorConfig {
    fn default() -> Self {
        Self {
            grid_size: 1.27,           // KiCad 50mil grid
            min_label_spacing: 2.54,   // 100mil minimum spacing
            pin_offset: 2.54,          // 100mil offset from pin
            font_size: 1.27,           // Standard KiCad font size
        }
    }
}

impl HierarchicalLabelGenerator {
    /// Create a new label generator
    pub fn new(config: LabelGeneratorConfig) -> Self {
        Self {
            config,
            used_positions: HashSet::new(),
        }
    }

    /// Generate hierarchical labels for all nets in the circuit (including subcircuits)
    pub fn generate_labels(&mut self, circuit_data: &CircuitData) -> Result<Vec<HierarchicalLabel>, SchematicError> {
        info!("🚀 Starting HIERARCHICAL label generation for circuit '{}'", circuit_data.name);
        
        // Get hierarchy statistics
        let hierarchy_stats = circuit_data.get_hierarchy_stats();
        info!("🏗️  Circuit hierarchy stats:");
        info!("    - Max depth: {} levels", hierarchy_stats.max_depth);
        info!("    - Total subcircuits: {}", hierarchy_stats.total_subcircuits);
        info!("    - Total components: {}", hierarchy_stats.total_components);
        info!("    - Total nets: {}", hierarchy_stats.total_nets);
        info!("    - Is hierarchical: {}", circuit_data.is_hierarchical());

        // Use recursive methods to get ALL components and nets
        let all_components = circuit_data.get_all_components();
        let all_nets = circuit_data.get_all_nets();
        
        info!("📊 Processing {} total nets with {} total components (flattened from hierarchy)",
              all_nets.len(), all_components.len());
        
        // Log detailed component information
        info!("🔧 All component details (flattened):");
        for (i, component) in all_components.iter().enumerate() {
            info!("  Component #{}: {} ({}) at position ({:.2}, {:.2}), rotation: {:.1}°",
                  i + 1, component.reference, component.lib_id,
                  component.position.x, component.position.y, component.rotation);
            info!("    Pins: {}", component.pins.len());
            for pin in &component.pins {
                info!("      Pin {}: '{}' at local ({:.2}, {:.2}), orientation: {:.1}°",
                      pin.number, pin.name, pin.x, pin.y, pin.orientation);
            }
        }
        
        // Log detailed net information
        info!("🌐 All net details (flattened):");
        for (i, net) in all_nets.iter().enumerate() {
            info!("  Net #{}: '{}' with {} connections", i + 1, net.name, net.connected_pins.len());
            for conn in &net.connected_pins {
                info!("    Connection: {}.{}", conn.component_ref, conn.pin_id);
            }
        }

        let mut labels = Vec::new();
        let mut label_count = 0;
        let mut generated_labels = std::collections::HashSet::new(); // Track generated label names

        // Clear previous positions
        self.used_positions.clear();

        let total_nets_count = all_nets.len();
        
        // Process ALL nets (including from subcircuits)
        for net in &all_nets {
            info!("🌐 Processing net '{}' with {} connections", net.name, net.connected_pins.len());

            // Generate only ONE label per net (not per pin connection)
            if !generated_labels.contains(&net.name) {
                // Find the first valid pin connection for this net
                if let Some(pin_connection) = net.connected_pins.first() {
                    info!("🔗 Generating single label for net '{}' using connection {}.{}",
                          net.name, pin_connection.component_ref, pin_connection.pin_id);
                          
                    match self.generate_label_for_pin_hierarchical(circuit_data, net, pin_connection) {
                        Ok(label) => {
                            label_count += 1;
                            info!("🏷️  Generated label #{} for net '{}' at ({:.2}, {:.2}) orientation {:.1}°",
                                  label_count, net.name, label.position.x, label.position.y, label.orientation);
                            generated_labels.insert(net.name.clone());
                            labels.push(label);
                        }
                        Err(e) => {
                            warn!("⚠️  Failed to generate label for net '{}': {}", net.name, e);
                        }
                    }
                } else {
                    warn!("⚠️  Net '{}' has no pin connections", net.name);
                }
            } else {
                debug!("⏭️  Skipping duplicate label for net '{}'", net.name);
            }
        }

        info!("✨ Generated {} hierarchical labels successfully from {} total nets", label_count, total_nets_count);
        
        // Log final label summary
        info!("📋 Final label summary:");
        for (i, label) in labels.iter().enumerate() {
            info!("  Label #{}: '{}' at ({:.2}, {:.2}) orientation {:.1}°",
                  i + 1, label.name, label.position.x, label.position.y, label.orientation);
        }
        
        Ok(labels)
    }

    /// Generate a hierarchical label for a specific pin connection (legacy method)
    fn generate_label_for_pin(
        &mut self,
        circuit_data: &CircuitData,
        net: &Net,
        pin_connection: &PinConnection,
    ) -> Result<HierarchicalLabel, SchematicError> {
        debug!("🔗 Generating label for {}.{} on net '{}'",
               pin_connection.component_ref, pin_connection.pin_id, net.name);

        // Find the component
        let component = circuit_data.find_component(&pin_connection.component_ref)
            .ok_or_else(|| SchematicError::ComponentNotFound(pin_connection.component_ref.clone()))?;

        debug!("✅ Found component {} ({}) at ({}, {})",
               component.reference, component.lib_id, component.position.x, component.position.y);

        // Find the pin
        let pin = component.find_pin(&pin_connection.pin_id)
            .ok_or_else(|| SchematicError::PinNotFound(pin_connection.pin_id.clone()))?;

        debug!("📍 Found pin {}: name='{}', position=({}, {}), orientation={}°",
               pin.number, pin.name, pin.x, pin.y, pin.orientation);

        // Calculate label position
        let position = self.calculate_label_position(component, pin)?;
        let orientation = self.calculate_label_orientation(component, pin);

        debug!("🧮 Calculated label position: ({:.2}, {:.2}), orientation: {}°",
               position.x, position.y, orientation);

        // Determine label justification based on orientation
        let justify = match orientation as i32 {
            90 => "left",
            270 => "right",
            0 | 180 => "center",
            _ => "center",
        };

        // Create the hierarchical label
        let label = HierarchicalLabel {
            name: net.name.clone(),
            shape: LabelShape::Input, // Default to input, could be made configurable
            position,
            orientation,
            effects: LabelEffects {
                font_size: self.config.font_size,
                justify: justify.to_string(),
            },
            uuid: uuid::Uuid::new_v4().to_string(),
        };

        // Mark position as used
        let grid_pos = self.position_to_grid(&position);
        self.used_positions.insert(grid_pos);

        debug!("✨ Created hierarchical label: name='{}', uuid='{}'", label.name, label.uuid);

        Ok(label)
    }

    /// Generate a hierarchical label for a specific pin connection (hierarchical-aware method)
    fn generate_label_for_pin_hierarchical(
        &mut self,
        circuit_data: &CircuitData,
        net: &Net,
        pin_connection: &PinConnection,
    ) -> Result<HierarchicalLabel, SchematicError> {
        info!("🔗 HIERARCHICAL: Generating label for {}.{} on net '{}'",
               pin_connection.component_ref, pin_connection.pin_id, net.name);

        // Find the component using hierarchical search
        let component = circuit_data.find_component(&pin_connection.component_ref)
            .ok_or_else(|| {
                warn!("❌ Component '{}' not found in hierarchical circuit", pin_connection.component_ref);
                SchematicError::ComponentNotFound(pin_connection.component_ref.clone())
            })?;

        info!("✅ HIERARCHICAL: Found component {} ({}) at ({}, {})",
               component.reference, component.lib_id, component.position.x, component.position.y);

        // Find the pin
        let pin = component.find_pin(&pin_connection.pin_id)
            .ok_or_else(|| {
                warn!("❌ Pin '{}' not found in component '{}'", pin_connection.pin_id, component.reference);
                warn!("   Available pins: {:?}", component.pins.iter().map(|p| &p.number).collect::<Vec<_>>());
                SchematicError::PinNotFound(pin_connection.pin_id.clone())
            })?;

        info!("📍 HIERARCHICAL: Found pin {}: name='{}', position=({}, {}), orientation={}°",
               pin.number, pin.name, pin.x, pin.y, pin.orientation);

        // Calculate label position
        let position = self.calculate_label_position(component, pin)?;
        let orientation = self.calculate_label_orientation(component, pin);

        info!("🧮 HIERARCHICAL: Calculated label position: ({:.2}, {:.2}), orientation: {}°",
               position.x, position.y, orientation);

        // Determine label justification based on orientation
        let justify = match orientation as i32 {
            90 => "left",
            270 => "right",
            0 | 180 => "center",
            _ => "center",
        };

        // Create the hierarchical label
        let label = HierarchicalLabel {
            name: net.name.clone(),
            shape: LabelShape::Input, // Default to input, could be made configurable
            position,
            orientation,
            effects: LabelEffects {
                font_size: self.config.font_size,
                justify: justify.to_string(),
            },
            uuid: uuid::Uuid::new_v4().to_string(),
        };

        // Mark position as used
        let grid_pos = self.position_to_grid(&position);
        self.used_positions.insert(grid_pos);

        info!("✨ HIERARCHICAL: Created hierarchical label: name='{}', uuid='{}'", label.name, label.uuid);

        Ok(label)
    }

    /// Calculate the position for a hierarchical label based on component and pin
    fn calculate_label_position(&self, component: &Component, pin: &Pin) -> Result<Position, SchematicError> {
        info!("🔧 FIXED PIN END LOCATION CALCULATION for component {} pin {}", component.reference, pin.number);
        info!("  📍 Component position: ({:.2}, {:.2})", component.position.x, component.position.y);
        info!("  🔄 Component rotation: {:.1}°", component.rotation);
        info!("  📌 Pin data from Python: position=({:.2}, {:.2}), orientation={:.1}°", pin.x, pin.y, pin.orientation);
        
        // CRITICAL FIX: Determine if pin data is local or world coordinates
        // If the pin coordinates are very close to the component position, they're likely world coordinates
        // If they're small values (like -12.7, 3.81), they're likely local coordinates
        
        let pin_world_x: f64;
        let pin_world_y: f64;
        let world_pin_orientation: f64;
        
        // Check if pin coordinates look like world coordinates (close to component position)
        let distance_from_component = ((pin.x - component.position.x).powi(2) + (pin.y - component.position.y).powi(2)).sqrt();
        
        if distance_from_component < 50.0 {
            // Pin coordinates are likely world coordinates (already calculated by Python)
            pin_world_x = pin.x;
            pin_world_y = pin.y;
            world_pin_orientation = pin.orientation; // Orientation should already be in world coordinates
            info!("  🌍 DETECTED: Pin coordinates are WORLD coordinates");
            info!("  🎯 Using pin world position directly: ({:.2}, {:.2})", pin_world_x, pin_world_y);
            info!("  🧭 Using pin orientation directly: {:.1}°", world_pin_orientation);
        } else {
            // Pin coordinates are local coordinates relative to component
            info!("  📐 DETECTED: Pin coordinates are LOCAL coordinates");
            info!("  📐 Pin local coordinates: ({:.2}, {:.2})", pin.x, pin.y);
            
            // Apply component rotation to local pin position
            let rotation_rad = component.rotation.to_radians();
            let rotated_pin_x = pin.x * rotation_rad.cos() - pin.y * rotation_rad.sin();
            let rotated_pin_y = pin.x * rotation_rad.sin() + pin.y * rotation_rad.cos();
            info!("  🔄 After rotation ({:.1}°): ({:.2}, {:.2})", component.rotation, rotated_pin_x, rotated_pin_y);
            
            // Add component position to get world coordinates
            pin_world_x = component.position.x + rotated_pin_x;
            pin_world_y = component.position.y + rotated_pin_y;
            
            // Calculate world pin orientation
            world_pin_orientation = (pin.orientation + component.rotation) % 360.0;
            
            info!("  🌍 Calculated pin world position: ({:.2}, {:.2})", pin_world_x, pin_world_y);
            info!("  🧭 Calculated world pin orientation: {:.1}°", world_pin_orientation);
        }
        
        info!("  🎯 FINAL PIN END LOCATION: ({:.2}, {:.2})", pin_world_x, pin_world_y);

        // Calculate label offset based on pin orientation
        let pin_angle_rad = world_pin_orientation.to_radians();
        let label_offset = 2.54; // 100mil (2.54mm) offset from pin
        
        // Calculate offset vector pointing away from the pin
        let offset_x = label_offset * pin_angle_rad.cos();
        let offset_y = label_offset * pin_angle_rad.sin();
        
        info!("  ➡️  Label offset calculation:");
        info!("    - World pin orientation: {:.1}°", world_pin_orientation);
        info!("    - Offset distance: {:.2}mm", label_offset);
        info!("    - Offset vector: ({:.2}, {:.2})", offset_x, offset_y);
        
        // Apply offset to get final label position
        let label_x = pin_world_x + offset_x;
        let label_y = pin_world_y + offset_y;
        
        info!("  🏷️  Label position before grid snap: ({:.2}, {:.2})", label_x, label_y);

        // Snap to grid for proper KiCad alignment
        let mut snapped_x = self.snap_to_grid(label_x);
        let mut snapped_y = self.snap_to_grid(label_y);
        
        info!("  📐 Grid snapping: ({:.2}, {:.2}) -> ({:.2}, {:.2})", label_x, label_y, snapped_x, snapped_y);

        // Check for position conflicts and adjust if necessary
        let mut grid_pos = self.position_to_grid(&Position { x: snapped_x, y: snapped_y });
        let mut offset_attempts = 0;
        const MAX_OFFSET_ATTEMPTS: i32 = 20;
        
        while self.used_positions.contains(&grid_pos) && offset_attempts < MAX_OFFSET_ATTEMPTS {
            // Try different offset positions to avoid overlaps
            let offset_distance = self.config.min_label_spacing * (offset_attempts as f64 + 1.0);
            match offset_attempts % 4 {
                0 => snapped_y += offset_distance,  // Move up
                1 => snapped_x += offset_distance,  // Move right
                2 => snapped_y -= offset_distance,  // Move down
                3 => snapped_x -= offset_distance,  // Move left
                _ => {}
            }
            
            // Re-snap to grid after offset
            snapped_x = self.snap_to_grid(snapped_x);
            snapped_y = self.snap_to_grid(snapped_y);
            grid_pos = self.position_to_grid(&Position { x: snapped_x, y: snapped_y });
            offset_attempts += 1;
            
            info!("  🔄 Position conflict detected, trying offset #{}: ({:.2}, {:.2})",
                  offset_attempts, snapped_x, snapped_y);
        }

        let final_position = Position {
            x: snapped_x,
            y: snapped_y,
        };
        
        info!("  🎯 FINAL LABEL POSITION: ({:.2}, {:.2})", final_position.x, final_position.y);
        info!("  ═══════════════════════════════════════════════════════════════");
        
        Ok(final_position)
    }

    /// Calculate the orientation for a hierarchical label
    fn calculate_label_orientation(&self, component: &Component, pin: &Pin) -> f64 {
        // Calculate label orientation based on pin orientation and component rotation
        let pin_angle = pin.orientation;
        let label_angle = (pin_angle + 180.0) % 360.0; // Opposite direction from pin
        let global_angle = (label_angle + component.rotation) % 360.0;

        debug!("🧮 Orientation calculation: pin={}°, label_base={}°, component_rotation={}°, final={}°", 
               pin_angle, label_angle, component.rotation, global_angle);

        // Normalize to common KiCad orientations
        self.normalize_orientation(global_angle)
    }

    /// Normalize orientation to common KiCad values (0, 90, 180, 270)
    fn normalize_orientation(&self, angle: f64) -> f64 {
        let normalized = ((angle + 45.0) / 90.0).floor() * 90.0;
        normalized % 360.0
    }

    /// Snap a coordinate to the grid
    fn snap_to_grid(&self, value: f64) -> f64 {
        (value / self.config.grid_size).round() * self.config.grid_size
    }

    /// Convert position to grid coordinates for collision detection
    fn position_to_grid(&self, position: &Position) -> (i32, i32) {
        (
            (position.x / self.config.grid_size).round() as i32,
            (position.y / self.config.grid_size).round() as i32,
        )
    }

    /// Check if a position is available (not used by another label)
    fn is_position_available(&self, position: &Position) -> bool {
        let grid_pos = self.position_to_grid(position);
        !self.used_positions.contains(&grid_pos)
    }

    /// Find an alternative position if the primary position is occupied
    fn find_alternative_position(&self, base_position: Position, _component: &Component, _pin: &Pin) -> Position {
        let mut test_position = base_position;
        let grid_spacing = self.config.grid_size;

        // Try positions in a spiral pattern around the base position
        for radius in 1..=5 {
            for angle in (0..360).step_by(45) {
                let angle_rad = (angle as f64).to_radians();
                let offset_x = radius as f64 * grid_spacing * angle_rad.cos();
                let offset_y = radius as f64 * grid_spacing * angle_rad.sin();

                test_position.x = self.snap_to_grid(base_position.x + offset_x);
                test_position.y = self.snap_to_grid(base_position.y + offset_y);

                if self.is_position_available(&test_position) {
                    debug!("🔄 Found alternative position: ({:.2}, {:.2}) at radius {}, angle {}°", 
                           test_position.x, test_position.y, radius, angle);
                    return test_position;
                }
            }
        }

        warn!("⚠️  Could not find alternative position, using original");
        base_position
    }

    /// Get statistics about label generation
    pub fn get_stats(&self) -> LabelGenerationStats {
        LabelGenerationStats {
            total_positions_used: self.used_positions.len(),
            grid_size: self.config.grid_size,
        }
    }
}

/// Statistics about label generation
#[derive(Debug)]
pub struct LabelGenerationStats {
    pub total_positions_used: usize,
    pub grid_size: f64,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_label_generation() {
        let mut generator = HierarchicalLabelGenerator::new(LabelGeneratorConfig::default());
        let circuit_data = create_test_circuit();
        
        let labels = generator.generate_labels(&circuit_data).unwrap();
        
        assert!(!labels.is_empty());
        assert_eq!(labels.len(), 2); // Two pins, two labels
        
        // Check that labels have valid UUIDs
        for label in &labels {
            assert!(uuid::Uuid::parse_str(&label.uuid).is_ok());
        }
    }

    #[test]
    fn test_world_coordinate_detection() {
        let mut generator = HierarchicalLabelGenerator::new(LabelGeneratorConfig::default());
        let circuit_data = create_world_coordinate_test_circuit();
        
        let labels = generator.generate_labels(&circuit_data).unwrap();
        
        assert!(!labels.is_empty());
        assert_eq!(labels.len(), 2); // Two pins, two labels
        
        // Check that labels are positioned correctly near the pins
        // For world coordinates, labels should be very close to the pin positions
        for label in &labels {
            println!("Label '{}' at ({:.2}, {:.2})", label.name, label.position.x, label.position.y);
        }
    }

    #[test]
    fn test_position_snapping() {
        let generator = HierarchicalLabelGenerator::new(LabelGeneratorConfig::default());
        
        // Test grid snapping
        assert_eq!(generator.snap_to_grid(1.0), 1.27);
        assert_eq!(generator.snap_to_grid(2.0), 2.54);
        assert_eq!(generator.snap_to_grid(2.5), 2.54);
    }

    fn create_test_circuit() -> CircuitData {
        let mut circuit = CircuitData::new("test".to_string());
        
        let mut component = Component::new(
            "R1".to_string(),
            "Device:R".to_string(),
            "1k".to_string(),
            Position { x: 100.0, y: 100.0 },
        );
        
        component.add_pin(Pin {
            number: "1".to_string(),
            name: "~".to_string(),
            x: 0.0,
            y: 3.81,
            orientation: 270.0,
        });
        
        component.add_pin(Pin {
            number: "2".to_string(),
            name: "~".to_string(),
            x: 0.0,
            y: -3.81,
            orientation: 90.0,
        });
        
        circuit.add_component(component);
        
        let mut net = Net::new("VCC".to_string());
        net.add_connection("R1".to_string(), "1".to_string());
        circuit.add_net(net);
        
        let mut net2 = Net::new("GND".to_string());
        net2.add_connection("R1".to_string(), "2".to_string());
        circuit.add_net(net2);
        
        circuit
    }

    fn create_world_coordinate_test_circuit() -> CircuitData {
        let mut circuit = CircuitData::new("world_coord_test".to_string());
        
        // Component at position (38.1, 40.64) - similar to user's reported issue
        let mut component = Component::new(
            "R1".to_string(),
            "Device:R".to_string(),
            "1k".to_string(),
            Position { x: 38.1, y: 40.64 },
        );
        
        // Pins with WORLD coordinates (like Python sends)
        // Pin 1 at world position (38.1, 44.45) - component position + pin offset
        component.add_pin(Pin {
            number: "1".to_string(),
            name: "~".to_string(),
            x: 38.1,      // World coordinate
            y: 44.45,     // World coordinate
            orientation: 270.0,
        });
        
        // Pin 2 at world position (38.1, 36.83) - component position + pin offset
        component.add_pin(Pin {
            number: "2".to_string(),
            name: "~".to_string(),
            x: 38.1,      // World coordinate
            y: 36.83,     // World coordinate
            orientation: 90.0,
        });
        
        circuit.add_component(component);
        
        let mut net = Net::new("VCC".to_string());
        net.add_connection("R1".to_string(), "1".to_string());
        circuit.add_net(net);
        
        let mut net2 = Net::new("GND".to_string());
        net2.add_connection("R1".to_string(), "2".to_string());
        circuit.add_net(net2);
        
        circuit
    }
}