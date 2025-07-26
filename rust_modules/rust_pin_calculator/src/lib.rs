//! Rust Pin Calculator - High-performance pin position calculator and coordinate transformer
//! 
//! This library provides fast and accurate pin position calculations for KiCad schematic generation,
//! with Python bindings for seamless integration with existing Python workflows.

pub mod types;
pub mod coordinate_transform;
pub mod pin_calculator;

#[cfg(test)]
pub mod tests;

// Re-export main types and functions for easier access
pub use types::{
    Position, Component, Pin, Net, PinReference, HierarchicalLabelPosition,
    PinPositionResult, CalculationConfig, PinCalculationError, Result,
    PinType, PinOrientation, LabelOrientation, LabelShape,
};
pub use coordinate_transform::{
    transform_pin_position, transform_component_pins, inverse_transform_pin_position,
    positions_approximately_equal, calculate_bounding_box, normalize_angle,
};
pub use pin_calculator::PinCalculator;

#[cfg(feature = "python-bindings")]
use pyo3::prelude::*;

#[cfg(feature = "python-bindings")]

/// Python wrapper for Position
#[cfg(feature = "python-bindings")]
#[pyclass]
#[derive(Clone)]
pub struct PyPosition {
    #[pyo3(get, set)]
    pub x: f64,
    #[pyo3(get, set)]
    pub y: f64,
}

#[cfg(feature = "python-bindings")]
#[pymethods]
impl PyPosition {
    #[new]
    fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }

    fn distance_to(&self, other: &PyPosition) -> f64 {
        let pos1 = Position::new(self.x, self.y);
        let pos2 = Position::new(other.x, other.y);
        pos1.distance_to(&pos2)
    }

    fn __repr__(&self) -> String {
        format!("Position(x={}, y={})", self.x, self.y)
    }
}

#[cfg(feature = "python-bindings")]
impl From<Position> for PyPosition {
    fn from(pos: Position) -> Self {
        Self { x: pos.x, y: pos.y }
    }
}

#[cfg(feature = "python-bindings")]
impl From<PyPosition> for Position {
    fn from(py_pos: PyPosition) -> Self {
        Position::new(py_pos.x, py_pos.y)
    }
}

/// Python wrapper for PinCalculator
#[cfg(feature = "python-bindings")]
#[pyclass]
pub struct PyPinCalculator {
    calculator: PinCalculator,
}

#[cfg(feature = "python-bindings")]
#[pymethods]
impl PyPinCalculator {
    #[new]
    fn new() -> Self {
        Self {
            calculator: PinCalculator::new(),
        }
    }

    #[staticmethod]
    fn with_reference_config() -> Self {
        let config = PinCalculator::create_reference_design_config();
        Self {
            calculator: PinCalculator::with_config(config),
        }
    }

    fn add_component_simple(
        &mut self,
        reference: String,
        x: f64,
        y: f64,
        rotation: f64,
        component_type: String,
        value: Option<String>,
    ) {
        let mut component = Component::new(reference, Position::new(x, y), rotation);
        component.component_type = component_type;
        component.value = value;
        self.calculator.add_component(component);
    }

    fn add_pin_to_component(
        &mut self,
        component_ref: String,
        pin_number: String,
        local_x: f64,
        local_y: f64,
        pin_type: String,
        orientation: String,
    ) -> PyResult<()> {
        use types::{PinType, PinOrientation};

        let pin_type_enum = match pin_type.as_str() {
            "input" => PinType::Input,
            "output" => PinType::Output,
            "bidirectional" => PinType::Bidirectional,
            "tristate" => PinType::TriState,
            "passive" => PinType::Passive,
            "power_in" => PinType::PowerIn,
            "power_out" => PinType::PowerOut,
            "open_collector" => PinType::OpenCollector,
            "open_emitter" => PinType::OpenEmitter,
            "not_connected" => PinType::NotConnected,
            _ => PinType::Unspecified,
        };

        let orientation_enum = match orientation.as_str() {
            "right" => PinOrientation::Right,
            "left" => PinOrientation::Left,
            "up" => PinOrientation::Up,
            "down" => PinOrientation::Down,
            _ => PinOrientation::Right,
        };

        let pin = Pin {
            number: pin_number,
            name: None,
            local_position: Position::new(local_x, local_y),
            pin_type: pin_type_enum,
            orientation: orientation_enum,
        };

        // Find the component and add the pin
        if let Some(component) = self.calculator.get_component_mut(&component_ref) {
            component.add_pin(pin);
            Ok(())
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("Component {} not found", component_ref)
            ))
        }
    }

    fn calculate_pin_position(&self, component_ref: String, pin_number: String) -> PyResult<(f64, f64)> {
        match self.calculator.calculate_pin_position(&component_ref, &pin_number) {
            Ok(result) => Ok((result.global_position.x, result.global_position.y)),
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())),
        }
    }

    fn calculate_all_pin_positions(&self) -> Vec<(String, String, f64, f64)> {
        self.calculator
            .calculate_all_pin_positions()
            .into_iter()
            .map(|result| {
                (
                    result.component_ref,
                    result.pin_number,
                    result.global_position.x,
                    result.global_position.y,
                )
            })
            .collect()
    }

    fn validate_against_reference(&self, component_ref: String, pin_number: String) -> PyResult<bool> {
        match self.calculator.validate_against_reference(&component_ref, &pin_number) {
            Ok(valid) => Ok(valid),
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())),
        }
    }

    #[staticmethod]
    fn create_reference_design_test() -> PyResult<Vec<(String, String, f64, f64)>> {
        let components = PinCalculator::create_reference_design_components();
        let config = PinCalculator::create_reference_design_config();
        let mut calculator = PinCalculator::with_config(config);

        for component in components {
            calculator.add_component(component);
        }

        let results = calculator.calculate_all_pin_positions();
        Ok(results
            .into_iter()
            .map(|result| {
                (
                    result.component_ref,
                    result.pin_number,
                    result.global_position.x,
                    result.global_position.y,
                )
            })
            .collect())
    }
}

