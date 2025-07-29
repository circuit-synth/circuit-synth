//! Error types for the reference manager
//!
//! This module defines all error types used throughout the reference manager,
//! providing clear error messages and proper error handling.

use thiserror::Error;

/// Main error type for reference manager operations
#[derive(Error, Debug, Clone)]
pub enum ReferenceError {
    /// Validation errors
    #[error("Validation error: {0}")]
    Validation(#[from] ValidationError),

    /// Hierarchy management errors
    #[error("Hierarchy error: {0}")]
    HierarchyError(String),

    /// Concurrency errors
    #[error("Concurrency error: {0}")]
    ConcurrencyError(String),

    /// Configuration errors
    #[error("Configuration error: {0}")]
    ConfigError(String),

    /// Internal errors
    #[error("Internal error: {0}")]
    InternalError(String),
}

/// Validation-specific errors
#[derive(Error, Debug, Clone)]
pub enum ValidationError {
    /// Empty reference provided
    #[error("Reference cannot be empty")]
    EmptyReference,

    /// Empty prefix provided
    #[error("Prefix cannot be empty")]
    EmptyPrefix,

    /// Reference is too long
    #[error("Reference '{reference}' exceeds maximum length of {max_length} characters")]
    ReferenceTooLong {
        reference: String,
        max_length: usize,
    },

    /// Prefix is too long
    #[error("Prefix '{prefix}' exceeds maximum length of {max_length} characters")]
    PrefixTooLong { prefix: String, max_length: usize },

    /// Reference already in use
    #[error("Reference '{reference}' is already in use")]
    AlreadyInUse { reference: String },

    /// Reserved reference cannot be used
    #[error("Reference '{reference}' is reserved and cannot be used")]
    ReservedReference { reference: String },

    /// Reserved prefix cannot be used
    #[error("Prefix '{prefix}' is reserved and cannot be used")]
    ReservedPrefix { prefix: String },

    /// Invalid character in prefix
    #[error("Invalid character '{invalid_char}' in prefix '{prefix}'")]
    InvalidPrefixCharacter { prefix: String, invalid_char: char },

    /// Invalid character in number part
    #[error("Invalid character '{invalid_char}' in number part '{number_part}'")]
    InvalidNumberCharacter {
        number_part: String,
        invalid_char: char,
    },

    /// Prefix must start with a letter
    #[error("Prefix '{prefix}' must start with a letter")]
    PrefixMustStartWithLetter { prefix: String },

    /// Missing number in reference
    #[error("Reference must contain a number")]
    MissingNumber,

    /// Invalid number format
    #[error("Invalid number format in '{number_part}'")]
    InvalidNumber { number_part: String },

    /// Invalid reference format
    #[error("Invalid reference format '{reference}': {reason}")]
    InvalidReferenceFormat { reference: String, reason: String },

    /// Counter overflow
    #[error("Counter overflow for prefix '{prefix}' (max value: {max_value})")]
    CounterOverflow { prefix: String, max_value: u32 },
}

/// Result type alias for reference manager operations
pub type ReferenceResult<T> = Result<T, ReferenceError>;

/// Result type alias for validation operations
pub type ValidationResult<T> = Result<T, ValidationError>;

impl ReferenceError {
    /// Create a hierarchy error
    pub fn hierarchy_error(message: impl Into<String>) -> Self {
        Self::HierarchyError(message.into())
    }

    /// Create a concurrency error
    pub fn concurrency_error(message: impl Into<String>) -> Self {
        Self::ConcurrencyError(message.into())
    }

    /// Create a configuration error
    pub fn config_error(message: impl Into<String>) -> Self {
        Self::ConfigError(message.into())
    }

    /// Create an internal error
    pub fn internal_error(message: impl Into<String>) -> Self {
        Self::InternalError(message.into())
    }

    /// Check if this is a validation error
    pub fn is_validation_error(&self) -> bool {
        matches!(self, Self::Validation(_))
    }

    /// Check if this is a hierarchy error
    pub fn is_hierarchy_error(&self) -> bool {
        matches!(self, Self::HierarchyError(_))
    }

