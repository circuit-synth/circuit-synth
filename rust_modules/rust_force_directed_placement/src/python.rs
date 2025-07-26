//! Python bindings for force-directed placement algorithm
//! 
//! This module provides PyO3 bindings that maintain 100% API compatibility
//! with the existing Python implementation for seamless integration.

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};
use std::collections::HashMap;

use crate::types::{Point, Component, Connection, PlacementConfig, PlacementResult as RustPlacementResult};
use crate::placement::ForceDirectedPlacer;
use crate::errors::PlacementError;

/// Python-compatible Point class
#[pyclass(name = "Point")]
#[derive(Clone, Debug)]
pub struct PyPoint {
    #[pyo3(get, set)]
    pub x: f64,
    #[pyo3(get, set)]
    pub y: f64,
}

#[pymethods]
impl PyPoint {
    #[new]
    fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }

    fn __repr__(&self) -> String {
        format!("Point({}, {})", self.x, self.y)
    }

    fn __str__(&self) -> String {
        format!("({:.2}, {:.2})", self.x, self.y)
    }

    fn distance_to(&self, other: &PyPoint) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        (dx * dx + dy * dy).sqrt()
    }
}

impl From<Point> for PyPoint {
    fn from(point: Point) -> Self {
        Self { x: point.x, y: point.y }
    }
}

impl From<PyPoint> for Point {
    fn from(py_point: PyPoint) -> Self {
        Point::new(py_point.x, py_point.y)
    }
}

/// Python-compatible Component class
#[pyclass(name = "Component")]
#[derive(Clone, Debug)]
pub struct PyComponent {
    #[pyo3(get, set)]
    pub reference: String,
    #[pyo3(get, set)]
    pub position: PyPoint,
    #[pyo3(get, set)]
    pub rotation: f64,
    #[pyo3(get, set)]
    pub footprint: String,
    #[pyo3(get, set)]
    pub value: String,
    #[pyo3(get, set)]
    pub path: String,
    #[pyo3(get, set)]
    pub width: f64,
    #[pyo3(get, set)]
    pub height: f64,
}

#[pymethods]
impl PyComponent {
    #[new]
    fn new(reference: String, footprint: String, value: String) -> Self {
        Self {
            reference,
            position: PyPoint::new(0.0, 0.0),
            rotation: 0.0,
            footprint,
            value,
            path: String::new(),
            width: 2.0,
            height: 2.0,
        }
    }

    fn __repr__(&self) -> String {
        format!("Component('{}', '{}', '{}')", self.reference, self.footprint, self.value)
    }

    fn with_position(&mut self, x: f64, y: f64) -> PyResult<()> {
        self.position = PyPoint::new(x, y);
        Ok(())
    }

    fn with_size(&mut self, width: f64, height: f64) -> PyResult<()> {
        self.width = width;
        self.height = height;
        Ok(())
    }

    fn with_path(&mut self, path: String) -> PyResult<()> {
        self.path = path;
        Ok(())
    }

    fn bounding_box(&self) -> PyResult<(f64, f64, f64, f64)> {
        let half_width = self.width / 2.0;
        let half_height = self.height / 2.0;
        Ok((
            self.position.x - half_width,
            self.position.y - half_height,
            self.width,
            self.height,
        ))
    }
}

impl From<Component> for PyComponent {
    fn from(component: Component) -> Self {
        Self {
            reference: component.reference,
            position: component.position.into(),
            rotation: component.rotation,
            footprint: component.footprint,
            value: component.value,
            path: component.path,
            width: component.width,
            height: component.height,
        }
    }
}

impl From<PyComponent> for Component {
    fn from(py_component: PyComponent) -> Self {
        Component {
            reference: py_component.reference,
            position: py_component.position.into(),
            rotation: py_component.rotation,
            footprint: py_component.footprint,
            value: py_component.value,
            path: py_component.path,
            width: py_component.width,
            height: py_component.height,
        }
    }
}