/// Python function to calculate pin positions from component data
#[cfg(feature = "python-bindings")]
#[pyfunction]
pub fn calculate_pin_positions(
    component_positions: Vec<(String, f64, f64, f64)>, // (ref, x, y, rotation)
    pin_definitions: Vec<(String, String, f64, f64)>,  // (component_ref, pin_num, local_x, local_y)
) -> PyResult<Vec<(String, String, f64, f64)>> {
    let mut calculator = PinCalculator::new();

    // Create components from position data
    for (reference, x, y, rotation) in component_positions {
        let component = Component::new(reference, Position::new(x, y), rotation);
        calculator.add_component(component);
    }

    // Add pins to components
    for (component_ref, pin_number, local_x, local_y) in pin_definitions {
        let pin = Pin {
            number: pin_number,
            name: None,
            local_position: Position::new(local_x, local_y),
            pin_type: PinType::Passive,
            orientation: PinOrientation::Right,
        };

        if let Some(component) = calculator.get_component_mut(&component_ref) {
            component.add_pin(pin);
        }
    }

    // Calculate all pin positions
    let results = calculator.calculate_all_pin_positions();
    Ok(results
        .into_iter()
        .map(|result| {
            (
                result.component_ref,
                result.pin_number,
                result.global_position.x,
                result.global_position.y,
            )
        })
        .collect())
}

/// Python function to transform a single pin position
#[cfg(feature = "python-bindings")]
#[pyfunction]
pub fn transform_pin_position_py(
    component_x: f64,
    component_y: f64,
    local_pin_x: f64,
    local_pin_y: f64,
    rotation: f64,
) -> (f64, f64) {
    let component_pos = Position::new(component_x, component_y);
    let local_pin_pos = Position::new(local_pin_x, local_pin_y);
    let result = transform_pin_position(component_pos, local_pin_pos, rotation);
    (result.x, result.y)
}

/// Python function to calculate hierarchical label positions
#[cfg(feature = "python-bindings")]
#[pyfunction]
pub fn calculate_hierarchical_labels(
    component_positions: Vec<(String, f64, f64, f64)>, // (ref, x, y, rotation)
    pin_definitions: Vec<(String, String, f64, f64)>,  // (component_ref, pin_num, local_x, local_y)
    nets: Vec<(String, Vec<(String, String)>)>,        // (net_name, [(component_ref, pin_num)])
) -> PyResult<Vec<(String, f64, f64, String)>> {
    let mut calculator = PinCalculator::new();

    // Create components
    for (reference, x, y, rotation) in component_positions {
        let component = Component::new(reference, Position::new(x, y), rotation);
        calculator.add_component(component);
    }

    // Add pins to components
    for (component_ref, pin_number, local_x, local_y) in pin_definitions {
        let pin = Pin {
            number: pin_number,
            name: None,
            local_position: Position::new(local_x, local_y),
            pin_type: PinType::Passive,
            orientation: PinOrientation::Right,
        };

        if let Some(component) = calculator.get_component_mut(&component_ref) {
            component.add_pin(pin);
        }
    }

    // Create nets
    let nets: Vec<Net> = nets
        .into_iter()
        .map(|(net_name, pin_refs)| Net {
            name: net_name,
            pins: pin_refs
                .into_iter()
                .map(|(component_ref, pin_number)| PinReference::new(component_ref, pin_number))
                .collect(),
        })
        .collect();

    // Calculate hierarchical label positions
    match calculator.calculate_hierarchical_label_positions(&nets) {
        Ok(labels) => Ok(labels
            .into_iter()
            .map(|label| {
                let orientation_str = match label.orientation {
                    LabelOrientation::Right => "right",
                    LabelOrientation::Left => "left",
                    LabelOrientation::Up => "up",
                    LabelOrientation::Down => "down",
                };
                (
                    label.net_name,
                    label.position.x,
                    label.position.y,
                    orientation_str.to_string(),
                )
            })
            .collect()),
        Err(e) => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())),
    }
}

/// Python function to get reference design positions for testing
#[cfg(feature = "python-bindings")]
#[pyfunction]
pub fn get_reference_design_positions() -> Vec<(String, f64, f64)> {
    let config = PinCalculator::create_reference_design_config();
    config
        .reference_positions
        .into_iter()
        .map(|(key, pos)| (key, pos.x, pos.y))
        .collect()
}

