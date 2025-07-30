//! Pin position calculator with reference design matching logic

use crate::coordinate_transform::{
    positions_approximately_equal, transform_component_pins, transform_pin_position,
};
use crate::types::{
    CalculationConfig, Component, HierarchicalLabelPosition, LabelOrientation, LabelShape, Net,
    PinCalculationError, PinPositionResult, PinReference, Position, Result,
};
use std::collections::HashMap;

/// Main pin calculator struct
pub struct PinCalculator {
    config: CalculationConfig,
    components: HashMap<String, Component>,
}

impl PinCalculator {
    /// Create a new pin calculator with default configuration
    pub fn new() -> Self {
        Self {
            config: CalculationConfig::default(),
            components: HashMap::new(),
        }
    }

    /// Create a new pin calculator with custom configuration
    pub fn with_config(config: CalculationConfig) -> Self {
        Self {
            config,
            components: HashMap::new(),
        }
    }

    /// Add a component to the calculator
    pub fn add_component(&mut self, component: Component) {
        self.components
            .insert(component.reference.clone(), component);
    }

    /// Get a component by reference
    pub fn get_component(&self, reference: &str) -> Option<&Component> {
        self.components.get(reference)
    }

    /// Get mutable access to a component by reference
    pub fn get_component_mut(&mut self, reference: &str) -> Option<&mut Component> {
        self.components.get_mut(reference)
    }

    /// Calculate pin positions for all components
    pub fn calculate_all_pin_positions(&self) -> Vec<PinPositionResult> {
        self.components
            .values()
            .flat_map(|component| transform_component_pins(component))
            .collect()
    }

    /// Calculate pin position for a specific component and pin
    pub fn calculate_pin_position(
        &self,
        component_ref: &str,
        pin_number: &str,
    ) -> Result<PinPositionResult> {
        let component = self
            .components
            .get(component_ref)
            .ok_or_else(|| PinCalculationError::ComponentNotFound(component_ref.to_string()))?;

        let pin =
            component
                .get_pin(pin_number)
                .ok_or_else(|| PinCalculationError::PinNotFound {
                    component_ref: component_ref.to_string(),
                    pin_number: pin_number.to_string(),
                })?;

        let global_position =
            transform_pin_position(component.position, pin.local_position, component.rotation);

        Ok(PinPositionResult {
            component_ref: component_ref.to_string(),
            pin_number: pin_number.to_string(),
            global_position,
            local_position: pin.local_position,
            rotation_applied: component.rotation,
        })
    }

    /// Calculate hierarchical label positions based on nets and component positions
    pub fn calculate_hierarchical_label_positions(
        &self,
        nets: &[Net],
    ) -> Result<Vec<HierarchicalLabelPosition>> {
        let mut label_positions = Vec::new();

        for net in nets {
            if let Some(position) = self.calculate_net_label_position(net)? {
                label_positions.push(position);
            }
        }

        Ok(label_positions)
    }

    /// Calculate the optimal position for a hierarchical label for a given net
    fn calculate_net_label_position(&self, net: &Net) -> Result<Option<HierarchicalLabelPosition>> {
        if net.pins.is_empty() {
            return Ok(None);
        }

        // Calculate positions of all pins in this net
        let mut pin_positions = Vec::new();
        for pin_ref in &net.pins {
            let pin_result =
                self.calculate_pin_position(&pin_ref.component_ref, &pin_ref.pin_number)?;
            pin_positions.push(pin_result.global_position);
        }

        // Find the optimal label position
        let label_position = self.find_optimal_label_position(&pin_positions, &net.name)?;

        Ok(Some(label_position))
    }

