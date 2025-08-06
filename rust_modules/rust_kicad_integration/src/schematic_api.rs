//! Simple API for creating KiCad schematics
//!
//! This module provides a clean, minimal API for generating new KiCad schematic files.

use lexpr::{sexp, Value};
use uuid::Uuid;

/// Create a new, empty KiCad schematic
pub fn create_empty_schematic(paper_size: &str) -> String {
    let uuid = Uuid::new_v4().to_string();
    
    // Build using Value::list for proper control
    let schematic = Value::list(vec![
        Value::symbol("kicad_sch"),
        Value::list(vec![Value::symbol("version"), Value::from(20250114)]),
        Value::list(vec![Value::symbol("generator"), Value::string("circuit_synth")]),
        Value::list(vec![Value::symbol("generator_version"), Value::string("1.0")]),
        Value::list(vec![Value::symbol("uuid"), Value::string(uuid)]),
        Value::list(vec![Value::symbol("paper"), Value::string(paper_size)]),
        Value::list(vec![Value::symbol("lib_symbols")]),
        Value::list(vec![Value::symbol("symbol_instances")]),
    ]);
    
    lexpr::to_string(&schematic).unwrap()
}

/// Create a minimal KiCad schematic with basic structure
pub fn create_minimal_schematic() -> String {
    create_empty_schematic("A4")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_minimal_schematic() {
        let schematic = create_minimal_schematic();
        
        // Check it has all required elements
        assert!(schematic.contains("kicad_sch"));
        assert!(schematic.contains("version"));
        assert!(schematic.contains("generator"));
        assert!(schematic.contains("paper"));
        assert!(schematic.contains("lib_symbols"));
        assert!(schematic.contains("symbol_instances"));
        
        // Check no dotted pairs
        assert!(!schematic.contains(". \""));
    }
    
    #[test]
    fn test_custom_paper_size() {
        let schematic = create_empty_schematic("A3");
        assert!(schematic.contains("\"A3\""));
    }
}