/// Python-compatible PlacementResult class
#[pyclass(name = "PlacementResult")]
#[derive(Clone, Debug)]
pub struct PyPlacementResult {
    #[pyo3(get)]
    pub positions: HashMap<String, PyPoint>,
    #[pyo3(get)]
    pub rotations: HashMap<String, f64>,
    #[pyo3(get)]
    pub iterations_used: usize,
    #[pyo3(get)]
    pub final_energy: f64,
    #[pyo3(get)]
    pub convergence_achieved: bool,
    #[pyo3(get)]
    pub collision_count: usize,
}

#[pymethods]
impl PyPlacementResult {
    #[new]
    fn new() -> Self {
        Self {
            positions: HashMap::new(),
            rotations: HashMap::new(),
            iterations_used: 0,
            final_energy: 0.0,
            convergence_achieved: false,
            collision_count: 0,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "PlacementResult(components={}, iterations={}, energy={:.2}, converged={})",
            self.positions.len(),
            self.iterations_used,
            self.final_energy,
            self.convergence_achieved
        )
    }

    fn get_position(&self, reference: &str) -> PyResult<Option<PyPoint>> {
        Ok(self.positions.get(reference).cloned())
    }

    fn get_rotation(&self, reference: &str) -> PyResult<Option<f64>> {
        Ok(self.rotations.get(reference).copied())
    }
}

impl From<RustPlacementResult> for PyPlacementResult {
    fn from(result: RustPlacementResult) -> Self {
        let positions = result.positions
            .into_iter()
            .map(|(k, v)| (k, v.into()))
            .collect();

        Self {
            positions,
            rotations: result.rotations,
            iterations_used: result.iterations_used,
            final_energy: result.final_energy,
            convergence_achieved: result.convergence_achieved,
            collision_count: result.collision_count,
        }
    }
}

/// Main Python-compatible ForceDirectedPlacer class
#[pyclass(name = "ForceDirectedPlacer")]
pub struct PyForceDirectedPlacer {
    placer: ForceDirectedPlacer,
}

