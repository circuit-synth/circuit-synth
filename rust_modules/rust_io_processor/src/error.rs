//! Error handling for the Rust I/O processor
//! 
//! Provides comprehensive error types and handling for all I/O operations
//! with detailed context and Python-compatible error conversion.

use std::fmt;
use thiserror::Error;
use pyo3::{PyErr, exceptions::PyRuntimeError};

/// Result type alias for I/O operations
pub type IoResult<T> = Result<T, IoError>;

/// Comprehensive error types for I/O operations
#[derive(Error, Debug)]
pub enum IoError {
    #[error("File I/O error: {message}")]
    FileIo {
        message: String,
        path: Option<String>,
        #[source]
        source: Option<std::io::Error>,
    },

    #[error("JSON processing error: {message}")]
    JsonProcessing {
        message: String,
        line: Option<usize>,
        column: Option<usize>,
        #[source]
        source: Option<serde_json::Error>,
    },

    #[error("KiCad parsing error: {message}")]
    KiCadParsing {
        message: String,
        file_type: String,
        line: Option<usize>,
        #[source]
        source: Option<Box<dyn std::error::Error + Send + Sync>>,
    },

    #[error("Validation error: {message}")]
    Validation {
        message: String,
        field: Option<String>,
        expected: Option<String>,
        actual: Option<String>,
    },

    #[error("Memory error: {message}")]
    Memory {
        message: String,
        requested_size: Option<usize>,
        available_size: Option<usize>,
    },

    #[error("Configuration error: {message}")]
    Configuration {
        message: String,
        key: Option<String>,
        value: Option<String>,
    },

    #[error("Performance error: {message}")]
    Performance {
        message: String,
        operation: String,
        duration_ms: Option<u64>,
        threshold_ms: Option<u64>,
    },

    #[error("Python integration error: {message}")]
    PythonIntegration {
        message: String,
        python_type: Option<String>,
    },
}

impl IoError {
    /// Create a file I/O error
    pub fn file_io<S: Into<String>>(message: S, path: Option<String>) -> Self {
        Self::FileIo {
            message: message.into(),
            path,
            source: None,
        }
    }

    /// Create a file I/O error with source
    pub fn file_io_with_source<S: Into<String>>(
        message: S,
        path: Option<String>,
        source: std::io::Error,
    ) -> Self {
        Self::FileIo {
            message: message.into(),
            path,
            source: Some(source),
        }
    }

    /// Create a JSON processing error
    pub fn json_processing<S: Into<String>>(message: S) -> Self {
        Self::JsonProcessing {
            message: message.into(),
            line: None,
            column: None,
            source: None,
        }
    }

    /// Create a JSON processing error with location
    pub fn json_processing_with_location<S: Into<String>>(
        message: S,
        line: usize,
        column: usize,
    ) -> Self {
        Self::JsonProcessing {
            message: message.into(),
            line: Some(line),
            column: Some(column),
            source: None,
        }
    }

    /// Create a KiCad parsing error
    pub fn kicad_parsing<S: Into<String>>(message: S, file_type: S) -> Self {
        Self::KiCadParsing {
            message: message.into(),
            file_type: file_type.into(),
            line: None,
            source: None,
        }
    }

    /// Create a validation error
    pub fn validation<S: Into<String>>(message: S) -> Self {
        Self::Validation {
            message: message.into(),
            field: None,
            expected: None,
            actual: None,
        }
    }

    /// Create a validation error with field details
    pub fn validation_with_field<S: Into<String>>(
        message: S,
        field: S,
        expected: Option<S>,
        actual: Option<S>,
    ) -> Self {
        Self::Validation {
            message: message.into(),
            field: Some(field.into()),
            expected: expected.map(|s| s.into()),
            actual: actual.map(|s| s.into()),
        }
    }

    /// Create a memory error
    pub fn memory<S: Into<String>>(message: S) -> Self {
        Self::Memory {
            message: message.into(),
            requested_size: None,
            available_size: None,
        }
    }

    /// Create a performance error
    pub fn performance<S: Into<String>>(
        message: S,
        operation: S,
        duration_ms: Option<u64>,
        threshold_ms: Option<u64>,
    ) -> Self {
        Self::Performance {
            message: message.into(),
            operation: operation.into(),
            duration_ms,
            threshold_ms,
        }
    }

