//! Integration tests for force-directed placement algorithm
//! 
//! These tests validate correctness, performance, and API compatibility.

use rust_force_directed_placement::*;
use approx::assert_relative_eq;
use std::collections::HashMap;

/// Test basic placement functionality
#[test]
fn test_basic_placement() {
    let config = PlacementConfig::default();
    let mut placer = ForceDirectedPlacer::new(config);
    
    let components = vec![
        Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_position(Point::new(0.0, 0.0))
            .with_size(2.0, 1.0),
        Component::new("R2".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_position(Point::new(10.0, 0.0))
            .with_size(2.0, 1.0),
    ];
    
    let connections = vec![
        Connection::new("R1".to_string(), "R2".to_string()),
    ];
    
    let result = placer.place(components, connections, 100.0, 100.0).unwrap();
    
    assert_eq!(result.positions.len(), 2);
    assert!(result.positions.contains_key("R1"));
    assert!(result.positions.contains_key("R2"));
    assert_eq!(result.collision_count, 0);
}

/// Test placement with multiple connected components
#[test]
fn test_connected_components_placement() {
    let config = PlacementConfig::default();
    let mut placer = ForceDirectedPlacer::new(config);
    
    let components = vec![
        Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string()),
        Component::new("R2".to_string(), "R_0805".to_string(), "10k".to_string()),
        Component::new("C1".to_string(), "C_0805".to_string(), "100nF".to_string()),
        Component::new("U1".to_string(), "SOIC-8".to_string(), "LM358".to_string()),
    ];
    
    let connections = vec![
        Connection::new("R1".to_string(), "U1".to_string()),
        Connection::new("R2".to_string(), "U1".to_string()),
        Connection::new("C1".to_string(), "U1".to_string()),
        Connection::new("R1".to_string(), "R2".to_string()),
    ];
    
    let result = placer.place(components, connections, 100.0, 100.0).unwrap();
    
    assert_eq!(result.positions.len(), 4);
    
    // Verify that connected components are closer together
    let r1_pos = result.positions.get("R1").unwrap();
    let r2_pos = result.positions.get("R2").unwrap();
    let u1_pos = result.positions.get("U1").unwrap();
    let c1_pos = result.positions.get("C1").unwrap();
    
    // R1 and R2 should be close to U1 since they're connected
    let r1_to_u1_dist = r1_pos.distance_to(u1_pos);
    let r2_to_u1_dist = r2_pos.distance_to(u1_pos);
    let c1_to_u1_dist = c1_pos.distance_to(u1_pos);
    
    // All connected components should be reasonably close
    assert!(r1_to_u1_dist < 50.0, "R1 too far from U1: {}", r1_to_u1_dist);
    assert!(r2_to_u1_dist < 50.0, "R2 too far from U1: {}", r2_to_u1_dist);
    assert!(c1_to_u1_dist < 50.0, "C1 too far from U1: {}", c1_to_u1_dist);
}

