//! Coordinate transformation functions for pin position calculations

use crate::types::{Position, Component, PinPositionResult};

/// Transform a pin's local position to global coordinates
/// 
/// This function applies rotation and translation to convert a pin's local position
/// (relative to component center) to global schematic coordinates.
/// 
/// # Arguments
/// * `component_pos` - The global position of the component center
/// * `local_pin_pos` - The pin's position relative to component center
/// * `rotation` - Component rotation in degrees (clockwise positive)
/// 
/// # Returns
/// The pin's global position after transformation
pub fn transform_pin_position(
    component_pos: Position,
    local_pin_pos: Position,
    rotation: f64,
) -> Position {
    // Convert rotation from degrees to radians
    let rotation_rad = rotation.to_radians();
    let cos_r = rotation_rad.cos();
    let sin_r = rotation_rad.sin();
    
    // Apply rotation matrix transformation
    // [x'] = [cos(θ) -sin(θ)] [x]
    // [y']   [sin(θ)  cos(θ)] [y]
    let rotated_x = local_pin_pos.x * cos_r - local_pin_pos.y * sin_r;
    let rotated_y = local_pin_pos.x * sin_r + local_pin_pos.y * cos_r;
    
    // Translate to global coordinates
    Position {
        x: component_pos.x + rotated_x,
        y: component_pos.y + rotated_y,
    }
}

/// Transform multiple pin positions for a component
/// 
/// # Arguments
/// * `component` - The component containing pins to transform
/// 
/// # Returns
/// Vector of pin position results with global coordinates
pub fn transform_component_pins(component: &Component) -> Vec<PinPositionResult> {
    component
        .pins
        .iter()
        .map(|pin| {
            let global_position = transform_pin_position(
                component.position,
                pin.local_position,
                component.rotation,
            );
            
            PinPositionResult {
                component_ref: component.reference.clone(),
                pin_number: pin.number.clone(),
                global_position,
                local_position: pin.local_position,
                rotation_applied: component.rotation,
            }
        })
        .collect()
}

/// Calculate the inverse transformation (global to local coordinates)
/// 
/// This is useful for determining what local pin position would result
/// in a desired global position.
/// 
/// # Arguments
/// * `component_pos` - The global position of the component center
/// * `global_pin_pos` - The desired global pin position
/// * `rotation` - Component rotation in degrees
/// 
/// # Returns
/// The local pin position that would result in the global position
pub fn inverse_transform_pin_position(
    component_pos: Position,
    global_pin_pos: Position,
    rotation: f64,
) -> Position {
    // First translate to component-relative coordinates
    let relative_pos = global_pin_pos.subtract(&component_pos);
    
    // Then apply inverse rotation
    let rotation_rad = (-rotation).to_radians(); // Negative for inverse
    let cos_r = rotation_rad.cos();
    let sin_r = rotation_rad.sin();
    
    Position {
        x: relative_pos.x * cos_r - relative_pos.y * sin_r,
        y: relative_pos.x * sin_r + relative_pos.y * cos_r,
    }
}

/// Apply a series of transformations to a position
/// 
/// This allows for complex transformation chains, useful for hierarchical
/// coordinate systems or multiple reference frames.
/// 
/// # Arguments
/// * `initial_pos` - Starting position
/// * `transformations` - Vector of (translation, rotation) pairs to apply
/// 
/// # Returns
/// Final transformed position
pub fn apply_transformation_chain(
    initial_pos: Position,
    transformations: &[(Position, f64)],
) -> Position {
    transformations.iter().fold(initial_pos, |pos, (translation, rotation)| {
        let rotated = transform_pin_position(Position::new(0.0, 0.0), pos, *rotation);
        rotated.add(translation)
    })
}