/// Python function to estimate pin position for common component types
#[cfg(feature = "python-bindings")]
#[pyfunction]
pub fn estimate_pin_position(
    lib_id: String,
    pin_id: String,
    component_pos: (f64, f64, f64), // (x, y, rotation)
) -> PyResult<(f64, f64, f64)> {
    let (x, y, rotation) = component_pos;
    let component_position = Position::new(x, y);
    
    // Create estimated pin definition based on component type and pin number
    let estimated_pin = match lib_id.as_str() {
        lib if lib.contains("Device:R") => {
            // Resistor: pins at opposite ends
            match pin_id.as_str() {
                "1" => Pin {
                    number: "1".to_string(),
                    name: Some("~".to_string()),
                    local_position: Position::new(0.0, 3.81),  // 150mil above center
                    pin_type: PinType::Passive,
                    orientation: PinOrientation::Down,
                },
                "2" => Pin {
                    number: "2".to_string(),
                    name: Some("~".to_string()),
                    local_position: Position::new(0.0, -3.81),  // 150mil below center
                    pin_type: PinType::Passive,
                    orientation: PinOrientation::Up,
                },
                _ => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    format!("Unknown pin {} for resistor", pin_id)
                )),
            }
        },
        lib if lib.contains("Device:C") => {
            // Capacitor: similar to resistor
            match pin_id.as_str() {
                "1" => Pin {
                    number: "1".to_string(),
                    name: Some("~".to_string()),
                    local_position: Position::new(0.0, 3.81),
                    pin_type: PinType::Passive,
                    orientation: PinOrientation::Down,
                },
                "2" => Pin {
                    number: "2".to_string(),
                    name: Some("~".to_string()),
                    local_position: Position::new(0.0, -3.81),
                    pin_type: PinType::Passive,
                    orientation: PinOrientation::Up,
                },
                _ => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    format!("Unknown pin {} for capacitor", pin_id)
                )),
            }
        },
        _ => {
            // Generic component: place pins on left side
            let pin_num: i32 = pin_id.parse().unwrap_or(1);
            let y_offset = (pin_num - 1) as f64 * -2.54; // 100mil spacing
            
            Pin {
                number: pin_id.clone(),
                name: Some(pin_id.clone()),
                local_position: Position::new(-12.7, y_offset),  // 500mil to the left
                pin_type: PinType::Passive,
                orientation: PinOrientation::Right,
            }
        }
    };
    
    // Calculate world position using coordinate transformation
    let world_pos = transform_pin_position(component_position, estimated_pin.local_position, rotation);
    
    // Return position and orientation (convert orientation enum to degrees)
    let orientation_degrees = match estimated_pin.orientation {
        PinOrientation::Right => 0.0,
        PinOrientation::Up => 90.0,
        PinOrientation::Left => 180.0,
        PinOrientation::Down => 270.0,
    };
    
    Ok((world_pos.x, world_pos.y, orientation_degrees))
}

/// Python module definition
#[cfg(feature = "python-bindings")]
#[pymodule]
fn rust_pin_calculator(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyPosition>()?;
    m.add_class::<PyPinCalculator>()?;
    m.add_function(wrap_pyfunction!(calculate_pin_positions, m)?)?;
    m.add_function(wrap_pyfunction!(transform_pin_position_py, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_hierarchical_labels, m)?)?;
    m.add_function(wrap_pyfunction!(get_reference_design_positions, m)?)?;
    m.add_function(wrap_pyfunction!(estimate_pin_position, m)?)?;
    Ok(())
}

// CLI binary support
#[cfg(not(feature = "python-bindings"))]
pub fn main() {
    println!("Rust Pin Calculator - Command Line Interface");
    
    // Create reference design test
    let components = PinCalculator::create_reference_design_components();
    let config = PinCalculator::create_reference_design_config();
    let mut calculator = PinCalculator::with_config(config);

    for component in components {
        calculator.add_component(component);
    }

    println!("Reference Design Pin Positions:");
    let results = calculator.calculate_all_pin_positions();
    for result in results {
        println!(
            "{}.{}: ({:.2}, {:.2})",
            result.component_ref,
            result.pin_number,
            result.global_position.x,
            result.global_position.y
        );
        
        // Validate against reference
        match calculator.validate_against_reference(&result.component_ref, &result.pin_number) {
            Ok(valid) => println!("  Validation: {}", if valid { "PASS" } else { "FAIL" }),
            Err(e) => println!("  Validation Error: {}", e),
        }
    }

    // Test hierarchical labels
    let nets = PinCalculator::create_reference_design_nets();
    match calculator.calculate_hierarchical_label_positions(&nets) {
        Ok(labels) => {
            println!("\nHierarchical Label Positions:");
            for label in labels {
                println!(
                    "{}: ({:.2}, {:.2}) - {:?}",
                    label.net_name,
                    label.position.x,
                    label.position.y,
                    label.orientation
                );
            }
        }
        Err(e) => println!("Error calculating labels: {}", e),
    }
}