    /// Check if this is a concurrency error
    pub fn is_concurrency_error(&self) -> bool {
        matches!(self, Self::ConcurrencyError(_))
    }

    /// Get the error category as a string
    pub fn category(&self) -> &'static str {
        match self {
            Self::Validation(_) => "validation",
            Self::HierarchyError(_) => "hierarchy",
            Self::ConcurrencyError(_) => "concurrency",
            Self::ConfigError(_) => "configuration",
            Self::InternalError(_) => "internal",
        }
    }

    /// Get error details for logging
    pub fn details(&self) -> serde_json::Value {
        serde_json::json!({
            "category": self.category(),
            "message": self.to_string(),
            "error_type": match self {
                Self::Validation(v) => format!("validation::{}", v.error_type()),
                Self::HierarchyError(_) => "hierarchy::general".to_string(),
                Self::ConcurrencyError(_) => "concurrency::general".to_string(),
                Self::ConfigError(_) => "config::general".to_string(),
                Self::InternalError(_) => "internal::general".to_string(),
            }
        })
    }
}

impl ValidationError {
    /// Get the specific validation error type
    pub fn error_type(&self) -> &'static str {
        match self {
            Self::EmptyReference => "empty_reference",
            Self::EmptyPrefix => "empty_prefix",
            Self::ReferenceTooLong { .. } => "reference_too_long",
            Self::PrefixTooLong { .. } => "prefix_too_long",
            Self::AlreadyInUse { .. } => "already_in_use",
            Self::ReservedReference { .. } => "reserved_reference",
            Self::ReservedPrefix { .. } => "reserved_prefix",
            Self::InvalidPrefixCharacter { .. } => "invalid_prefix_character",
            Self::InvalidNumberCharacter { .. } => "invalid_number_character",
            Self::PrefixMustStartWithLetter { .. } => "prefix_must_start_with_letter",
            Self::MissingNumber => "missing_number",
            Self::InvalidNumber { .. } => "invalid_number",
            Self::InvalidReferenceFormat { .. } => "invalid_reference_format",
            Self::CounterOverflow { .. } => "counter_overflow",
        }
    }

    /// Check if this is a format-related error
    pub fn is_format_error(&self) -> bool {
        matches!(
            self,
            Self::EmptyReference
                | Self::EmptyPrefix
                | Self::InvalidPrefixCharacter { .. }
                | Self::InvalidNumberCharacter { .. }
                | Self::PrefixMustStartWithLetter { .. }
                | Self::MissingNumber
                | Self::InvalidNumber { .. }
                | Self::InvalidReferenceFormat { .. }
        )
    }

    /// Check if this is a constraint-related error
    pub fn is_constraint_error(&self) -> bool {
        matches!(
            self,
            Self::ReferenceTooLong { .. }
                | Self::PrefixTooLong { .. }
                | Self::AlreadyInUse { .. }
                | Self::ReservedReference { .. }
                | Self::ReservedPrefix { .. }
                | Self::CounterOverflow { .. }
        )
    }

    /// Get validation error details for logging
    pub fn details(&self) -> serde_json::Value {
        match self {
            Self::EmptyReference => serde_json::json!({
                "type": "empty_reference"
            }),
            Self::EmptyPrefix => serde_json::json!({
                "type": "empty_prefix"
            }),
            Self::ReferenceTooLong {
                reference,
                max_length,
            } => serde_json::json!({
                "type": "reference_too_long",
                "reference": reference,
                "max_length": max_length,
                "actual_length": reference.len()
            }),
            Self::PrefixTooLong { prefix, max_length } => serde_json::json!({
                "type": "prefix_too_long",
                "prefix": prefix,
                "max_length": max_length,
                "actual_length": prefix.len()
            }),
            Self::AlreadyInUse { reference } => serde_json::json!({
                "type": "already_in_use",
                "reference": reference
            }),
            Self::ReservedReference { reference } => serde_json::json!({
                "type": "reserved_reference",
                "reference": reference
            }),
            Self::ReservedPrefix { prefix } => serde_json::json!({
                "type": "reserved_prefix",
                "prefix": prefix
            }),
            Self::InvalidPrefixCharacter {
                prefix,
                invalid_char,
            } => serde_json::json!({
                "type": "invalid_prefix_character",
                "prefix": prefix,
                "invalid_char": invalid_char.to_string()
            }),
            Self::InvalidNumberCharacter {
                number_part,
                invalid_char,
            } => serde_json::json!({
                "type": "invalid_number_character",
                "number_part": number_part,
                "invalid_char": invalid_char.to_string()
            }),
            Self::PrefixMustStartWithLetter { prefix } => serde_json::json!({
                "type": "prefix_must_start_with_letter",
                "prefix": prefix
            }),
            Self::MissingNumber => serde_json::json!({
                "type": "missing_number"
            }),
            Self::InvalidNumber { number_part } => serde_json::json!({
                "type": "invalid_number",
                "number_part": number_part
            }),
            Self::InvalidReferenceFormat { reference, reason } => serde_json::json!({
                "type": "invalid_reference_format",
                "reference": reference,
                "reason": reason
            }),
            Self::CounterOverflow { prefix, max_value } => serde_json::json!({
                "type": "counter_overflow",
                "prefix": prefix,
                "max_value": max_value
            }),
        }
    }
}

