//! Utility functions for the core circuit engine
//! 
//! This module provides common utilities used throughout the circuit engine.

use pyo3::prelude::*;
use regex::Regex;
use std::collections::HashMap;

/// String utilities for efficient text processing
pub struct StringUtils;

impl StringUtils {
    /// Extract symbol library and name from symbol string (e.g., "Device:R" -> ("Device", "R"))
    pub fn parse_symbol(symbol: &str) -> Option<(String, String)> {
        let parts: Vec<&str> = symbol.split(':').collect();
        if parts.len() == 2 && !parts[0].is_empty() && !parts[1].is_empty() {
            Some((parts[0].to_string(), parts[1].to_string()))
        } else {
            None
        }
    }
    
    /// Clean reference string for use as component reference
    pub fn clean_reference(input: &str) -> String {
        // Remove invalid characters and ensure it starts with a letter
        let cleaned: String = input.chars()
            .filter(|c| c.is_alphanumeric() || *c == '_')
            .collect();
        
        if cleaned.is_empty() || !cleaned.chars().next().unwrap().is_alphabetic() {
            "U".to_string()  // Default fallback
        } else {
            cleaned
        }
    }
    
    /// Check if string has trailing digits
    pub fn has_trailing_digits(s: &str) -> bool {
        if s.is_empty() {
            return false;
        }
        
        s.chars().rev().take_while(|c| c.is_numeric()).count() > 0
    }
    
    /// Extract prefix from reference (e.g., "R123" -> "R")
    pub fn extract_prefix(reference: &str) -> String {
        if let Some(pos) = reference.find(char::is_numeric) {
            reference[..pos].to_string()
        } else {
            reference.to_string()
        }
    }
    
    /// Generate default prefix from symbol (e.g., "Device:R" -> "R")
    pub fn default_prefix_from_symbol(symbol: &str) -> String {
        if let Some((_, name)) = Self::parse_symbol(symbol) {
            Self::clean_reference(&name)
        } else {
            "U".to_string()
        }
    }
}

/// Validation utilities
pub struct ValidationUtils;

impl ValidationUtils {
    /// Validate property name according to Python identifier rules
    pub fn validate_property_name(name: &str) -> Result<(), String> {
        if name.is_empty() {
            return Err("Property name cannot be empty".to_string());
        }
        
        if name.starts_with('_') {
            return Err("Property name cannot start with underscore".to_string());
        }
        
        if name.chars().next().unwrap().is_numeric() {
            return Err("Property name cannot start with digit".to_string());
        }
        
        // Check for Python keywords (basic set)
        let keywords = [
            "and", "as", "assert", "break", "class", "continue", "def", "del",
            "elif", "else", "except", "exec", "finally", "for", "from", "global",
            "if", "import", "in", "is", "lambda", "not", "or", "pass", "print",
            "raise", "return", "try", "while", "with", "yield"
        ];
        
        if keywords.contains(&name) {
            return Err("Property name cannot be a Python keyword".to_string());
        }
        
        // Check for valid identifier characters
        if !name.chars().all(|c| c.is_alphanumeric() || c == '_') {
            return Err("Property name contains invalid characters".to_string());
        }
        
        Ok(())
    }
    
    /// Validate property value (basic validation)
    pub fn validate_property_value(value: &str) -> Result<(), String> {
        if value.trim().is_empty() {
            return Err("Property value cannot be empty".to_string());
        }
        
        Ok(())
    }
    
    /// Validate symbol format
    pub fn validate_symbol_format(symbol: &str) -> Result<(), String> {
        if symbol.is_empty() {
            return Err("Symbol cannot be empty".to_string());
        }
        
        if StringUtils::parse_symbol(symbol).is_none() {
            return Err("Symbol must be in format 'Library:Symbol'".to_string());
        }
        
        Ok(())
    }
    
    /// Validate reference format
    pub fn validate_reference_format(reference: &str) -> Result<(), String> {
        if reference.is_empty() {
            return Err("Reference cannot be empty".to_string());
        }
        
        if !reference.chars().next().unwrap().is_alphabetic() {
            return Err("Reference must start with a letter".to_string());
        }
        
        if !reference.chars().all(|c| c.is_alphanumeric() || c == '_') {
            return Err("Reference contains invalid characters".to_string());
        }
        
        Ok(())
    }
}

/// Performance utilities
pub struct PerformanceUtils;

impl PerformanceUtils {
    /// Create a hash map with optimal capacity for the expected size
    pub fn create_hashmap_with_capacity<K, V>(expected_size: usize) -> HashMap<K, V> 
    where
        K: std::hash::Hash + Eq,
    {
        // Use 1.3x the expected size to reduce collisions
        let capacity = (expected_size as f64 * 1.3) as usize;
        HashMap::with_capacity(capacity)
    }
    