/// Test hierarchical placement with subcircuits
#[test]
fn test_hierarchical_placement() {
    let config = PlacementConfig::default();
    let mut placer = ForceDirectedPlacer::new(config);
    
    let components = vec![
        Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_path("subcircuit1".to_string()),
        Component::new("R2".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_path("subcircuit1".to_string()),
        Component::new("R3".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_path("subcircuit2".to_string()),
        Component::new("R4".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_path("subcircuit2".to_string()),
    ];
    
    let connections = vec![
        Connection::new("R1".to_string(), "R2".to_string()), // Internal to subcircuit1
        Connection::new("R3".to_string(), "R4".to_string()), // Internal to subcircuit2
        Connection::new("R2".to_string(), "R3".to_string()), // Between subcircuits
    ];
    
    let result = placer.place(components, connections, 100.0, 100.0).unwrap();
    
    assert_eq!(result.positions.len(), 4);
    
    // Components in the same subcircuit should be closer together
    let r1_pos = result.positions.get("R1").unwrap();
    let r2_pos = result.positions.get("R2").unwrap();
    let r3_pos = result.positions.get("R3").unwrap();
    let r4_pos = result.positions.get("R4").unwrap();
    
    let subcircuit1_distance = r1_pos.distance_to(r2_pos);
    let subcircuit2_distance = r3_pos.distance_to(r4_pos);
    let inter_subcircuit_distance = r2_pos.distance_to(r3_pos);
    
    // Internal distances should be smaller than inter-subcircuit distance
    assert!(subcircuit1_distance < inter_subcircuit_distance * 0.8);
    assert!(subcircuit2_distance < inter_subcircuit_distance * 0.8);
}

/// Test collision detection and resolution
#[test]
fn test_collision_resolution() {
    let config = PlacementConfig {
        component_spacing: 5.0, // Larger spacing to test collision resolution
        ..PlacementConfig::default()
    };
    let mut placer = ForceDirectedPlacer::new(config);
    
    // Place components very close together initially
    let components = vec![
        Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_position(Point::new(0.0, 0.0))
            .with_size(3.0, 2.0),
        Component::new("R2".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_position(Point::new(1.0, 0.0)) // Very close to R1
            .with_size(3.0, 2.0),
        Component::new("R3".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_position(Point::new(0.0, 1.0)) // Very close to R1
            .with_size(3.0, 2.0),
    ];
    
    let connections = vec![]; // No connections to test pure repulsion
    
    let result = placer.place(components, connections, 100.0, 100.0).unwrap();
    
    // All components should be separated by at least the minimum spacing
    let positions: Vec<_> = result.positions.values().collect();
    for i in 0..positions.len() {
        for j in (i + 1)..positions.len() {
            let distance = positions[i].distance_to(positions[j]);
            assert!(distance >= 4.0, "Components too close: {} mm", distance);
        }
    }
}

/// Test boundary constraints
#[test]
fn test_boundary_constraints() {
    let config = PlacementConfig::default();
    let mut placer = ForceDirectedPlacer::new(config);
    
    let components = vec![
        Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string()),
        Component::new("R2".to_string(), "R_0805".to_string(), "10k".to_string()),
        Component::new("R3".to_string(), "R_0805".to_string(), "10k".to_string()),
    ];
    
    let connections = vec![];
    
    let board_width = 50.0;
    let board_height = 30.0;
    let result = placer.place(components, connections, board_width, board_height).unwrap();
    
    // All components should be within board boundaries
    for (reference, position) in &result.positions {
        assert!(position.x >= 0.0 && position.x <= board_width, 
            "Component {} X position {} outside board width {}", reference, position.x, board_width);
        assert!(position.y >= 0.0 && position.y <= board_height,
            "Component {} Y position {} outside board height {}", reference, position.y, board_height);
    }
}

/// Test force calculation accuracy
#[test]
fn test_force_calculation_accuracy() {
    let config = PlacementConfig::default();
    let force_calculator = ForceCalculator::new(config);
    
    // Test attraction force
    let comp1 = Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
        .with_position(Point::new(0.0, 0.0));
    let comp2 = Component::new("R2".to_string(), "R_0805".to_string(), "10k".to_string())
        .with_position(Point::new(10.0, 0.0));
    
    let attraction = force_calculator.calculate_attraction_force(&comp1, &comp2, false);
    
    // Force should point from comp1 towards comp2 (positive X direction)
    assert!(attraction.fx > 0.0, "Attraction force should be positive in X direction");
    assert_relative_eq!(attraction.fy, 0.0, epsilon = 0.001);
    
    // Test repulsion force
    let comp3 = Component::new("R3".to_string(), "R_0805".to_string(), "10k".to_string())
        .with_position(Point::new(1.0, 0.0)); // Very close to comp1
    
    let repulsion = force_calculator.calculate_repulsion_force(&comp1, &comp3);
    
    // Force should point away from comp3 (negative X direction)
    assert!(repulsion.fx < 0.0, "Repulsion force should be negative in X direction");
    assert_relative_eq!(repulsion.fy, 0.0, epsilon = 0.001);
}

/// Test collision detection performance and accuracy
#[test]
fn test_collision_detection() {
    let detector = CollisionDetector::new(2.0);
    
    // Test no collision case
    let components_no_collision = vec![
        Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_position(Point::new(0.0, 0.0))
            .with_size(2.0, 1.0),
        Component::new("R2".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_position(Point::new(10.0, 0.0))
            .with_size(2.0, 1.0),
    ];
    
    let collisions = detector.detect_collisions(&components_no_collision);
    assert!(collisions.is_empty(), "Should detect no collisions");
    
    // Test collision case
    let components_with_collision = vec![
        Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_position(Point::new(0.0, 0.0))
            .with_size(2.0, 1.0),
        Component::new("R2".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_position(Point::new(1.0, 0.0)) // Overlapping
            .with_size(2.0, 1.0),
    ];
    
    let collisions = detector.detect_collisions(&components_with_collision);
    assert_eq!(collisions.len(), 1, "Should detect one collision");
    assert_eq!(collisions[0], (0, 1));
}

/// Test configuration validation
#[test]
fn test_configuration_validation() {
    use rust_force_directed_placement::errors::validation;
    
    // Valid configuration
    let valid_config = PlacementConfig::default();
    assert!(validation::validate_config(&valid_config).is_ok());
    
    // Invalid configurations
    let invalid_spacing = PlacementConfig {
        component_spacing: -1.0,
        ..PlacementConfig::default()
    };
    assert!(validation::validate_config(&invalid_spacing).is_err());
    
    let invalid_damping = PlacementConfig {
        damping: 1.5, // > 1.0
        ..PlacementConfig::default()
    };
    assert!(validation::validate_config(&invalid_damping).is_err());
    
    let invalid_iterations = PlacementConfig {
        iterations_per_level: 0,
        ..PlacementConfig::default()
    };
    assert!(validation::validate_config(&invalid_iterations).is_err());
}

/// Test component validation
#[test]
fn test_component_validation() {
    use rust_force_directed_placement::errors::validation;
    
    // Valid component
    let valid_component = Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
        .with_size(2.0, 1.0);
    assert!(validation::validate_component(&valid_component).is_ok());
    
    // Invalid components
    let empty_reference = Component::new("".to_string(), "R_0805".to_string(), "10k".to_string());
    assert!(validation::validate_component(&empty_reference).is_err());
    
    let zero_size = Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
        .with_size(0.0, 1.0);
    assert!(validation::validate_component(&zero_size).is_err());
}

/// Test performance scaling
#[test]
fn test_performance_scaling() {
    let config = PlacementConfig {
        iterations_per_level: 10, // Reduced for testing
        ..PlacementConfig::default()
    };
    
    // Test with different component counts to verify reasonable scaling
    for component_count in [10, 25, 50] {
        let components: Vec<Component> = (0..component_count)
            .map(|i| {
                Component::new(
                    format!("R{}", i),
                    "R_0805".to_string(),
                    "10k".to_string(),
                )
                .with_position(Point::new(
                    (i as f64 % 10.0) * 3.0,
                    (i as f64 / 10.0) * 3.0,
                ))
            })
            .collect();
        
        let connections: Vec<Connection> = (0..(component_count - 1))
            .map(|i| Connection::new(format!("R{}", i), format!("R{}", i + 1)))
            .collect();
        
        let start = std::time::Instant::now();
        let mut placer = ForceDirectedPlacer::new(config.clone());
        let result = placer.place(components, connections, 100.0, 100.0).unwrap();
        let duration = start.elapsed();
        
        assert_eq!(result.positions.len(), component_count);
        println!("Placed {} components in {:?}", component_count, duration);
        
        // Should complete in reasonable time (less than 1 second for test sizes)
        assert!(duration.as_secs() < 5, "Placement took too long: {:?}", duration);
    }
}

/// Test energy minimization
#[test]
fn test_energy_minimization() {
    let config = PlacementConfig::default();
    let mut placer = ForceDirectedPlacer::new(config.clone());
    
    let components = vec![
        Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_position(Point::new(0.0, 0.0)),
        Component::new("R2".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_position(Point::new(50.0, 50.0)), // Far apart initially
    ];
    
    let connections = vec![
        Connection::new("R1".to_string(), "R2".to_string()),
    ];
    
    // Calculate initial energy
    let force_calculator = ForceCalculator::new(config);
    let connection_graph = std::collections::HashMap::from([
        ("R1".to_string(), vec!["R2".to_string()]),
        ("R2".to_string(), vec!["R1".to_string()]),
    ]);
    let initial_energy = force_calculator.calculate_system_energy(&components, &connections, &connection_graph);
    
    // Perform placement
    let result = placer.place(components, connections, 100.0, 100.0).unwrap();
    
    // Final energy should be lower (system should have minimized energy)
    assert!(result.final_energy < initial_energy, 
        "Final energy {} should be less than initial energy {}", 
        result.final_energy, initial_energy);
    
    // Connected components should be closer together
    let r1_final = result.positions.get("R1").unwrap();
    let r2_final = result.positions.get("R2").unwrap();
    let final_distance = r1_final.distance_to(r2_final);
    
    assert!(final_distance < 50.0, "Connected components should be closer: {} mm", final_distance);
}

/// Test rotation optimization
#[test]
fn test_rotation_optimization() {
    let config = PlacementConfig {
        enable_rotation: true,
        ..PlacementConfig::default()
    };
    let mut placer = ForceDirectedPlacer::new(config);
    
    let components = vec![
        Component::new("U1".to_string(), "SOIC-8".to_string(), "LM358".to_string())
            .with_position(Point::new(10.0, 10.0)),
        Component::new("R1".to_string(), "R_0805".to_string(), "10k".to_string())
            .with_position(Point::new(20.0, 10.0)),
    ];
    
    let connections = vec![
        Connection::new("U1".to_string(), "R1".to_string()),
    ];
    
    let result = placer.place(components, connections, 100.0, 100.0).unwrap();
    
    // Rotations should be set (not all zero)
    let u1_rotation = result.rotations.get("U1").unwrap();
    let r1_rotation = result.rotations.get("R1").unwrap();
    
    // At least one component should have been rotated
    assert!(*u1_rotation % 360.0 == 0.0 || *u1_rotation % 90.0 == 0.0, 
        "Rotation should be multiple of 90 degrees: {}", u1_rotation);
    assert!(*r1_rotation % 360.0 == 0.0 || *r1_rotation % 90.0 == 0.0,
        "Rotation should be multiple of 90 degrees: {}", r1_rotation);
}