#[pymethods]
impl PyForceDirectedPlacer {
    #[new]
    #[pyo3(signature = (
        component_spacing = 2.0,
        attraction_strength = 1.5,
        repulsion_strength = 50.0,
        iterations_per_level = 100,
        damping = 0.8,
        initial_temperature = 10.0,
        cooling_rate = 0.95,
        enable_rotation = true,
        internal_force_multiplier = 2.0
    ))]
    fn new(
        component_spacing: f64,
        attraction_strength: f64,
        repulsion_strength: f64,
        iterations_per_level: usize,
        damping: f64,
        initial_temperature: f64,
        cooling_rate: f64,
        enable_rotation: bool,
        internal_force_multiplier: f64,
    ) -> PyResult<Self> {
        let config = PlacementConfig {
            component_spacing,
            attraction_strength,
            repulsion_strength,
            iterations_per_level,
            damping,
            initial_temperature,
            cooling_rate,
            enable_rotation,
            internal_force_multiplier,
            convergence_threshold: 1.0,
            max_move_distance: 5.0,
        };

        // Validate configuration
        crate::errors::validation::validate_config(&config)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

        Ok(Self {
            placer: ForceDirectedPlacer::new(config),
        })
    }

    /// Main placement method - maintains 100% API compatibility
    #[pyo3(signature = (components, connections, board_width = 100.0, board_height = 100.0))]
    fn place(
        &mut self,
        components: Vec<PyComponent>,
        connections: Vec<(String, String)>,
        board_width: f64,
        board_height: f64,
    ) -> PyResult<PyPlacementResult> {
        // Validate inputs
        crate::errors::validation::validate_board_dimensions(board_width, board_height)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

        // Convert Python types to Rust types
        let rust_components: Vec<Component> = components
            .into_iter()
            .map(|c| c.into())
            .collect();

        let rust_connections: Vec<Connection> = connections
            .into_iter()
            .map(|(ref1, ref2)| Connection::new(ref1, ref2))
            .collect();

        // Validate components and connections
        crate::errors::validation::validate_components(&rust_components)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

        crate::errors::validation::validate_connections(&rust_connections, &rust_components)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

        // Perform placement
        let result = self.placer
            .place(rust_components, rust_connections, board_width, board_height)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

        Ok(result.into())
    }

    /// Alternative placement method that accepts Python dictionaries (for compatibility)
    fn place_dict(
        &mut self,
        py: Python,
        components_dict: &PyDict,
        connections_list: &PyList,
        board_width: f64,
        board_height: f64,
    ) -> PyResult<PyObject> {
        // Convert dictionary format to component list
        let mut components = Vec::new();
        for (key, value) in components_dict.iter() {
            let reference: String = key.extract()?;
            let comp_dict: &PyDict = value.extract()?;
            
            let footprint: String = comp_dict.get_item("footprint")?.unwrap().extract()?;
            let value_str: String = comp_dict.get_item("value")?.unwrap_or(py.None().as_ref(py)).extract().unwrap_or_default();
            
            let mut component = PyComponent::new(reference, footprint, value_str);
            
            // Set position if provided
            if let Some(position) = comp_dict.get_item("position")? {
                let pos_tuple: &PyTuple = position.extract()?;
                let x: f64 = pos_tuple.get_item(0)?.extract()?;
                let y: f64 = pos_tuple.get_item(1)?.extract()?;
                component.with_position(x, y)?;
            }
            
            // Set size if provided
            if let Some(size) = comp_dict.get_item("size")? {
                let size_tuple: &PyTuple = size.extract()?;
                let width: f64 = size_tuple.get_item(0)?.extract()?;
                let height: f64 = size_tuple.get_item(1)?.extract()?;
                component.with_size(width, height)?;
            }
            
            // Set path if provided
            if let Some(path) = comp_dict.get_item("path")? {
                let path_str: String = path.extract()?;
                component.with_path(path_str)?;
            }
            
            components.push(component);
        }

        // Convert connections list
        let mut connections = Vec::new();
        for item in connections_list.iter() {
            let conn_tuple: &PyTuple = item.extract()?;
            let ref1: String = conn_tuple.get_item(0)?.extract()?;
            let ref2: String = conn_tuple.get_item(1)?.extract()?;
            connections.push((ref1, ref2));
        }

        // Perform placement
        let result = self.place(components, connections, board_width, board_height)?;

        // Convert result to dictionary format
        let result_dict = PyDict::new(py);
        
        let positions_dict = PyDict::new(py);
        for (reference, position) in &result.positions {
            let pos_tuple = PyTuple::new(py, &[position.x, position.y]);
            positions_dict.set_item(reference, pos_tuple)?;
        }
        result_dict.set_item("positions", positions_dict)?;
        
        let rotations_dict = PyDict::new(py);
        for (reference, rotation) in &result.rotations {
            rotations_dict.set_item(reference, rotation)?;
        }
        result_dict.set_item("rotations", rotations_dict)?;
        
        result_dict.set_item("iterations_used", result.iterations_used)?;
        result_dict.set_item("final_energy", result.final_energy)?;
        result_dict.set_item("convergence_achieved", result.convergence_achieved)?;
        result_dict.set_item("collision_count", result.collision_count)?;

        Ok(result_dict.into())
    }

    /// Get placement statistics
    fn get_stats(&self, py: Python) -> PyResult<PyObject> {
        let stats = PyDict::new(py);
        
        stats.set_item("component_spacing", self.placer.config().component_spacing)?;
        stats.set_item("attraction_strength", self.placer.config().attraction_strength)?;
        stats.set_item("repulsion_strength", self.placer.config().repulsion_strength)?;
        stats.set_item("iterations_per_level", self.placer.config().iterations_per_level)?;
        stats.set_item("damping", self.placer.config().damping)?;
        stats.set_item("enable_rotation", self.placer.config().enable_rotation)?;
        
        Ok(stats.into())
    }

    /// Update configuration
    fn update_config(
        &mut self,
        component_spacing: Option<f64>,
        attraction_strength: Option<f64>,
        repulsion_strength: Option<f64>,
        iterations_per_level: Option<usize>,
        damping: Option<f64>,
        enable_rotation: Option<bool>,
    ) -> PyResult<()> {
        let mut config = self.placer.config().clone();
        
        if let Some(spacing) = component_spacing {
            config.component_spacing = spacing;
        }
        if let Some(attraction) = attraction_strength {
            config.attraction_strength = attraction;
        }
        if let Some(repulsion) = repulsion_strength {
            config.repulsion_strength = repulsion;
        }
        if let Some(iterations) = iterations_per_level {
            config.iterations_per_level = iterations;
        }
        if let Some(damp) = damping {
            config.damping = damp;
        }
        if let Some(rotation) = enable_rotation {
            config.enable_rotation = rotation;
        }

        // Validate new configuration
        crate::errors::validation::validate_config(&config)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

        self.placer = ForceDirectedPlacer::new(config);
        Ok(())
    }

    fn __repr__(&self) -> String {
        format!(
            "ForceDirectedPlacer(spacing={}, attraction={}, repulsion={})",
            self.placer.config().component_spacing,
            self.placer.config().attraction_strength,
            self.placer.config().repulsion_strength
        )
    }
}

