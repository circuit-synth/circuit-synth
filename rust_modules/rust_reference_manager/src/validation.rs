//! Reference validation utilities
//! 
//! This module provides validation functionality for reference formats,
//! prefixes, and other constraints to ensure data integrity.

use crate::errors::{ReferenceError, ValidationError};
use std::collections::HashSet;

/// Reference validator with configurable rules
#[derive(Debug, Clone)]
pub struct ReferenceValidator {
    /// Maximum length for a reference
    max_reference_length: usize,
    
    /// Maximum length for a prefix
    max_prefix_length: usize,
    
    /// Allowed characters in prefixes
    allowed_prefix_chars: HashSet<char>,
    
    /// Allowed characters in reference numbers
    allowed_number_chars: HashSet<char>,
    
    /// Reserved prefixes that cannot be used
    reserved_prefixes: HashSet<String>,
    
    /// Reserved references that cannot be used
    reserved_references: HashSet<String>,
}

impl Default for ReferenceValidator {
    fn default() -> Self {
        let mut allowed_prefix_chars = HashSet::new();
        // Allow uppercase letters
        for c in 'A'..='Z' {
            allowed_prefix_chars.insert(c);
        }
        // Allow lowercase letters
        for c in 'a'..='z' {
            allowed_prefix_chars.insert(c);
        }
        // Allow underscore
        allowed_prefix_chars.insert('_');

        let mut allowed_number_chars = HashSet::new();
        // Allow digits
        for c in '0'..='9' {
            allowed_number_chars.insert(c);
        }

        let mut reserved_prefixes = HashSet::new();
        reserved_prefixes.insert("N$".to_string()); // Reserved for unnamed nets

        let mut reserved_references = HashSet::new();
        reserved_references.insert("GND".to_string());
        reserved_references.insert("VCC".to_string());
        reserved_references.insert("VDD".to_string());
        reserved_references.insert("VSS".to_string());

        Self {
            max_reference_length: 64,
            max_prefix_length: 16,
            allowed_prefix_chars,
            allowed_number_chars,
            reserved_prefixes,
            reserved_references,
        }
    }
}

impl ReferenceValidator {
    /// Create a new reference validator with default rules
    pub fn new() -> Self {
        Self::default()
    }

    /// Create a validator with custom configuration
    pub fn with_config(
        max_reference_length: usize,
        max_prefix_length: usize,
        reserved_prefixes: Vec<String>,
        reserved_references: Vec<String>,
    ) -> Self {
        let mut validator = Self::default();
        validator.max_reference_length = max_reference_length;
        validator.max_prefix_length = max_prefix_length;
        validator.reserved_prefixes.extend(reserved_prefixes);
        validator.reserved_references.extend(reserved_references);
        validator
    }

    /// Validate a complete reference (e.g., "R1", "C23", "U5")
    pub fn validate_format(&self, reference: &str) -> Result<(), ReferenceError> {
        // Check length
        if reference.is_empty() {
            return Err(ReferenceError::Validation(ValidationError::EmptyReference));
        }

        if reference.len() > self.max_reference_length {
            return Err(ReferenceError::Validation(ValidationError::ReferenceTooLong {
                reference: reference.to_string(),
                max_length: self.max_reference_length,
            }));
        }

        // Check for reserved references
        if self.reserved_references.contains(reference) {
            return Err(ReferenceError::Validation(ValidationError::ReservedReference {
                reference: reference.to_string(),
            }));
        }

        // Parse prefix and number
        let (prefix, number_part) = self.parse_reference(reference)?;

        // Validate prefix
        self.validate_prefix(&prefix)?;

        // Validate number part
        self.validate_number_part(&number_part)?;

        Ok(())
    }

    /// Validate a prefix (e.g., "R", "C", "U")
    pub fn validate_prefix(&self, prefix: &str) -> Result<(), ReferenceError> {
        // Check length
        if prefix.is_empty() {
            return Err(ReferenceError::Validation(ValidationError::EmptyPrefix));
        }

        if prefix.len() > self.max_prefix_length {
            return Err(ReferenceError::Validation(ValidationError::PrefixTooLong {
                prefix: prefix.to_string(),
                max_length: self.max_prefix_length,
            }));
        }

        // Check for reserved prefixes
        if self.reserved_prefixes.contains(prefix) {
            return Err(ReferenceError::Validation(ValidationError::ReservedPrefix {
                prefix: prefix.to_string(),
            }));
        }

        // Check characters
        for ch in prefix.chars() {
            if !self.allowed_prefix_chars.contains(&ch) {
                return Err(ReferenceError::Validation(ValidationError::InvalidPrefixCharacter {
                    prefix: prefix.to_string(),
                    invalid_char: ch,
                }));
            }
        }

        // Prefix must start with a letter
        if let Some(first_char) = prefix.chars().next() {
            if !first_char.is_alphabetic() {
                return Err(ReferenceError::Validation(ValidationError::PrefixMustStartWithLetter {
                    prefix: prefix.to_string(),
                }));
            }
        }

        Ok(())
    }

