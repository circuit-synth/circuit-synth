//! Simple API for creating KiCad schematics
//!
//! This module provides a clean, minimal API for generating new KiCad schematic files.
//! It's designed to be the easiest entry point for users who want to quickly create
//! valid KiCad schematics without dealing with the complexity of the full API.
//!
//! # Examples
//!
//! ```rust
//! use rust_kicad_schematic_writer::schematic_api::*;
//!
//! // Create a minimal schematic
//! let schematic = create_minimal_schematic();
//!
//! // Create with specific paper size
//! let a3_schematic = create_empty_schematic("A3");
//! ```

use lexpr::Value;
use uuid::Uuid;

/// A simple component structure for the API
///
/// This provides a simplified interface for defining components
/// without needing to understand the full complexity of the Component struct.
///
/// # Fields
/// * `reference` - Component reference designator (e.g., "R1", "U2")
/// * `lib_id` - KiCad library ID (e.g., "Device:R", "MCU_ST:STM32F103")
/// * `value` - Component value or part number
/// * `x`, `y` - Position in millimeters
/// * `rotation` - Rotation in degrees (0, 90, 180, 270)
#[derive(Debug, Clone)]
pub struct SimpleComponent {
    pub reference: String,
    pub lib_id: String,
    pub value: String,
    pub x: f64,
    pub y: f64,
    pub rotation: f64,
    pub footprint: Option<String>,
}

/// Create a new, empty KiCad schematic
///
/// Generates a minimal but valid KiCad schematic file with the specified paper size.
///
/// # Arguments
/// * `paper_size` - Paper size ("A4", "A3", "A2", "A1", "A0", "Letter", "Legal")
///
/// # Returns
/// A string containing the complete KiCad schematic in S-expression format
///
/// # Example
/// ```rust
/// use rust_kicad_schematic_writer::schematic_api::create_empty_schematic;
/// 
/// let schematic = create_empty_schematic("A3");
/// std::fs::write("empty.kicad_sch", schematic).unwrap();
/// ```
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
    ]);
    
    lexpr::to_string(&schematic).unwrap()
}

/// Create a minimal KiCad schematic with basic structure
///
/// Convenience function that creates an A4-sized empty schematic.
/// Equivalent to calling `create_empty_schematic("A4")`.
///
/// # Returns
/// A string containing a minimal A4 KiCad schematic
///
/// # Example
/// ```rust
/// use rust_kicad_schematic_writer::schematic_api::create_minimal_schematic;
/// 
/// let schematic = create_minimal_schematic();
/// assert!(schematic.contains("(paper \"A4\")"));
/// ```
pub fn create_minimal_schematic() -> String {
    create_empty_schematic("A4")
}

