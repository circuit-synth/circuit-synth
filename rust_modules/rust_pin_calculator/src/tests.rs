//! Comprehensive unit tests for the Rust Pin Calculator

#[cfg(test)]
mod tests {
    use crate::coordinate_transform::{angle_between_positions, rotation_matrix};
    use crate::*;
    use approx::assert_relative_eq;

    // Test data constants
    const TOLERANCE: f64 = 1e-10;
    const POSITION_TOLERANCE: f64 = 0.01;

    #[test]
    fn test_position_basic_operations() {
        let pos1 = Position::new(3.0, 4.0);
        let pos2 = Position::new(1.0, 2.0);

        // Test addition
        let sum = pos1.add(&pos2);
        assert_relative_eq!(sum.x, 4.0);
        assert_relative_eq!(sum.y, 6.0);

        // Test subtraction
        let diff = pos1.subtract(&pos2);
        assert_relative_eq!(diff.x, 2.0);
        assert_relative_eq!(diff.y, 2.0);

        // Test scaling
        let scaled = pos1.scale(2.0);
        assert_relative_eq!(scaled.x, 6.0);
        assert_relative_eq!(scaled.y, 8.0);

        // Test distance
        let distance = pos1.distance_to(&pos2);
        assert_relative_eq!(distance, (8.0_f64).sqrt());
    }

    #[test]
    fn test_pin_orientation_angles() {
        use types::PinOrientation;

        assert_relative_eq!(PinOrientation::Right.to_radians(), 0.0);
        assert_relative_eq!(PinOrientation::Up.to_radians(), std::f64::consts::PI / 2.0);
        assert_relative_eq!(PinOrientation::Left.to_radians(), std::f64::consts::PI);
        assert_relative_eq!(
            PinOrientation::Down.to_radians(),
            3.0 * std::f64::consts::PI / 2.0
        );
    }

    #[test]
    fn test_component_creation_and_pin_management() {
        use types::{Pin, PinOrientation, PinType};

        let mut component = Component::new("R1".to_string(), Position::new(100.0, 50.0), 0.0);
        assert_eq!(component.reference, "R1");
        assert_relative_eq!(component.position.x, 100.0);
        assert_relative_eq!(component.position.y, 50.0);
        assert_relative_eq!(component.rotation, 0.0);
        assert_eq!(component.pins.len(), 0);

        // Add pins
        let pin1 = Pin {
            number: "1".to_string(),
            name: Some("A".to_string()),
            local_position: Position::new(-1.905, 0.0),
            pin_type: PinType::Passive,
            orientation: PinOrientation::Left,
        };

        let pin2 = Pin {
            number: "2".to_string(),
            name: Some("B".to_string()),
            local_position: Position::new(1.905, 0.0),
            pin_type: PinType::Passive,
            orientation: PinOrientation::Right,
        };

        component.add_pin(pin1);
        component.add_pin(pin2);

        assert_eq!(component.pins.len(), 2);
        assert!(component.get_pin("1").is_some());
        assert!(component.get_pin("2").is_some());
        assert!(component.get_pin("3").is_none());

        let pin_numbers = component.get_pin_numbers();
        assert_eq!(pin_numbers, vec!["1", "2"]);
    }

    #[test]
    fn test_coordinate_transformations() {
        // Test basic transformation (no rotation)
        let component_pos = Position::new(100.0, 50.0);
        let local_pin_pos = Position::new(2.0, 1.0);
        let rotation = 0.0;

        let result = transform_pin_position(component_pos, local_pin_pos, rotation);
        assert_relative_eq!(result.x, 102.0);
        assert_relative_eq!(result.y, 51.0);

        // Test 90-degree rotation
        let rotation = 90.0;
        let result = transform_pin_position(component_pos, local_pin_pos, rotation);
        assert_relative_eq!(result.x, 99.0, epsilon = TOLERANCE);
        assert_relative_eq!(result.y, 52.0, epsilon = TOLERANCE);

        // Test 180-degree rotation
        let rotation = 180.0;
        let result = transform_pin_position(component_pos, local_pin_pos, rotation);
        assert_relative_eq!(result.x, 98.0, epsilon = TOLERANCE);
        assert_relative_eq!(result.y, 49.0, epsilon = TOLERANCE);

        // Test 270-degree rotation
        let rotation = 270.0;
        let result = transform_pin_position(component_pos, local_pin_pos, rotation);
        assert_relative_eq!(result.x, 101.0, epsilon = TOLERANCE);
        assert_relative_eq!(result.y, 48.0, epsilon = TOLERANCE);
    }