    /// Validate the number part of a reference
    pub fn validate_number_part(&self, number_part: &str) -> Result<(), ReferenceError> {
        if number_part.is_empty() {
            return Err(ReferenceError::Validation(ValidationError::MissingNumber));
        }

        // Check characters
        for ch in number_part.chars() {
            if !self.allowed_number_chars.contains(&ch) {
                return Err(ReferenceError::Validation(ValidationError::InvalidNumberCharacter {
                    number_part: number_part.to_string(),
                    invalid_char: ch,
                }));
            }
        }

        // Parse as number to ensure it's valid
        number_part.parse::<u32>().map_err(|_| {
            ReferenceError::Validation(ValidationError::InvalidNumber {
                number_part: number_part.to_string(),
            })
        })?;

        Ok(())
    }

    /// Parse a reference into prefix and number parts
    pub fn parse_reference(&self, reference: &str) -> Result<(String, String), ReferenceError> {
        // Find the boundary between letters and numbers
        let mut prefix_end = 0;
        
        for (i, ch) in reference.char_indices() {
            if ch.is_alphabetic() || ch == '_' {
                prefix_end = i + ch.len_utf8();
            } else if ch.is_numeric() {
                break;
            } else {
                return Err(ReferenceError::Validation(ValidationError::InvalidReferenceFormat {
                    reference: reference.to_string(),
                    reason: format!("Invalid character '{}' at position {}", ch, i),
                }));
            }
        }

        if prefix_end == 0 {
            return Err(ReferenceError::Validation(ValidationError::InvalidReferenceFormat {
                reference: reference.to_string(),
                reason: "Reference must start with a letter".to_string(),
            }));
        }

        if prefix_end >= reference.len() {
            return Err(ReferenceError::Validation(ValidationError::InvalidReferenceFormat {
                reference: reference.to_string(),
                reason: "Reference must contain a number".to_string(),
            }));
        }

        let prefix = reference[..prefix_end].to_string();
        let number_part = reference[prefix_end..].to_string();

        Ok((prefix, number_part))
    }

    /// Check if a reference follows the expected pattern for a given prefix
    pub fn matches_prefix(&self, reference: &str, expected_prefix: &str) -> bool {
        match self.parse_reference(reference) {
            Ok((prefix, _)) => prefix == expected_prefix,
            Err(_) => false,
        }
    }

    /// Extract the number from a reference
    pub fn extract_number(&self, reference: &str) -> Result<u32, ReferenceError> {
        let (_, number_part) = self.parse_reference(reference)?;
        number_part.parse::<u32>().map_err(|_| {
            ReferenceError::Validation(ValidationError::InvalidNumber {
                number_part,
            })
        })
    }

    /// Generate a reference from prefix and number
    pub fn format_reference(&self, prefix: &str, number: u32) -> Result<String, ReferenceError> {
        self.validate_prefix(prefix)?;
        
        let reference = format!("{}{}", prefix, number);
        self.validate_format(&reference)?;
        
        Ok(reference)
    }

    /// Check if a reference is a valid unnamed net reference (N$1, N$2, etc.)
    pub fn is_unnamed_net(&self, reference: &str) -> bool {
        reference.starts_with("N$") && 
        reference.len() > 2 && 
        reference[2..].chars().all(|c| c.is_numeric())
    }

    /// Add a reserved prefix
    pub fn add_reserved_prefix(&mut self, prefix: String) {
        self.reserved_prefixes.insert(prefix);
    }

    /// Add a reserved reference
    pub fn add_reserved_reference(&mut self, reference: String) {
        self.reserved_references.insert(reference);
    }

