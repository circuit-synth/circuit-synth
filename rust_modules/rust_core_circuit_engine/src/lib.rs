//! # Rust Core Circuit Engine
//!
//! High-performance core circuit engine for Circuit Synth, providing 10-100x performance
//! improvements over the Python implementation while maintaining 100% API compatibility.
//!
//! This crate implements the core circuit data structures (Circuit, Component, Net, Pin)
//! and reference management system in Rust with PyO3 bindings for seamless Python integration.

use pyo3::prelude::*;

// Core modules
pub mod circuit;
pub mod component;
pub mod debug_utils;
pub mod errors;
pub mod net;
pub mod pin;
pub mod reference_manager;
pub mod utils;

// Re-export main types
pub use circuit::Circuit;
pub use component::Component;
pub use errors::{CircuitError, ComponentError, ValidationError};
pub use net::Net;
pub use pin::{Pin, PinType};
pub use reference_manager::ReferenceManager;

/// Python module definition
#[pymodule]
fn rust_core_circuit_engine(_py: Python, m: &PyModule) -> PyResult<()> {
    // Add core classes
    m.add_class::<Circuit>()?;
    m.add_class::<Component>()?;
    m.add_class::<Net>()?;
    m.add_class::<Pin>()?;
    m.add_class::<PinType>()?;
    m.add_class::<ReferenceManager>()?;

    // Add exception types
    m.add_class::<errors::PyCircuitError>()?;
    m.add_class::<errors::PyComponentError>()?;
    m.add_class::<errors::PyValidationError>()?;
    m.add_class::<errors::PyNetError>()?;
    m.add_class::<errors::PyPinError>()?;
    m.add_class::<errors::PyReferenceError>()?;

    // Add module metadata
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add("__author__", "Circuit Synth Team")?;
    m.add("__description__", "High-performance core circuit engine")?;

    Ok(())
}