    #[test]
    fn test_inverse_coordinate_transformation() {
        let component_pos = Position::new(10.0, 20.0);
        let local_pin_pos = Position::new(3.0, 4.0);
        let rotation = 45.0;

        // Forward transformation
        let global_pos = transform_pin_position(component_pos, local_pin_pos, rotation);

        // Inverse transformation
        let recovered_local = inverse_transform_pin_position(component_pos, global_pos, rotation);

        assert_relative_eq!(recovered_local.x, local_pin_pos.x, epsilon = TOLERANCE);
        assert_relative_eq!(recovered_local.y, local_pin_pos.y, epsilon = TOLERANCE);
    }

    #[test]
    fn test_component_pin_transformation() {
        use types::{Pin, PinOrientation, PinType};

        let mut component = Component::new("R1".to_string(), Position::new(100.0, 50.0), 90.0);

        let pin1 = Pin {
            number: "1".to_string(),
            name: Some("A".to_string()),
            local_position: Position::new(-1.905, 0.0),
            pin_type: PinType::Passive,
            orientation: PinOrientation::Left,
        };

        let pin2 = Pin {
            number: "2".to_string(),
            name: Some("B".to_string()),
            local_position: Position::new(1.905, 0.0),
            pin_type: PinType::Passive,
            orientation: PinOrientation::Right,
        };

        component.add_pin(pin1);
        component.add_pin(pin2);

        let results = transform_component_pins(&component);

        assert_eq!(results.len(), 2);

        // With 90° rotation: (-1.905, 0) -> (0, -1.905) -> (100, 48.095)
        assert_relative_eq!(results[0].global_position.x, 100.0, epsilon = TOLERANCE);
        assert_relative_eq!(results[0].global_position.y, 48.095, epsilon = TOLERANCE);

        // With 90° rotation: (1.905, 0) -> (0, 1.905) -> (100, 51.905)
        assert_relative_eq!(results[1].global_position.x, 100.0, epsilon = TOLERANCE);
        assert_relative_eq!(results[1].global_position.y, 51.905, epsilon = TOLERANCE);
    }

    #[test]
    fn test_pin_calculator_basic_operations() {
        let mut calculator = PinCalculator::new();

        // Test empty calculator
        assert_eq!(calculator.calculate_all_pin_positions().len(), 0);
        assert!(calculator.get_component("R1").is_none());

        // Add a component
        let component = Component::new("R1".to_string(), Position::new(100.0, 50.0), 0.0);
        calculator.add_component(component);

        assert!(calculator.get_component("R1").is_some());
    }

    #[test]
    fn test_reference_design_components_creation() {
        let components = PinCalculator::create_reference_design_components();

        assert_eq!(components.len(), 3);

        // Test R1
        let r1 = &components[0];
        assert_eq!(r1.reference, "R1");
        assert_relative_eq!(r1.position.x, 95.25);
        assert_relative_eq!(r1.position.y, 62.23);
        assert_relative_eq!(r1.rotation, 0.0);
        assert_eq!(r1.pins.len(), 2);
        assert_eq!(r1.component_type, "Resistor");
        assert_eq!(r1.value, Some("10k".to_string()));

        // Test R2
        let r2 = &components[1];
        assert_eq!(r2.reference, "R2");
        assert_relative_eq!(r2.position.x, 106.68);
        assert_relative_eq!(r2.position.y, 62.23);

        // Test C1
        let c1 = &components[2];
        assert_eq!(c1.reference, "C1");
        assert_relative_eq!(c1.position.x, 120.65);
        assert_relative_eq!(c1.position.y, 63.5);
        assert_eq!(c1.component_type, "Capacitor");
        assert_eq!(c1.value, Some("100nF".to_string()));
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

        // Test R2 pin positions
        let r2_pin1 = calculator.calculate_pin_position("R2", "1").unwrap();
        let r2_pin2 = calculator.calculate_pin_position("R2", "2").unwrap();

        assert_relative_eq!(r2_pin1.global_position.x, 106.68);
        assert_relative_eq!(r2_pin1.global_position.y, 58.42);
        assert_relative_eq!(r2_pin2.global_position.x, 106.68);
        assert_relative_eq!(r2_pin2.global_position.y, 66.04);

        // Test C1 pin positions
        let c1_pin1 = calculator.calculate_pin_position("C1", "1").unwrap();
        let c1_pin2 = calculator.calculate_pin_position("C1", "2").unwrap();

        assert_relative_eq!(c1_pin1.global_position.x, 120.65);
        assert_relative_eq!(c1_pin1.global_position.y, 59.69);
        assert_relative_eq!(c1_pin2.global_position.x, 120.65);
        assert_relative_eq!(c1_pin2.global_position.y, 67.31);
    }

