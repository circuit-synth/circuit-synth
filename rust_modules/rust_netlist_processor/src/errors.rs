//! Error types and handling for the netlist processor
//!
//! This module defines comprehensive error types for all processing stages,
//! enabling precise error reporting and debugging.

use std::fmt;
use thiserror::Error;

/// Result type alias for netlist processing operations
pub type Result<T> = std::result::Result<T, NetlistError>;

/// Comprehensive error types for netlist processing
#[derive(Error, Debug)]
pub enum NetlistError {
    /// JSON parsing or serialization errors
    #[error("JSON processing error: {message}")]
    JsonError {
        message: String,
        #[source]
        source: Option<serde_json::Error>,
    },

    /// Invalid circuit data structure
    #[error("Invalid circuit data: {message}")]
    InvalidCircuitData { message: String },

    /// Component processing errors
    #[error("Component processing error: {message}")]
    ComponentError { message: String },

    /// Net processing errors
    #[error("Net processing error: {message}")]
    NetProcessingError { message: String },

    /// Library part processing errors
    #[error("Library part error: {message}")]
    LibpartError { message: String },

    /// S-expression formatting errors
    #[error("S-expression formatting error: {message}")]
    FormattingError { message: String },

    /// Missing required data
    #[error("Missing required data: {field}")]
    MissingData { field: String },

    /// Invalid pin type or configuration
    #[error("Invalid pin configuration: {message}")]
    InvalidPin { message: String },

    /// Hierarchical path processing errors
    #[error("Hierarchical path error: {message}")]
    HierarchyError { message: String },

    /// String interning or memory errors
    #[error("Memory management error: {message}")]
    MemoryError { message: String },

    /// I/O errors (file operations, etc.)
    #[error("I/O error: {message}")]
    IoError {
        message: String,
        #[source]
        source: std::io::Error,
    },

    /// Generic processing errors
    #[error("Processing error: {message}")]
    ProcessingError { message: String },
}

impl NetlistError {
    /// Create a new JSON error
    pub fn json_error(message: impl Into<String>, source: Option<serde_json::Error>) -> Self {
        Self::JsonError {
            message: message.into(),
            source,
        }
    }

    /// Create a new invalid circuit data error
    pub fn invalid_circuit_data(message: impl Into<String>) -> Self {
        Self::InvalidCircuitData {
            message: message.into(),
        }
    }

    /// Create a new component error
    pub fn component_error(message: impl Into<String>) -> Self {
        Self::ComponentError {
            message: message.into(),
        }
    }

    /// Create a new net processing error
    pub fn net_processing_error(message: impl Into<String>) -> Self {
        Self::NetProcessingError {
            message: message.into(),
        }
    }

    /// Create a new libpart error
    pub fn libpart_error(message: impl Into<String>) -> Self {
        Self::LibpartError {
            message: message.into(),
        }
    }

    /// Create a new formatting error
    pub fn formatting_error(message: impl Into<String>) -> Self {
        Self::FormattingError {
            message: message.into(),
        }
    }

    /// Create a new missing data error
    pub fn missing_data(field: impl Into<String>) -> Self {
        Self::MissingData {
            field: field.into(),
        }
    }

    /// Create a new invalid pin error
    pub fn invalid_pin(message: impl Into<String>) -> Self {
        Self::InvalidPin {
            message: message.into(),
        }
    }

    /// Create a new hierarchy error
    pub fn hierarchy_error(message: impl Into<String>) -> Self {
        Self::HierarchyError {
            message: message.into(),
        }
    }

    /// Create a new memory error
    pub fn memory_error(message: impl Into<String>) -> Self {
        Self::MemoryError {
            message: message.into(),
        }
    }

    /// Create a new I/O error
    pub fn io_error(message: impl Into<String>, source: std::io::Error) -> Self {
        Self::IoError {
            message: message.into(),
            source,
        }
    }

    /// Create a new processing error
    pub fn processing_error(message: impl Into<String>) -> Self {
        Self::ProcessingError {
            message: message.into(),
        }
    }
}

// Automatic conversion from serde_json::Error
impl From<serde_json::Error> for NetlistError {
    fn from(err: serde_json::Error) -> Self {
        Self::json_error("JSON serialization/deserialization failed", Some(err))
    }
}

// Automatic conversion from std::io::Error
impl From<std::io::Error> for NetlistError {
    fn from(err: std::io::Error) -> Self {
        Self::io_error("I/O operation failed", err)
    }
}

// Automatic conversion from std::fmt::Error (for write! operations)
impl From<std::fmt::Error> for NetlistError {
    fn from(_err: std::fmt::Error) -> Self {
        Self::formatting_error("String formatting failed")
    }
}

/// Context trait for adding context to errors
pub trait ErrorContext<T> {
    /// Add context to an error
    fn with_context<F>(self, f: F) -> Result<T>
    where
        F: FnOnce() -> String;

    /// Add context to an error with a static string
    fn context(self, msg: &'static str) -> Result<T>;
}

impl<T, E> ErrorContext<T> for std::result::Result<T, E>
where
    E: Into<NetlistError>,
{
    fn with_context<F>(self, f: F) -> Result<T>
    where
        F: FnOnce() -> String,
    {
        self.map_err(|e| {
            let original_error = e.into();
            NetlistError::processing_error(format!("{}: {}", f(), original_error))
        })
    }

    fn context(self, msg: &'static str) -> Result<T> {
        self.with_context(|| msg.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_creation() {
        let err = NetlistError::component_error("Test component error");
        assert!(matches!(err, NetlistError::ComponentError { .. }));
        assert_eq!(err.to_string(), "Component processing error: Test component error");
    }

    #[test]
    fn test_error_context() {
        let result: std::result::Result<(), std::io::Error> = 
            Err(std::io::Error::new(std::io::ErrorKind::NotFound, "file not found"));
        
        let with_context = result.context("Failed to read configuration file");
        assert!(with_context.is_err());
    }

    #[test]
    fn test_json_error_conversion() {
        let json_err = serde_json::from_str::<serde_json::Value>("invalid json");
        assert!(json_err.is_err());
        
        let netlist_err: NetlistError = json_err.unwrap_err().into();
        assert!(matches!(netlist_err, NetlistError::JsonError { .. }));
    }
}