/// Calculate the transformation matrix for a given rotation
/// 
/// Returns the 2x2 rotation matrix as a tuple of (a, b, c, d) where:
/// [a b]
/// [c d]
/// 
/// # Arguments
/// * `rotation_degrees` - Rotation angle in degrees
/// 
/// # Returns
/// Tuple representing the 2x2 rotation matrix
pub fn rotation_matrix(rotation_degrees: f64) -> (f64, f64, f64, f64) {
    let rad = rotation_degrees.to_radians();
    let cos_r = rad.cos();
    let sin_r = rad.sin();
    
    (cos_r, -sin_r, sin_r, cos_r)
}

/// Check if two positions are approximately equal within tolerance
/// 
/// # Arguments
/// * `pos1` - First position
/// * `pos2` - Second position
/// * `tolerance` - Maximum allowed difference in each dimension
/// 
/// # Returns
/// True if positions are within tolerance
pub fn positions_approximately_equal(pos1: &Position, pos2: &Position, tolerance: f64) -> bool {
    (pos1.x - pos2.x).abs() < tolerance && (pos1.y - pos2.y).abs() < tolerance
}

/// Calculate the bounding box of a set of positions
/// 
/// # Arguments
/// * `positions` - Iterator of positions
/// 
/// # Returns
/// Option containing (min_pos, max_pos) if positions is not empty
pub fn calculate_bounding_box<I>(positions: I) -> Option<(Position, Position)>
where
    I: Iterator<Item = Position>,
{
    let positions: Vec<Position> = positions.collect();
    if positions.is_empty() {
        return None;
    }
    
    let mut min_x = positions[0].x;
    let mut max_x = positions[0].x;
    let mut min_y = positions[0].y;
    let mut max_y = positions[0].y;
    
    for pos in positions.iter().skip(1) {
        min_x = min_x.min(pos.x);
        max_x = max_x.max(pos.x);
        min_y = min_y.min(pos.y);
        max_y = max_y.max(pos.y);
    }
    
    Some((Position::new(min_x, min_y), Position::new(max_x, max_y)))
}

/// Normalize an angle to the range [0, 360) degrees
/// 
/// # Arguments
/// * `angle_degrees` - Input angle in degrees
/// 
/// # Returns
/// Normalized angle in the range [0, 360)
pub fn normalize_angle(angle_degrees: f64) -> f64 {
    let mut normalized = angle_degrees % 360.0;
    if normalized < 0.0 {
        normalized += 360.0;
    }
    normalized
}