    /// Estimate optimal capacity for component collections based on symbol type
    pub fn estimate_pin_capacity(symbol: &str) -> usize {
        // Rough estimates based on common component types
        if let Some((_, name)) = StringUtils::parse_symbol(symbol) {
            match name.to_lowercase().as_str() {
                s if s.contains("microcontroller") || s.contains("mcu") => 100,
                s if s.contains("connector") => 50,
                s if s.contains("ic") || s.contains("chip") => 20,
                s if s.starts_with("r") || s.starts_with("c") || s.starts_with("l") => 2,
                _ => 10,  // Default
            }
        } else {
            10  // Default
        }
    }
}

/// Regex utilities with compiled patterns
pub struct RegexUtils {
    reference_pattern: Regex,
    trailing_digits_pattern: Regex,
}

impl RegexUtils {
    /// Create new regex utilities with compiled patterns
    pub fn new() -> Result<Self, regex::Error> {
        Ok(RegexUtils {
            reference_pattern: Regex::new(r"^[A-Za-z][A-Za-z0-9_]*\d*$")?,
            trailing_digits_pattern: Regex::new(r"\d+$")?,
        })
    }
    
    /// Check if string matches reference pattern
    pub fn is_valid_reference(&self, s: &str) -> bool {
        self.reference_pattern.is_match(s)
    }
    
    /// Check if string has trailing digits
    pub fn has_trailing_digits(&self, s: &str) -> bool {
        self.trailing_digits_pattern.is_match(s)
    }
}

impl Default for RegexUtils {
    fn default() -> Self {
        Self::new().expect("Failed to compile regex patterns")
    }
}

/// Python integration utilities
#[pyfunction]
pub fn parse_symbol_py(symbol: &str) -> Option<(String, String)> {
    StringUtils::parse_symbol(symbol)
}

#[pyfunction]
pub fn clean_reference_py(input: &str) -> String {
    StringUtils::clean_reference(input)
}

#[pyfunction]
pub fn has_trailing_digits_py(s: &str) -> bool {
    StringUtils::has_trailing_digits(s)
}

#[pyfunction]
pub fn validate_property_name_py(name: &str) -> PyResult<()> {
    ValidationUtils::validate_property_name(name)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))
}

#[pyfunction]
pub fn validate_symbol_format_py(symbol: &str) -> PyResult<()> {
    ValidationUtils::validate_symbol_format(symbol)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))
}

/// Add utility functions to Python module
pub fn add_utils_to_module(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_symbol_py, m)?)?;
    m.add_function(wrap_pyfunction!(clean_reference_py, m)?)?;
    m.add_function(wrap_pyfunction!(has_trailing_digits_py, m)?)?;
    m.add_function(wrap_pyfunction!(validate_property_name_py, m)?)?;
    m.add_function(wrap_pyfunction!(validate_symbol_format_py, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_parse_symbol() {
        assert_eq!(
            StringUtils::parse_symbol("Device:R"),
            Some(("Device".to_string(), "R".to_string()))
        );
        assert_eq!(StringUtils::parse_symbol("Invalid"), None);
        assert_eq!(StringUtils::parse_symbol(""), None);
    }
    
    #[test]
    fn test_clean_reference() {
        assert_eq!(StringUtils::clean_reference("R1"), "R1");
        assert_eq!(StringUtils::clean_reference("1R"), "U");  // Invalid start
        assert_eq!(StringUtils::clean_reference("R-1"), "R1");  // Remove invalid chars
        assert_eq!(StringUtils::clean_reference(""), "U");  // Empty fallback
    }
    
    #[test]
    fn test_has_trailing_digits() {
        assert!(StringUtils::has_trailing_digits("R123"));
        assert!(StringUtils::has_trailing_digits("U1"));
        assert!(!StringUtils::has_trailing_digits("R"));
        assert!(!StringUtils::has_trailing_digits(""));
    }
    
    #[test]
    fn test_validation() {
        assert!(ValidationUtils::validate_property_name("valid_name").is_ok());
        assert!(ValidationUtils::validate_property_name("_invalid").is_err());
        assert!(ValidationUtils::validate_property_name("1invalid").is_err());
        assert!(ValidationUtils::validate_property_name("class").is_err());
        
        assert!(ValidationUtils::validate_symbol_format("Device:R").is_ok());
        assert!(ValidationUtils::validate_symbol_format("Invalid").is_err());
        
        assert!(ValidationUtils::validate_reference_format("R1").is_ok());
        assert!(ValidationUtils::validate_reference_format("1R").is_err());
    }
}