    #[test]
    fn test_reference_design_validation() {
        let config = PinCalculator::create_reference_design_config();
        let components = PinCalculator::create_reference_design_components();
        let mut calculator = PinCalculator::with_config(config);

        for component in components {
            calculator.add_component(component);
        }

        // All reference design positions should validate
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

        // Check that all labels have valid positions and names
        let mut label_names: Vec<String> = labels.iter().map(|l| l.net_name.clone()).collect();
        label_names.sort();
        assert_eq!(label_names, vec!["GND", "OUT", "VCC"]);

        for label in &labels {
            assert!(!label.net_name.is_empty());
            assert!(label.position.x.is_finite());
            assert!(label.position.y.is_finite());
        }
    }

    #[test]
    fn test_error_handling() {
        let mut calculator = PinCalculator::new();

        // Test component not found
        let result = calculator.calculate_pin_position("NONEXISTENT", "1");
        assert!(result.is_err());
        match result.unwrap_err() {
            PinCalculationError::ComponentNotFound(ref_name) => {
                assert_eq!(ref_name, "NONEXISTENT");
            }
            _ => panic!("Expected ComponentNotFound error"),
        }

        // Add a component without pins
        let component = Component::new("R1".to_string(), Position::new(0.0, 0.0), 0.0);
        calculator.add_component(component);

        // Test pin not found
        let result = calculator.calculate_pin_position("R1", "1");
        assert!(result.is_err());
        match result.unwrap_err() {
            PinCalculationError::PinNotFound {
                component_ref,
                pin_number,
            } => {
                assert_eq!(component_ref, "R1");
                assert_eq!(pin_number, "1");
            }
            _ => panic!("Expected PinNotFound error"),
        }
    }

    #[test]
    fn test_positions_approximately_equal() {
        let pos1 = Position::new(1.0, 2.0);
        let pos2 = Position::new(1.005, 2.005);
        let pos3 = Position::new(1.1, 2.1);

        assert!(positions_approximately_equal(&pos1, &pos2, 0.01));
        assert!(!positions_approximately_equal(&pos1, &pos3, 0.01));
        assert!(positions_approximately_equal(&pos1, &pos3, 0.2));
    }

    #[test]
    fn test_bounding_box_calculation() {
        let positions = vec![
            Position::new(1.0, 2.0),
            Position::new(5.0, 1.0),
            Position::new(3.0, 4.0),
            Position::new(0.0, 3.0),
        ];

        let bbox = calculate_bounding_box(positions.into_iter()).unwrap();

        assert_relative_eq!(bbox.0.x, 0.0); // min_x
        assert_relative_eq!(bbox.0.y, 1.0); // min_y
        assert_relative_eq!(bbox.1.x, 5.0); // max_x
        assert_relative_eq!(bbox.1.y, 4.0); // max_y

        // Test empty iterator
        let empty_bbox = calculate_bounding_box(std::iter::empty());
        assert!(empty_bbox.is_none());
    }

    #[test]
    fn test_angle_normalization() {
        assert_relative_eq!(normalize_angle(45.0), 45.0);
        assert_relative_eq!(normalize_angle(405.0), 45.0);
        assert_relative_eq!(normalize_angle(-45.0), 315.0);
        assert_relative_eq!(normalize_angle(-405.0), 315.0);
        assert_relative_eq!(normalize_angle(0.0), 0.0);
        assert_relative_eq!(normalize_angle(360.0), 0.0);
    }

    #[test]
    fn test_angle_between_positions() {
        let center = Position::new(0.0, 0.0);
        let right = Position::new(1.0, 0.0);
        let up = Position::new(0.0, 1.0);
        let left = Position::new(-1.0, 0.0);
        let down = Position::new(0.0, -1.0);

        assert_relative_eq!(angle_between_positions(&center, &right), 0.0);
        assert_relative_eq!(angle_between_positions(&center, &up), 90.0);
        assert_relative_eq!(angle_between_positions(&center, &left), 180.0);
        assert_relative_eq!(angle_between_positions(&center, &down), -90.0);
    }

    #[test]
    fn test_rotation_matrix() {
        let (a, b, c, d) = rotation_matrix(0.0);
        assert_relative_eq!(a, 1.0);
        assert_relative_eq!(b, 0.0);
        assert_relative_eq!(c, 0.0);
        assert_relative_eq!(d, 1.0);

        let (a, b, c, d) = rotation_matrix(90.0);
        assert_relative_eq!(a, 0.0, epsilon = TOLERANCE);
        assert_relative_eq!(b, -1.0, epsilon = TOLERANCE);
        assert_relative_eq!(c, 1.0, epsilon = TOLERANCE);
        assert_relative_eq!(d, 0.0, epsilon = TOLERANCE);
    }