    /// Find the optimal position for a hierarchical label given pin positions
    fn find_optimal_label_position(
        &self,
        pin_positions: &[Position],
        net_name: &str,
    ) -> Result<HierarchicalLabelPosition> {
        if pin_positions.is_empty() {
            return Err(PinCalculationError::CalculationFailed(
                "No pin positions provided for label calculation".to_string(),
            ));
        }

        // Check if we have a reference position for this net
        if let Some(reference_pos) = self.config.reference_positions.get(net_name) {
            return Ok(HierarchicalLabelPosition {
                net_name: net_name.to_string(),
                position: *reference_pos,
                orientation: LabelOrientation::Right,
                shape: LabelShape::Bidirectional,
            });
        }

        // Calculate centroid of pin positions
        let centroid = self.calculate_centroid(pin_positions);

        // Determine optimal orientation based on pin distribution
        let orientation = self.determine_label_orientation(pin_positions, &centroid);

        // Offset the label position to avoid overlapping with components
        let label_position = self.offset_label_position(&centroid, &orientation);

        Ok(HierarchicalLabelPosition {
            net_name: net_name.to_string(),
            position: label_position,
            orientation,
            shape: LabelShape::Bidirectional,
        })
    }

    /// Calculate the centroid of a set of positions
    fn calculate_centroid(&self, positions: &[Position]) -> Position {
        let sum_x: f64 = positions.iter().map(|p| p.x).sum();
        let sum_y: f64 = positions.iter().map(|p| p.y).sum();
        let count = positions.len() as f64;

        Position::new(sum_x / count, sum_y / count)
    }

    /// Determine the optimal orientation for a label based on pin distribution
    fn determine_label_orientation(
        &self,
        positions: &[Position],
        centroid: &Position,
    ) -> LabelOrientation {
        if positions.len() < 2 {
            return LabelOrientation::Right;
        }

        // Calculate the spread in x and y directions
        let x_spread = positions
            .iter()
            .map(|p| (p.x - centroid.x).abs())
            .fold(0.0, f64::max);
        let y_spread = positions
            .iter()
            .map(|p| (p.y - centroid.y).abs())
            .fold(0.0, f64::max);

        // If pins are more spread horizontally, use vertical label orientation
        if x_spread > y_spread {
            LabelOrientation::Up
        } else {
            LabelOrientation::Right
        }
    }

    /// Offset label position to avoid component overlap
    fn offset_label_position(
        &self,
        centroid: &Position,
        orientation: &LabelOrientation,
    ) -> Position {
        let offset = 5.0; // 5mm offset

        match orientation {
            LabelOrientation::Right => Position::new(centroid.x + offset, centroid.y),
            LabelOrientation::Left => Position::new(centroid.x - offset, centroid.y),
            LabelOrientation::Up => Position::new(centroid.x, centroid.y + offset),
            LabelOrientation::Down => Position::new(centroid.x, centroid.y - offset),
        }
    }

    /// Validate calculated positions against reference design
    pub fn validate_against_reference(
        &self,
        component_ref: &str,
        pin_number: &str,
    ) -> Result<bool> {
        let calculated = self.calculate_pin_position(component_ref, pin_number)?;

        let reference_key = format!("{}.{}", component_ref, pin_number);
        if let Some(reference_pos) = self.config.reference_positions.get(&reference_key) {
            let matches = positions_approximately_equal(
                &calculated.global_position,
                reference_pos,
                self.config.position_tolerance,
            );

            if !matches && self.config.use_reference_positions {
                return Err(PinCalculationError::ReferenceDesignMismatch {
                    expected: *reference_pos,
                    actual: calculated.global_position,
                });
            }

            Ok(matches)
        } else {
            // No reference position available, consider it valid
            Ok(true)
        }
    }

    /// Create reference design configuration for resistor divider circuit
    pub fn create_reference_design_config() -> CalculationConfig {
        let mut reference_positions = HashMap::new();

        // Reference design positions from the task specification
        // R1: (95.25, 62.23) with pins at (95.25, 58.42) and (95.25, 66.04)
        reference_positions.insert("R1.1".to_string(), Position::new(95.25, 58.42));
        reference_positions.insert("R1.2".to_string(), Position::new(95.25, 66.04));

        // R2: (106.68, 62.23) with pins at (106.68, 58.42) and (106.68, 66.04)
        reference_positions.insert("R2.1".to_string(), Position::new(106.68, 58.42));
        reference_positions.insert("R2.2".to_string(), Position::new(106.68, 66.04));

        // C1: (120.65, 63.5) with pins at (120.65, 59.69) and (120.65, 67.31)
        reference_positions.insert("C1.1".to_string(), Position::new(120.65, 59.69));
        reference_positions.insert("C1.2".to_string(), Position::new(120.65, 67.31));

        CalculationConfig {
            position_tolerance: 0.01,
            default_pin_offset: 1.905,
            use_reference_positions: true,
            reference_positions,
        }
    }

