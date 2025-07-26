//! Error types for the core circuit engine
//! 
//! This module defines all error types used throughout the circuit engine,
//! with PyO3 integration for seamless Python exception handling.

use pyo3::prelude::*;
use pyo3::exceptions::PyException;
use thiserror::Error;

/// General circuit-related errors
#[derive(Error, Debug)]
pub enum CircuitError {
    #[error("Invalid circuit name: {0}")]
    InvalidName(String),
    
    #[error("Circuit hierarchy error: {0}")]
    HierarchyError(String),
    
    #[error("Reference collision: {0}")]
    ReferenceCollision(String),
    
    #[error("Invalid operation: {0}")]
    InvalidOperation(String),
}

/// Component-specific errors
#[derive(Error, Debug)]
pub enum ComponentError {
    #[error("Invalid symbol format: {0}")]
    InvalidSymbol(String),
    
    #[error("Symbol not found: {0}")]
    SymbolNotFound(String),
    
    #[error("Invalid component reference: {0}")]
    InvalidReference(String),
    
    #[error("Pin not found: {0}")]
    PinNotFound(String),
    
    #[error("Invalid property: {0}")]
    InvalidProperty(String),
    
    #[error("Component cloning error: {0}")]
    CloningError(String),
}

/// Validation errors for properties and references
#[derive(Error, Debug)]
pub enum ValidationError {
    #[error("Invalid reference format: {0}")]
    InvalidReference(String),
    
    #[error("Invalid symbol format: {0}")]
    InvalidSymbol(String),
    
    #[error("Property validation failed: {0}")]
    PropertyValidation(String),
    
    #[error("Type validation failed: {0}")]
    TypeValidation(String),
    
    #[error("Range validation failed: {0}")]
    RangeValidation(String),
    
    #[error("Required field missing: {0}")]
    MissingField(String),
}

/// Net connectivity errors
#[derive(Error, Debug)]
pub enum NetError {
    #[error("Invalid net connection: {0}")]
    InvalidConnection(String),
    
    #[error("Pin type mismatch: {0}")]
    PinTypeMismatch(String),
    
    #[error("Net not found: {0}")]
    NetNotFound(String),
    
    #[error("Circular connection detected: {0}")]
    CircularConnection(String),
}

/// Pin-specific errors
#[derive(Error, Debug)]
pub enum PinError {
    #[error("Invalid pin type: {0}")]
    InvalidType(String),
    
    #[error("Pin already connected: {0}")]
    AlreadyConnected(String),
    
    #[error("Incompatible pin types: {0} cannot connect to {1}")]
    IncompatibleTypes(String, String),
    
    #[error("Pin geometry error: {0}")]
    GeometryError(String),
}

/// Reference manager errors
#[derive(Error, Debug)]
pub enum ReferenceError {
    #[error("Reference already exists: {0}")]
    AlreadyExists(String),
    
    #[error("Invalid reference format: {0}")]
    InvalidFormat(String),
    
    #[error("Reference generation failed: {0}")]
    GenerationFailed(String),
    
    #[error("Hierarchy validation failed: {0}")]
    HierarchyValidation(String),
}

// Python wrapper structs for error types
#[pyclass(name = "CircuitError")]
#[derive(Debug, Clone)]
pub struct PyCircuitError {
    pub message: String,
}

#[pymethods]
impl PyCircuitError {
    #[new]
    fn new(message: String) -> Self {
        PyCircuitError { message }
    }
    
    fn __str__(&self) -> String {
        self.message.clone()
    }
    
    fn __repr__(&self) -> String {
        format!("CircuitError('{}')", self.message)
    }
}

#[pyclass(name = "ComponentError")]
#[derive(Debug, Clone)]
pub struct PyComponentError {
    pub message: String,
}

#[pymethods]
impl PyComponentError {
    #[new]
    fn new(message: String) -> Self {
        PyComponentError { message }
    }
    