/// Utility functions for Python integration
#[pyfunction]
pub fn create_component(reference: String, footprint: String, value: String) -> PyComponent {
    PyComponent::new(reference, footprint, value)
}

#[pyfunction]
pub fn create_point(x: f64, y: f64) -> PyPoint {
    PyPoint::new(x, y)
}

#[pyfunction]
pub fn validate_placement_inputs(
    components: Vec<PyComponent>,
    connections: Vec<(String, String)>,
    board_width: f64,
    board_height: f64,
) -> PyResult<bool> {
    // Convert to Rust types for validation
    let rust_components: Vec<Component> = components.into_iter().map(|c| c.into()).collect();
    let rust_connections: Vec<Connection> = connections.into_iter().map(|(r1, r2)| Connection::new(r1, r2)).collect();

    // Validate all inputs
    crate::errors::validation::validate_board_dimensions(board_width, board_height)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    
    crate::errors::validation::validate_components(&rust_components)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    
    crate::errors::validation::validate_connections(&rust_connections, &rust_components)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

    Ok(true)
}

/// Module initialization for Python
pub fn register_python_module(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyForceDirectedPlacer>()?;
    m.add_class::<PyPoint>()?;
    m.add_class::<PyComponent>()?;
    m.add_class::<PyPlacementResult>()?;
    m.add_function(wrap_pyfunction!(create_component, m)?)?;
    m.add_function(wrap_pyfunction!(create_point, m)?)?;
    m.add_function(wrap_pyfunction!(validate_placement_inputs, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_py_point_creation() {
        let point = PyPoint::new(10.0, 20.0);
        assert_eq!(point.x, 10.0);
        assert_eq!(point.y, 20.0);
    }

    #[test]
    fn test_py_component_creation() {
        let component = PyComponent::new(
            "R1".to_string(),
            "R_0805".to_string(),
            "10k".to_string()
        );
        assert_eq!(component.reference, "R1");
        assert_eq!(component.footprint, "R_0805");
        assert_eq!(component.value, "10k");
    }

    #[test]
    fn test_component_conversion() {
        let py_component = PyComponent::new(
            "R1".to_string(),
            "R_0805".to_string(),
            "10k".to_string()
        );
        
        let rust_component: Component = py_component.clone().into();
        let back_to_py: PyComponent = rust_component.into();
        
        assert_eq!(py_component.reference, back_to_py.reference);
        assert_eq!(py_component.footprint, back_to_py.footprint);
        assert_eq!(py_component.value, back_to_py.value);
    }
}