    /// Create components for reference design testing
    pub fn create_reference_design_components() -> Vec<Component> {
        use crate::types::{Pin, PinOrientation, PinType};

        let mut components = Vec::new();

        // R1 component
        let mut r1 = Component::new("R1".to_string(), Position::new(95.25, 62.23), 0.0);
        r1.component_type = "Resistor".to_string();
        r1.value = Some("10k".to_string());
        r1.add_pin(Pin {
            number: "1".to_string(),
            name: Some("A".to_string()),
            local_position: Position::new(0.0, -3.81), // -3.81mm offset for pin 1
            pin_type: PinType::Passive,
            orientation: PinOrientation::Down,
        });
        r1.add_pin(Pin {
            number: "2".to_string(),
            name: Some("B".to_string()),
            local_position: Position::new(0.0, 3.81), // +3.81mm offset for pin 2
            pin_type: PinType::Passive,
            orientation: PinOrientation::Up,
        });
        components.push(r1);

        // R2 component
        let mut r2 = Component::new("R2".to_string(), Position::new(106.68, 62.23), 0.0);
        r2.component_type = "Resistor".to_string();
        r2.value = Some("10k".to_string());
        r2.add_pin(Pin {
            number: "1".to_string(),
            name: Some("A".to_string()),
            local_position: Position::new(0.0, -3.81),
            pin_type: PinType::Passive,
            orientation: PinOrientation::Down,
        });
        r2.add_pin(Pin {
            number: "2".to_string(),
            name: Some("B".to_string()),
            local_position: Position::new(0.0, 3.81),
            pin_type: PinType::Passive,
            orientation: PinOrientation::Up,
        });
        components.push(r2);

        // C1 component
        let mut c1 = Component::new("C1".to_string(), Position::new(120.65, 63.5), 0.0);
        c1.component_type = "Capacitor".to_string();
        c1.value = Some("100nF".to_string());
        c1.add_pin(Pin {
            number: "1".to_string(),
            name: Some("A".to_string()),
            local_position: Position::new(0.0, -3.81),
            pin_type: PinType::Passive,
            orientation: PinOrientation::Down,
        });
        c1.add_pin(Pin {
            number: "2".to_string(),
            name: Some("B".to_string()),
            local_position: Position::new(0.0, 3.81),
            pin_type: PinType::Passive,
            orientation: PinOrientation::Up,
        });
        components.push(c1);

        components
    }

    /// Create nets for reference design testing
    pub fn create_reference_design_nets() -> Vec<Net> {
        vec![
            Net {
                name: "VCC".to_string(),
                pins: vec![PinReference::new("R1".to_string(), "2".to_string())],
            },
            Net {
                name: "OUT".to_string(),
                pins: vec![
                    PinReference::new("R1".to_string(), "1".to_string()),
                    PinReference::new("R2".to_string(), "2".to_string()),
                    PinReference::new("C1".to_string(), "1".to_string()),
                ],
            },
            Net {
                name: "GND".to_string(),
                pins: vec![
                    PinReference::new("R2".to_string(), "1".to_string()),
                    PinReference::new("C1".to_string(), "2".to_string()),
                ],
            },
        ]
    }
}

impl Default for PinCalculator {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_pin_calculator_creation() {
        let calculator = PinCalculator::new();
        assert_eq!(calculator.components.len(), 0);
    }