    /// Get validation statistics
    pub fn get_validation_rules(&self) -> serde_json::Value {
        serde_json::json!({
            "max_reference_length": self.max_reference_length,
            "max_prefix_length": self.max_prefix_length,
            "allowed_prefix_chars": self.allowed_prefix_chars.iter().collect::<Vec<_>>(),
            "allowed_number_chars": self.allowed_number_chars.iter().collect::<Vec<_>>(),
            "reserved_prefixes": self.reserved_prefixes.iter().collect::<Vec<_>>(),
            "reserved_references": self.reserved_references.iter().collect::<Vec<_>>()
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_references() {
        let validator = ReferenceValidator::new();
        
        assert!(validator.validate_format("R1").is_ok());
        assert!(validator.validate_format("C23").is_ok());
        assert!(validator.validate_format("U456").is_ok());
        assert!(validator.validate_format("IC1").is_ok());
        assert!(validator.validate_format("SW_1").is_ok());
    }

    #[test]
    fn test_invalid_references() {
        let validator = ReferenceValidator::new();
        
        // Empty reference
        assert!(validator.validate_format("").is_err());
        
        // No number
        assert!(validator.validate_format("R").is_err());
        
        // No prefix
        assert!(validator.validate_format("123").is_err());
        
        // Invalid characters
        assert!(validator.validate_format("R-1").is_err());
        assert!(validator.validate_format("R@1").is_err());
        
        // Reserved references
        assert!(validator.validate_format("GND").is_err());
        assert!(validator.validate_format("VCC").is_err());
    }

    #[test]
    fn test_prefix_validation() {
        let validator = ReferenceValidator::new();
        
        // Valid prefixes
        assert!(validator.validate_prefix("R").is_ok());
        assert!(validator.validate_prefix("IC").is_ok());
        assert!(validator.validate_prefix("SW_").is_ok());
        
        // Invalid prefixes
        assert!(validator.validate_prefix("").is_err());
        assert!(validator.validate_prefix("1R").is_err());
        assert!(validator.validate_prefix("R-").is_err());
        assert!(validator.validate_prefix("N$").is_err()); // Reserved
    }

    #[test]
    fn test_reference_parsing() {
        let validator = ReferenceValidator::new();
        
        let (prefix, number) = validator.parse_reference("R123").unwrap();
        assert_eq!(prefix, "R");
        assert_eq!(number, "123");
        
        let (prefix, number) = validator.parse_reference("IC_45").unwrap();
        assert_eq!(prefix, "IC_");
        assert_eq!(number, "45");
        
        // Invalid formats
        assert!(validator.parse_reference("123R").is_err());
        assert!(validator.parse_reference("R-123").is_err());
    }

    #[test]
    fn test_number_extraction() {
        let validator = ReferenceValidator::new();
        
        assert_eq!(validator.extract_number("R123").unwrap(), 123);
        assert_eq!(validator.extract_number("C1").unwrap(), 1);
        assert_eq!(validator.extract_number("U999").unwrap(), 999);
        
        // Invalid numbers
        assert!(validator.extract_number("R").is_err());
        assert!(validator.extract_number("R0123").is_ok()); // Leading zeros are ok
    }

    #[test]
    fn test_reference_formatting() {
        let validator = ReferenceValidator::new();
        
        assert_eq!(validator.format_reference("R", 1).unwrap(), "R1");
        assert_eq!(validator.format_reference("IC", 123).unwrap(), "IC123");
        
        // Invalid prefix should fail
        assert!(validator.format_reference("1R", 1).is_err());
        assert!(validator.format_reference("N$", 1).is_err());
    }

    #[test]
    fn test_unnamed_net_detection() {
        let validator = ReferenceValidator::new();
        
        assert!(validator.is_unnamed_net("N$1"));
        assert!(validator.is_unnamed_net("N$123"));
        assert!(!validator.is_unnamed_net("R1"));
        assert!(!validator.is_unnamed_net("N$"));
        assert!(!validator.is_unnamed_net("N$abc"));
    }

    #[test]
    fn test_prefix_matching() {
        let validator = ReferenceValidator::new();
        
        assert!(validator.matches_prefix("R123", "R"));
        assert!(validator.matches_prefix("IC45", "IC"));
        assert!(!validator.matches_prefix("R123", "C"));
        assert!(!validator.matches_prefix("invalid", "R"));
    }

    #[test]
    fn test_custom_validator() {
        let validator = ReferenceValidator::with_config(
            32,  // max_reference_length
            8,   // max_prefix_length
            vec!["CUSTOM".to_string()], // reserved_prefixes
            vec!["SPECIAL".to_string()], // reserved_references
        );
        
        // Custom reserved prefix should be rejected
        assert!(validator.validate_prefix("CUSTOM").is_err());
        
        // Custom reserved reference should be rejected
        assert!(validator.validate_format("SPECIAL").is_err());
        
        // Length limits should be enforced
        let long_prefix = "A".repeat(10);
        assert!(validator.validate_prefix(&long_prefix).is_err());
    }
}