/// Calculate the angle between two positions
/// 
/// # Arguments
/// * `from` - Starting position
/// * `to` - Ending position
/// 
/// # Returns
/// Angle in degrees from `from` to `to`
pub fn angle_between_positions(from: &Position, to: &Position) -> f64 {
    let dx = to.x - from.x;
    let dy = to.y - from.y;
    dy.atan2(dx).to_degrees()
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;
    use crate::types::{Pin, PinType, PinOrientation};

    #[test]
    fn test_basic_transformation() {
        let component_pos = Position::new(100.0, 50.0);
        let local_pin_pos = Position::new(2.0, 0.0);
        let rotation = 0.0;
        
        let result = transform_pin_position(component_pos, local_pin_pos, rotation);
        
        assert_relative_eq!(result.x, 102.0);
        assert_relative_eq!(result.y, 50.0);
    }

    #[test]
    fn test_90_degree_rotation() {
        let component_pos = Position::new(0.0, 0.0);
        let local_pin_pos = Position::new(1.0, 0.0);
        let rotation = 90.0;
        
        let result = transform_pin_position(component_pos, local_pin_pos, rotation);
        
        assert_relative_eq!(result.x, 0.0, epsilon = 1e-10);
        assert_relative_eq!(result.y, 1.0, epsilon = 1e-10);
    }

    #[test]
    fn test_180_degree_rotation() {
        let component_pos = Position::new(0.0, 0.0);
        let local_pin_pos = Position::new(1.0, 0.0);
        let rotation = 180.0;
        
        let result = transform_pin_position(component_pos, local_pin_pos, rotation);
        
        assert_relative_eq!(result.x, -1.0, epsilon = 1e-10);
        assert_relative_eq!(result.y, 0.0, epsilon = 1e-10);
    }

    #[test]
    fn test_inverse_transformation() {
        let component_pos = Position::new(10.0, 20.0);
        let local_pin_pos = Position::new(3.0, 4.0);
        let rotation = 45.0;
        
        // Forward transformation
        let global_pos = transform_pin_position(component_pos, local_pin_pos, rotation);
        
        // Inverse transformation
        let recovered_local = inverse_transform_pin_position(component_pos, global_pos, rotation);
        
        assert_relative_eq!(recovered_local.x, local_pin_pos.x, epsilon = 1e-10);
        assert_relative_eq!(recovered_local.y, local_pin_pos.y, epsilon = 1e-10);
    }

    #[test]
    fn test_component_pin_transformation() {
        let mut component = Component::new("R1".to_string(), Position::new(100.0, 50.0), 0.0);
        
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
        assert_relative_eq!(results[0].global_position.x, 98.095);
        assert_relative_eq!(results[0].global_position.y, 50.0);
        assert_relative_eq!(results[1].global_position.x, 101.905);
        assert_relative_eq!(results[1].global_position.y, 50.0);
    }

    #[test]
    fn test_rotation_matrix() {
        let (a, b, c, d) = rotation_matrix(90.0);
        
        assert_relative_eq!(a, 0.0, epsilon = 1e-10);
        assert_relative_eq!(b, -1.0, epsilon = 1e-10);
        assert_relative_eq!(c, 1.0, epsilon = 1e-10);
        assert_relative_eq!(d, 0.0, epsilon = 1e-10);
    }

    #[test]
    fn test_positions_approximately_equal() {
        let pos1 = Position::new(1.0, 2.0);
        let pos2 = Position::new(1.001, 2.001);
        let pos3 = Position::new(1.1, 2.1);
        
        assert!(positions_approximately_equal(&pos1, &pos2, 0.01));
        assert!(!positions_approximately_equal(&pos1, &pos3, 0.01));
    }

    #[test]
    fn test_bounding_box() {
        let positions = vec![
            Position::new(1.0, 2.0),
            Position::new(5.0, 1.0),
            Position::new(3.0, 4.0),
        ];
        
        let bbox = calculate_bounding_box(positions.into_iter()).unwrap();
        
        assert_relative_eq!(bbox.0.x, 1.0);
        assert_relative_eq!(bbox.0.y, 1.0);
        assert_relative_eq!(bbox.1.x, 5.0);
        assert_relative_eq!(bbox.1.y, 4.0);
    }

    #[test]
    fn test_normalize_angle() {
        assert_relative_eq!(normalize_angle(45.0), 45.0);
        assert_relative_eq!(normalize_angle(405.0), 45.0);
        assert_relative_eq!(normalize_angle(-45.0), 315.0);
        assert_relative_eq!(normalize_angle(-405.0), 315.0);
    }

    #[test]
    fn test_angle_between_positions() {
        let pos1 = Position::new(0.0, 0.0);
        let pos2 = Position::new(1.0, 0.0);
        let pos3 = Position::new(0.0, 1.0);
        
        assert_relative_eq!(angle_between_positions(&pos1, &pos2), 0.0);
        assert_relative_eq!(angle_between_positions(&pos1, &pos3), 90.0);
    }

    #[test]
    fn test_transformation_chain() {
        let initial = Position::new(1.0, 0.0);
        let transformations = vec![
            (Position::new(10.0, 20.0), 90.0),  // Rotate 90° then translate
            (Position::new(5.0, 5.0), 0.0),     // Just translate
        ];
        
        let result = apply_transformation_chain(initial, &transformations);
        
        // After 90° rotation: (1,0) -> (0,1)
        // After first translation: (0,1) -> (10,21)
        // After second translation: (10,21) -> (15,26)
        assert_relative_eq!(result.x, 15.0, epsilon = 1e-10);
        assert_relative_eq!(result.y, 26.0, epsilon = 1e-10);
    }
}