    fn __str__(&self) -> String {
        self.message.clone()
    }
    
    fn __repr__(&self) -> String {
        format!("ComponentError('{}')", self.message)
    }
}

#[pyclass(name = "ValidationError")]
#[derive(Debug, Clone)]
pub struct PyValidationError {
    pub message: String,
}

#[pymethods]
impl PyValidationError {
    #[new]
    fn new(message: String) -> Self {
        PyValidationError { message }
    }
    
    fn __str__(&self) -> String {
        self.message.clone()
    }
    
    fn __repr__(&self) -> String {
        format!("ValidationError('{}')", self.message)
    }
}

#[pyclass(name = "NetError")]
#[derive(Debug, Clone)]
pub struct PyNetError {
    pub message: String,
}

#[pymethods]
impl PyNetError {
    #[new]
    fn new(message: String) -> Self {
        PyNetError { message }
    }
    
    fn __str__(&self) -> String {
        self.message.clone()
    }
    
    fn __repr__(&self) -> String {
        format!("NetError('{}')", self.message)
    }
}

#[pyclass(name = "PinError")]
#[derive(Debug, Clone)]
pub struct PyPinError {
    pub message: String,
}

#[pymethods]
impl PyPinError {
    #[new]
    fn new(message: String) -> Self {
        PyPinError { message }
    }
    
    fn __str__(&self) -> String {
        self.message.clone()
    }
    
    fn __repr__(&self) -> String {
        format!("PinError('{}')", self.message)
    }
}

#[pyclass(name = "ReferenceError")]
#[derive(Debug, Clone)]
pub struct PyReferenceError {
    pub message: String,
}

#[pymethods]
impl PyReferenceError {
    #[new]
    fn new(message: String) -> Self {
        PyReferenceError { message }
    }
    
    fn __str__(&self) -> String {
        self.message.clone()
    }
    
    fn __repr__(&self) -> String {
        format!("ReferenceError('{}')", self.message)
    }
}

/// Convert Rust errors to Python exceptions
impl From<CircuitError> for PyErr {
    fn from(err: CircuitError) -> PyErr {
        PyException::new_err(err.to_string())
    }
}

impl From<ComponentError> for PyErr {
    fn from(err: ComponentError) -> PyErr {
        PyException::new_err(err.to_string())
    }
}

impl From<ValidationError> for PyErr {
    fn from(err: ValidationError) -> PyErr {
        PyException::new_err(err.to_string())
    }
}

impl From<NetError> for PyErr {
    fn from(err: NetError) -> PyErr {
        PyException::new_err(err.to_string())
    }
}

impl From<PinError> for PyErr {
    fn from(err: PinError) -> PyErr {
        PyException::new_err(err.to_string())
    }
}

impl From<ReferenceError> for PyErr {
    fn from(err: ReferenceError) -> PyErr {
        PyException::new_err(err.to_string())
    }
}

// Convert from Rust errors to Python wrapper structs
impl From<CircuitError> for PyCircuitError {
    fn from(err: CircuitError) -> Self {
        PyCircuitError {
            message: err.to_string(),
        }
    }
}

impl From<ComponentError> for PyComponentError {
    fn from(err: ComponentError) -> Self {
        PyComponentError {
            message: err.to_string(),
        }
    }
}

impl From<ValidationError> for PyValidationError {
    fn from(err: ValidationError) -> Self {
        PyValidationError {
            message: err.to_string(),
        }
    }
}

impl From<NetError> for PyNetError {
    fn from(err: NetError) -> Self {
        PyNetError {
            message: err.to_string(),
        }
    }
}

impl From<PinError> for PyPinError {
    fn from(err: PinError) -> Self {
        PyPinError {
            message: err.to_string(),
        }
    }
}

impl From<ReferenceError> for PyReferenceError {
    fn from(err: ReferenceError) -> Self {
        PyReferenceError {
            message: err.to_string(),
        }
    }
}