    #[test]
    fn test_calculation_config() {
        let config = CalculationConfig::default();
        assert_relative_eq!(config.position_tolerance, 0.01);
        assert_relative_eq!(config.default_pin_offset, 1.905);
        assert!(!config.use_reference_positions);
        assert!(config.reference_positions.is_empty());

        let ref_config = PinCalculator::create_reference_design_config();
        assert!(ref_config.use_reference_positions);
        assert_eq!(ref_config.reference_positions.len(), 6); // 3 components × 2 pins
    }

    #[test]
    fn test_net_creation() {
        let nets = PinCalculator::create_reference_design_nets();
        assert_eq!(nets.len(), 3);

        let vcc_net = &nets[0];
        assert_eq!(vcc_net.name, "VCC");
        assert_eq!(vcc_net.pins.len(), 1);
        assert_eq!(vcc_net.pins[0].component_ref, "R1");
        assert_eq!(vcc_net.pins[0].pin_number, "2");

        let out_net = &nets[1];
        assert_eq!(out_net.name, "OUT");
        assert_eq!(out_net.pins.len(), 3);

        let gnd_net = &nets[2];
        assert_eq!(gnd_net.name, "GND");
        assert_eq!(gnd_net.pins.len(), 2);
    }

    #[test]
    fn test_performance_characteristics() {
        let components = PinCalculator::create_reference_design_components();
        let mut calculator = PinCalculator::new();

        for component in components {
            calculator.add_component(component);
        }

        // Measure performance of pin position calculations
        let start = std::time::Instant::now();
        for _ in 0..1000 {
            let _ = calculator.calculate_all_pin_positions();
        }
        let duration = start.elapsed();

        // Should be much faster than 1ms per calculation (target: <100μs)
        assert!(
            duration.as_micros() < 100_000,
            "Performance regression: 1000 calculations took {:?}",
            duration
        );

        // Test individual pin calculation performance
        let start = std::time::Instant::now();
        for _ in 0..10000 {
            let _ = calculator.calculate_pin_position("R1", "1").unwrap();
        }
        let duration = start.elapsed();

        // Should be very fast for individual calculations (target: <10μs per call)
        assert!(
            duration.as_micros() < 100_000,
            "Performance regression: 10000 individual calculations took {:?}",
            duration
        );
    }

    #[test]
    fn test_complex_rotation_scenarios() {
        let component_pos = Position::new(50.0, 75.0);
        let local_pin_pos = Position::new(2.54, 1.27); // Standard grid positions

        // Test various rotation angles
        let test_angles = vec![
            0.0, 30.0, 45.0, 60.0, 90.0, 120.0, 135.0, 150.0, 180.0, 270.0,
        ];

        for angle in test_angles {
            let result = transform_pin_position(component_pos, local_pin_pos, angle);

            // Verify the result is at the correct distance from component center
            let distance = component_pos.distance_to(&result);
            let expected_distance = local_pin_pos.distance_to(&Position::new(0.0, 0.0));
            assert_relative_eq!(distance, expected_distance, epsilon = TOLERANCE);

            // Verify inverse transformation works
            let recovered = inverse_transform_pin_position(component_pos, result, angle);
            assert_relative_eq!(recovered.x, local_pin_pos.x, epsilon = TOLERANCE);
            assert_relative_eq!(recovered.y, local_pin_pos.y, epsilon = TOLERANCE);
        }
    }

    #[test]
    fn test_edge_cases() {
        // Test zero position
        let zero_pos = Position::new(0.0, 0.0);
        let result = transform_pin_position(zero_pos, zero_pos, 45.0);
        assert_relative_eq!(result.x, 0.0);
        assert_relative_eq!(result.y, 0.0);

        // Test very small positions
        let tiny_pos = Position::new(1e-10, 1e-10);
        let result = transform_pin_position(tiny_pos, tiny_pos, 90.0);
        assert!(result.x.abs() < 1e-9);
        assert!(result.y.abs() < 1e-9);

        // Test large positions
        let large_pos = Position::new(1e6, 1e6);
        let result = transform_pin_position(large_pos, Position::new(1.0, 0.0), 0.0);
        assert_relative_eq!(result.x, 1e6 + 1.0);
        assert_relative_eq!(result.y, 1e6);
    }
}