    #[test]
    fn test_add_and_get_component() {
        let mut calculator = PinCalculator::new();
        let component = Component::new("R1".to_string(), Position::new(100.0, 50.0), 0.0);

        calculator.add_component(component);

        assert!(calculator.get_component("R1").is_some());
        assert!(calculator.get_component("R2").is_none());
    }

    #[test]
    fn test_reference_design_components() {
        let components = PinCalculator::create_reference_design_components();
        assert_eq!(components.len(), 3);

        let r1 = &components[0];
        assert_eq!(r1.reference, "R1");
        assert_relative_eq!(r1.position.x, 95.25);
        assert_relative_eq!(r1.position.y, 62.23);
        assert_eq!(r1.pins.len(), 2);
    }

    #[test]
    fn test_reference_design_pin_positions() {
        let components = PinCalculator::create_reference_design_components();
        let mut calculator = PinCalculator::new();

        for component in components {
            calculator.add_component(component);
        }

        // Test R1 pin positions
        let r1_pin1 = calculator.calculate_pin_position("R1", "1").unwrap();
        let r1_pin2 = calculator.calculate_pin_position("R1", "2").unwrap();

        assert_relative_eq!(r1_pin1.global_position.x, 95.25);
        assert_relative_eq!(r1_pin1.global_position.y, 58.42);
        assert_relative_eq!(r1_pin2.global_position.x, 95.25);
        assert_relative_eq!(r1_pin2.global_position.y, 66.04);
    }

    #[test]
    fn test_reference_design_validation() {
        let config = PinCalculator::create_reference_design_config();
        let components = PinCalculator::create_reference_design_components();
        let mut calculator = PinCalculator::with_config(config);

        for component in components {
            calculator.add_component(component);
        }

        // Test validation against reference positions
        assert!(calculator.validate_against_reference("R1", "1").unwrap());
        assert!(calculator.validate_against_reference("R1", "2").unwrap());
        assert!(calculator.validate_against_reference("R2", "1").unwrap());
        assert!(calculator.validate_against_reference("R2", "2").unwrap());
        assert!(calculator.validate_against_reference("C1", "1").unwrap());
        assert!(calculator.validate_against_reference("C1", "2").unwrap());
    }

    #[test]
    fn test_hierarchical_label_calculation() {
        let components = PinCalculator::create_reference_design_components();
        let nets = PinCalculator::create_reference_design_nets();
        let mut calculator = PinCalculator::new();

        for component in components {
            calculator.add_component(component);
        }

        let labels = calculator
            .calculate_hierarchical_label_positions(&nets)
            .unwrap();

        assert_eq!(labels.len(), 3); // VCC, OUT, GND

        // Check that all labels have valid positions
        for label in &labels {
            assert!(!label.net_name.is_empty());
            assert!(label.position.x.is_finite());
            assert!(label.position.y.is_finite());
        }
    }

    #[test]
    fn test_centroid_calculation() {
        let calculator = PinCalculator::new();
        let positions = vec![
            Position::new(0.0, 0.0),
            Position::new(10.0, 0.0),
            Position::new(5.0, 10.0),
        ];

        let centroid = calculator.calculate_centroid(&positions);

        assert_relative_eq!(centroid.x, 5.0);
        assert_relative_eq!(centroid.y, 10.0 / 3.0);
    }

    #[test]
    fn test_label_orientation_determination() {
        let calculator = PinCalculator::new();
        let centroid = Position::new(5.0, 5.0);

        // Horizontally spread pins should result in vertical label
        let horizontal_positions = vec![Position::new(0.0, 5.0), Position::new(10.0, 5.0)];
        let orientation = calculator.determine_label_orientation(&horizontal_positions, &centroid);
        assert_eq!(orientation, LabelOrientation::Up);

        // Vertically spread pins should result in horizontal label
        let vertical_positions = vec![Position::new(5.0, 0.0), Position::new(5.0, 10.0)];
        let orientation = calculator.determine_label_orientation(&vertical_positions, &centroid);
        assert_eq!(orientation, LabelOrientation::Right);
    }
}