/// Convert ReferenceError to a format suitable for Python exceptions
impl ReferenceError {
    pub fn to_python_exception(&self) -> (&'static str, String) {
        match self {
            Self::Validation(v) => ("ValueError", format!("Validation error: {}", v)),
            Self::HierarchyError(msg) => ("RuntimeError", format!("Hierarchy error: {}", msg)),
            Self::ConcurrencyError(msg) => ("RuntimeError", format!("Concurrency error: {}", msg)),
            Self::ConfigError(msg) => ("ValueError", format!("Configuration error: {}", msg)),
            Self::InternalError(msg) => ("RuntimeError", format!("Internal error: {}", msg)),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_creation() {
        let error = ReferenceError::Validation(ValidationError::EmptyReference);
        assert!(error.is_validation_error());
        assert_eq!(error.category(), "validation");
    }

    #[test]
    fn test_validation_error_types() {
        let error = ValidationError::AlreadyInUse {
            reference: "R1".to_string(),
        };
        assert_eq!(error.error_type(), "already_in_use");
        assert!(error.is_constraint_error());
        assert!(!error.is_format_error());
    }

    #[test]
    fn test_error_details() {
        let error = ReferenceError::Validation(ValidationError::ReferenceTooLong {
            reference: "VERY_LONG_REFERENCE".to_string(),
            max_length: 10,
        });

        let details = error.details();
        assert_eq!(details["category"], "validation");
        assert!(details["message"]
            .as_str()
            .unwrap()
            .contains("VERY_LONG_REFERENCE"));
    }

    #[test]
    fn test_validation_error_details() {
        let error = ValidationError::InvalidPrefixCharacter {
            prefix: "R-".to_string(),
            invalid_char: '-',
        };

        let details = error.details();
        assert_eq!(details["type"], "invalid_prefix_character");
        assert_eq!(details["prefix"], "R-");
        assert_eq!(details["invalid_char"], "-");
    }

    #[test]
    fn test_python_exception_conversion() {
        let error = ReferenceError::Validation(ValidationError::EmptyReference);
        let (exc_type, message) = error.to_python_exception();
        assert_eq!(exc_type, "ValueError");
        assert!(message.contains("Validation error"));
    }

    #[test]
    fn test_error_categorization() {
        let format_error = ValidationError::InvalidReferenceFormat {
            reference: "123".to_string(),
            reason: "Must start with letter".to_string(),
        };
        assert!(format_error.is_format_error());
        assert!(!format_error.is_constraint_error());

        let constraint_error = ValidationError::AlreadyInUse {
            reference: "R1".to_string(),
        };
        assert!(!constraint_error.is_format_error());
        assert!(constraint_error.is_constraint_error());
    }

    #[test]
    fn test_error_chaining() {
        let validation_error = ValidationError::EmptyReference;
        let reference_error = ReferenceError::from(validation_error);

        assert!(reference_error.is_validation_error());
        assert_eq!(reference_error.category(), "validation");
    }
}