/// Create a KiCad schematic with components
///
/// Generates a complete KiCad schematic file with the specified components.
/// Components will be placed at their specified positions with proper
/// reference designators and values.
///
/// # Arguments
/// * `paper_size` - Paper size for the schematic
/// * `components` - Vector of components to place in the schematic
///
/// # Returns
/// A string containing the complete KiCad schematic with components
///
/// # Note
/// This function is currently in development and may not generate
/// all component properties correctly.
pub fn create_schematic_with_components(paper_size: &str, components: Vec<SimpleComponent>) -> String {
    let uuid = Uuid::new_v4().to_string();
    
    // Build the complete schematic
    let mut schematic_elements = vec![
        Value::symbol("kicad_sch"),
        Value::list(vec![Value::symbol("version"), Value::from(20250114)]),
        Value::list(vec![Value::symbol("generator"), Value::string("circuit_synth")]),
        Value::list(vec![Value::symbol("generator_version"), Value::string("1.0")]),
        Value::list(vec![Value::symbol("uuid"), Value::string(uuid.clone())]),
        Value::list(vec![Value::symbol("paper"), Value::string(paper_size)]),
    ];
    
    // Add empty lib_symbols section (library definitions would go here)
    // For now we assume Device:R and other standard symbols are known to KiCad
    schematic_elements.push(Value::list(vec![Value::symbol("lib_symbols")]));
    
    // Add each component as a symbol instance
    for component in &components {
        let symbol_uuid = Uuid::new_v4().to_string();
        let symbol = Value::list(vec![
            Value::symbol("symbol"),
            Value::list(vec![
                Value::symbol("lib_id"),
                Value::string(component.lib_id.clone()),
            ]),
            Value::list(vec![
                Value::symbol("at"),
                Value::from(component.x),
                Value::from(component.y),
                Value::from(component.rotation),
            ]),
            Value::list(vec![Value::symbol("unit"), Value::from(1)]),
            Value::list(vec![Value::symbol("exclude_from_sim"), Value::symbol("no")]),
            Value::list(vec![Value::symbol("in_bom"), Value::symbol("yes")]),
            Value::list(vec![Value::symbol("on_board"), Value::symbol("yes")]),
            Value::list(vec![Value::symbol("dnp"), Value::symbol("no")]),
            Value::list(vec![Value::symbol("fields_autoplaced"), Value::symbol("yes")]),
            Value::list(vec![Value::symbol("uuid"), Value::string(symbol_uuid.clone())]),
            Value::list(vec![
                Value::symbol("property"),
                Value::string("Reference"),
                Value::string(component.reference.clone()),
                Value::list(vec![
                    Value::symbol("at"),
                    Value::from(component.x + 2.54),  // Offset to the right
                    Value::from(component.y - 1.27),  // Slight offset up
                    Value::from(0),
                ]),
                Value::list(vec![
                    Value::symbol("effects"),
                    Value::list(vec![
                        Value::symbol("font"),
                        Value::list(vec![
                            Value::symbol("size"),
                            Value::from(1.27),
                            Value::from(1.27),
                        ]),
                    ]),
                    Value::list(vec![Value::symbol("justify"), Value::symbol("left")]),
                ]),
            ]),
            Value::list(vec![
                Value::symbol("property"),
                Value::string("Value"),
                Value::string(component.value.clone()),
                Value::list(vec![
                    Value::symbol("at"),
                    Value::from(component.x + 2.54),  // Offset to the right
                    Value::from(component.y + 1.27),  // Slight offset down
                    Value::from(0),
                ]),
                Value::list(vec![
                    Value::symbol("effects"),
                    Value::list(vec![
                        Value::symbol("font"),
                        Value::list(vec![
                            Value::symbol("size"),
                            Value::from(1.27),
                            Value::from(1.27),
                        ]),
                    ]),
                    Value::list(vec![Value::symbol("justify"), Value::symbol("left")]),
                ]),
            ]),
            // Add pins
            Value::list(vec![
                Value::symbol("pin"),
                Value::string("1"),
                Value::list(vec![
                    Value::symbol("uuid"),
                    Value::string(Uuid::new_v4().to_string()),
                ]),
            ]),
            Value::list(vec![
                Value::symbol("pin"),
                Value::string("2"),
                Value::list(vec![
                    Value::symbol("uuid"),
                    Value::string(Uuid::new_v4().to_string()),
                ]),
            ]),
            // Add instances section
            Value::list(vec![
                Value::symbol("instances"),
                Value::list(vec![
                    Value::symbol("project"),
                    Value::string("circuit_synth"),
                    Value::list(vec![
                        Value::symbol("path"),
                        Value::string(format!("/{}", uuid)),
                        Value::list(vec![
                            Value::symbol("reference"),
                            Value::string(component.reference.clone()),
                        ]),
                        Value::list(vec![
                            Value::symbol("unit"),
                            Value::from(1),
                        ]),
                    ]),
                ]),
            ]),
        ]);
        schematic_elements.push(symbol);
    }
    
    // Add sheet_instances section
    schematic_elements.push(Value::list(vec![
        Value::symbol("sheet_instances"),
        Value::list(vec![
            Value::symbol("path"),
            Value::string("/"),
            Value::list(vec![
                Value::symbol("page"),
                Value::string("1"),
            ]),
        ]),
    ]));
    
    let schematic = Value::list(schematic_elements);
    lexpr::to_string(&schematic).unwrap()
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