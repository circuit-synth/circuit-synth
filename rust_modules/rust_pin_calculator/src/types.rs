//! Core data types for pin position calculations and coordinate transformations

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Represents a 2D position with x and y coordinates
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct Position {
    pub x: f64,
    pub y: f64,
}

impl Position {
    /// Create a new position
    pub fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }

    /// Calculate distance to another position
    pub fn distance_to(&self, other: &Position) -> f64 {
        ((self.x - other.x).powi(2) + (self.y - other.y).powi(2)).sqrt()
    }

    /// Add two positions (vector addition)
    pub fn add(&self, other: &Position) -> Position {
        Position {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }

    /// Subtract two positions (vector subtraction)
    pub fn subtract(&self, other: &Position) -> Position {
        Position {
            x: self.x - other.x,
            y: self.y - other.y,
        }
    }

    /// Scale position by a factor
    pub fn scale(&self, factor: f64) -> Position {
        Position {
            x: self.x * factor,
            y: self.y * factor,
        }
    }
}

/// Represents a pin with its local position relative to component center
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Pin {
    pub number: String,
    pub name: Option<String>,
    pub local_position: Position,
    pub pin_type: PinType,
    pub orientation: PinOrientation,
}

/// Pin type enumeration
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum PinType {
    Input,
    Output,
    Bidirectional,
    TriState,
    Passive,
    Unspecified,
    PowerIn,
    PowerOut,
    OpenCollector,
    OpenEmitter,
    NotConnected,
}

/// Pin orientation relative to component
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum PinOrientation {
    Right,   // Pin points to the right
    Left,    // Pin points to the left
    Up,      // Pin points up
    Down,    // Pin points down
}

impl PinOrientation {
    /// Get the angle in radians for this orientation
    pub fn to_radians(&self) -> f64 {
        match self {
            PinOrientation::Right => 0.0,
            PinOrientation::Up => std::f64::consts::PI / 2.0,
            PinOrientation::Left => std::f64::consts::PI,
            PinOrientation::Down => 3.0 * std::f64::consts::PI / 2.0,
        }
    }
}

/// Represents a component with its position, rotation, and pins
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Component {
    pub reference: String,
    pub position: Position,
    pub rotation: f64, // Rotation in degrees
    pub pins: Vec<Pin>,
    pub component_type: String,
    pub value: Option<String>,
    pub footprint: Option<String>,
}

impl Component {
    /// Create a new component
    pub fn new(reference: String, position: Position, rotation: f64) -> Self {
        Self {
            reference,
            position,
            rotation,
            pins: Vec::new(),
            component_type: String::new(),
            value: None,
            footprint: None,
        }
    }

    /// Add a pin to the component
    pub fn add_pin(&mut self, pin: Pin) {
        self.pins.push(pin);
    }

    /// Get a pin by number
    pub fn get_pin(&self, pin_number: &str) -> Option<&Pin> {
        self.pins.iter().find(|pin| pin.number == pin_number)
    }

    /// Get all pin numbers
    pub fn get_pin_numbers(&self) -> Vec<String> {
        self.pins.iter().map(|pin| pin.number.clone()).collect()
    }
}

/// Represents a net connection between pins
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Net {
    pub name: String,
    pub pins: Vec<PinReference>,
}

/// Reference to a specific pin on a component
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PinReference {
    pub component_ref: String,
    pub pin_number: String,
}

impl PinReference {
    pub fn new(component_ref: String, pin_number: String) -> Self {
        Self {
            component_ref,
            pin_number,
        }
    }
}

/// Represents a hierarchical label position for KiCad schematic generation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HierarchicalLabelPosition {
    pub net_name: String,
    pub position: Position,
    pub orientation: LabelOrientation,
    pub shape: LabelShape,
}

/// Label orientation for hierarchical labels
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum LabelOrientation {
    Right,
    Left,
    Up,
    Down,
}

/// Label shape for hierarchical labels
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum LabelShape {
    Input,
    Output,
    Bidirectional,
    TriState,
    Passive,
}

/// Configuration for pin position calculations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CalculationConfig {
    /// Tolerance for position matching (in mm)
    pub position_tolerance: f64,
    /// Default pin offset from component center (in mm)
    pub default_pin_offset: f64,
    /// Whether to use exact reference design positions
    pub use_reference_positions: bool,
    /// Reference design positions for validation
    pub reference_positions: HashMap<String, Position>,
}

impl Default for CalculationConfig {
    fn default() -> Self {
        Self {
            position_tolerance: 0.01, // 0.01mm tolerance
            default_pin_offset: 1.905, // Standard KiCad pin offset
            use_reference_positions: false,
            reference_positions: HashMap::new(),
        }
    }
}

/// Result of pin position calculation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PinPositionResult {
    pub component_ref: String,
    pub pin_number: String,
    pub global_position: Position,
    pub local_position: Position,
    pub rotation_applied: f64,
}

/// Error types for pin calculation operations
#[derive(Debug, thiserror::Error)]
pub enum PinCalculationError {
    #[error("Component not found: {0}")]
    ComponentNotFound(String),
    
    #[error("Pin not found: {component_ref}.{pin_number}")]
    PinNotFound {
        component_ref: String,
        pin_number: String,
    },
    
    #[error("Invalid rotation angle: {0}")]
    InvalidRotation(f64),
    
    #[error("Position calculation failed: {0}")]
    CalculationFailed(String),
    
    #[error("Reference design mismatch: expected {expected:?}, got {actual:?}")]
    ReferenceDesignMismatch {
        expected: Position,
        actual: Position,
    },
}

pub type Result<T> = std::result::Result<T, PinCalculationError>;

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_position_operations() {
        let pos1 = Position::new(1.0, 2.0);
        let pos2 = Position::new(3.0, 4.0);
        
        let sum = pos1.add(&pos2);
        assert_relative_eq!(sum.x, 4.0);
        assert_relative_eq!(sum.y, 6.0);
        
        let diff = pos2.subtract(&pos1);
        assert_relative_eq!(diff.x, 2.0);
        assert_relative_eq!(diff.y, 2.0);
        
        let scaled = pos1.scale(2.0);
        assert_relative_eq!(scaled.x, 2.0);
        assert_relative_eq!(scaled.y, 4.0);
        
        let distance = pos1.distance_to(&pos2);
        assert_relative_eq!(distance, (8.0_f64).sqrt());
    }

    #[test]
    fn test_pin_orientation_angles() {
        assert_relative_eq!(PinOrientation::Right.to_radians(), 0.0);
        assert_relative_eq!(PinOrientation::Up.to_radians(), std::f64::consts::PI / 2.0);
        assert_relative_eq!(PinOrientation::Left.to_radians(), std::f64::consts::PI);
        assert_relative_eq!(PinOrientation::Down.to_radians(), 3.0 * std::f64::consts::PI / 2.0);
    }

    #[test]
    fn test_component_pin_management() {
        let mut component = Component::new("R1".to_string(), Position::new(0.0, 0.0), 0.0);
        
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
}