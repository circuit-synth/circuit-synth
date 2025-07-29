//! High-performance force-directed placement algorithm for PCB components
//!
//! This crate provides a Rust implementation of force-directed placement algorithms
//! optimized for PCB component placement with O(n²) performance improvements.

pub mod collision;
pub mod errors;
pub mod forces;
pub mod placement;
pub mod python;
pub mod types;

pub use collision::*;
pub use errors::*;
pub use forces::*;
pub use placement::*;
pub use types::*;

use pyo3::prelude::*;

/// Python module for force-directed placement
#[pymodule]
fn rust_force_directed_placement(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<python::PyForceDirectedPlacer>()?;
    m.add_class::<python::PyPoint>()?;
    m.add_class::<python::PyComponent>()?;
    m.add_class::<python::PyPlacementResult>()?;
    m.add_function(wrap_pyfunction!(python::create_component, m)?)?;
    m.add_function(wrap_pyfunction!(python::create_point, m)?)?;
    m.add_function(wrap_pyfunction!(python::validate_placement_inputs, m)?)?;
    Ok(())
}