    /// Create a Python integration error
    pub fn python_integration<S: Into<String>>(message: S) -> Self {
        Self::PythonIntegration {
            message: message.into(),
            python_type: None,
        }
    }

    /// Get error context as JSON for detailed logging
    pub fn to_json(&self) -> serde_json::Value {
        match self {
            IoError::FileIo { message, path, .. } => serde_json::json!({
                "type": "file_io",
                "message": message,
                "path": path
            }),
            IoError::JsonProcessing { message, line, column, .. } => serde_json::json!({
                "type": "json_processing",
                "message": message,
                "line": line,
                "column": column
            }),
            IoError::KiCadParsing { message, file_type, line, .. } => serde_json::json!({
                "type": "kicad_parsing",
                "message": message,
                "file_type": file_type,
                "line": line
            }),
            IoError::Validation { message, field, expected, actual } => serde_json::json!({
                "type": "validation",
                "message": message,
                "field": field,
                "expected": expected,
                "actual": actual
            }),
            IoError::Memory { message, requested_size, available_size } => serde_json::json!({
                "type": "memory",
                "message": message,
                "requested_size": requested_size,
                "available_size": available_size
            }),
            IoError::Configuration { message, key, value } => serde_json::json!({
                "type": "configuration",
                "message": message,
                "key": key,
                "value": value
            }),
            IoError::Performance { message, operation, duration_ms, threshold_ms } => serde_json::json!({
                "type": "performance",
                "message": message,
                "operation": operation,
                "duration_ms": duration_ms,
                "threshold_ms": threshold_ms
            }),
            IoError::PythonIntegration { message, python_type } => serde_json::json!({
                "type": "python_integration",
                "message": message,
                "python_type": python_type
            }),
        }
    }
}

// Convert std::io::Error to IoError
impl From<std::io::Error> for IoError {
    fn from(err: std::io::Error) -> Self {
        IoError::file_io_with_source(
            format!("I/O operation failed: {}", err),
            None,
            err,
        )
    }
}

// Convert serde_json::Error to IoError
impl From<serde_json::Error> for IoError {
    fn from(err: serde_json::Error) -> Self {
        IoError::JsonProcessing {
            message: format!("JSON processing failed: {}", err),
            line: Some(err.line()),
            column: Some(err.column()),
            source: Some(err),
        }
    }
}

// Convert IoError to Python exception
impl From<IoError> for PyErr {
    fn from(err: IoError) -> Self {
        let error_json = err.to_json();
        PyRuntimeError::new_err(format!("Rust I/O Error: {}", error_json))
    }
}

/// Error context for detailed error reporting
#[derive(Debug, Clone)]
pub struct ErrorContext {
    pub operation: String,
    pub file_path: Option<String>,
    pub line_number: Option<usize>,
    pub additional_info: std::collections::HashMap<String, String>,
}

impl ErrorContext {
    pub fn new<S: Into<String>>(operation: S) -> Self {
        Self {
            operation: operation.into(),
            file_path: None,
            line_number: None,
            additional_info: std::collections::HashMap::new(),
        }
    }

    pub fn with_file<S: Into<String>>(mut self, file_path: S) -> Self {
        self.file_path = Some(file_path.into());
        self
    }

    pub fn with_line(mut self, line_number: usize) -> Self {
        self.line_number = Some(line_number);
        self
    }

    pub fn with_info<K: Into<String>, V: Into<String>>(mut self, key: K, value: V) -> Self {
        self.additional_info.insert(key.into(), value.into());
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_creation() {
        let err = IoError::file_io("Test error", Some("test.json".to_string()));
        assert!(matches!(err, IoError::FileIo { .. }));
    }

    #[test]
    fn test_error_json_serialization() {
        let err = IoError::validation("Invalid data");
        let json = err.to_json();
        assert_eq!(json["type"], "validation");
        assert_eq!(json["message"], "Invalid data");
    }

    #[test]
    fn test_error_context() {
        let ctx = ErrorContext::new("test_operation")
            .with_file("test.json")
            .with_line(42)
            .with_info("key", "value");
        
        assert_eq!(ctx.operation, "test_operation");
        assert_eq!(ctx.file_path, Some("test.json".to_string()));
        assert_eq!(ctx.line_number, Some(42));
        assert_eq!(ctx.additional_info.get("key"), Some(&"value".to_string()));
    }
}