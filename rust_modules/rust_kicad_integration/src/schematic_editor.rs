//! KiCad Schematic Editor Module
//!
//! This module provides functionality to load, edit, and save KiCad schematic files.
//! It allows adding components to existing schematics at specific positions.

use lexpr::{Value, parse};
use std::fs;
use std::path::Path;
use uuid::Uuid;
use crate::schematic_api::SimpleComponent;
use crate::types::SchematicError;
use log::{debug, info, warn};

/// Schematic editor for loading and modifying KiCad schematics
pub struct SchematicEditor {
    /// The parsed S-expression tree
    sexp: Value,
    /// The schematic UUID
    uuid: String,
}

impl SchematicEditor {
    /// Load a schematic from a file
    pub fn load_from_file<P: AsRef<Path>>(path: P) -> Result<Self, SchematicError> {
        let content = fs::read_to_string(path)
            .map_err(|e| SchematicError::IoError(format!("Failed to read file: {}", e)))?;
        
        Self::load_from_string(&content)
    }
    
    /// Load a schematic from a string
    pub fn load_from_string(content: &str) -> Result<Self, SchematicError> {
        let sexp = parse::from_str(content)
            .map_err(|e| SchematicError::InvalidData(format!("Failed to parse S-expression: {}", e)))?;
        
        // Extract UUID from the schematic
        let uuid = extract_uuid(&sexp)?;
        
        Ok(SchematicEditor { sexp, uuid })
    }
    
    /// Add a component to the schematic at a specific position
    pub fn add_component(&mut self, component: &SimpleComponent) -> Result<(), SchematicError> {
        info!("🔧 Adding component: {} ({})", component.reference, component.lib_id);
        
        // Create the component S-expression
        let component_sexp = create_component_sexp(component, &self.uuid)?;
        debug!("  Component S-expression created");
        
        // Convert to vector, add component, rebuild
        let mut elements = sexp_to_vec(&self.sexp)?;
        debug!("  Schematic has {} top-level elements", elements.len());
        
        // Ensure we have lib_symbols section with Device:R definition if needed
        info!("  Ensuring lib_symbols section for: {}", component.lib_id);
        ensure_lib_symbols(&mut elements, &component.lib_id);
        
        // Find position to insert (before sheet_instances or at end)
        let mut insert_pos = elements.len();
        for (i, elem) in elements.iter().enumerate() {
            if is_sheet_instances(elem) || is_embedded_fonts(elem) {
                insert_pos = i;
                break;
            }
        }
        
        // Insert the component
        elements.insert(insert_pos, component_sexp);
        
        // Ensure sheet_instances exists
        ensure_sheet_instances(&mut elements, &self.uuid);
        
        // Ensure embedded_fonts exists
        ensure_embedded_fonts(&mut elements);
        
        // Rebuild the S-expression
        self.sexp = Value::list(elements);
        
        Ok(())
    }
    
    /// Save the schematic to a file
    pub fn save_to_file<P: AsRef<Path>>(&self, path: P) -> Result<(), SchematicError> {
        let content = self.to_string();
        fs::write(path, content)
            .map_err(|e| SchematicError::IoError(format!("Failed to write file: {}", e)))?;
        Ok(())
    }
    
    /// Convert the schematic to a string with proper formatting
    pub fn to_string(&self) -> String {
        format_sexp(&self.sexp)
    }
    
    /// Get a list of all components in the schematic
    pub fn get_components(&self) -> Vec<String> {
        let mut components = Vec::new();
        extract_components(&self.sexp, &mut components);
        components
    }
}

/// Extract the UUID from a schematic S-expression
fn extract_uuid(sexp: &Value) -> Result<String, SchematicError> {
    // Convert to vector for easier processing
    let elements = sexp_to_vec(sexp)?;
    
    // Look for uuid element
    for elem in elements {
        if let Value::Cons(cons) = elem {
            if let Value::Symbol(sym) = cons.car() {
                if sym.as_ref() == "uuid" {
                    // Get the next element which should be the UUID string
                    if let Value::Cons(next) = cons.cdr() {
                        if let Value::String(uuid) = next.car() {
                            return Ok(uuid.to_string());
                        }
                    }
                }
            }
        }
    }
    
    // If no UUID found, generate a new one
    Ok(Uuid::new_v4().to_string())
}

/// Convert S-expression to vector of elements
fn sexp_to_vec(sexp: &Value) -> Result<Vec<Value>, SchematicError> {
    let mut elements = Vec::new();
    
    if let Value::Cons(cons) = sexp {
        // First element should be the symbol (kicad_sch)
        elements.push(cons.car().clone());
        
        // Collect remaining elements
        let mut current = cons.cdr();
        while let Value::Cons(c) = current {
            elements.push(c.car().clone());
            current = c.cdr();
        }
    }
    
    Ok(elements)
}

/// Check if an element is sheet_instances
fn is_sheet_instances(elem: &Value) -> bool {
    if let Value::Cons(cons) = elem {
        if let Value::Symbol(sym) = cons.car() {
            return sym.as_ref() == "sheet_instances";
        }
    }
    false
}

/// Check if an element is embedded_fonts
fn is_embedded_fonts(elem: &Value) -> bool {
    if let Value::Cons(cons) = elem {
        if let Value::Symbol(sym) = cons.car() {
            return sym.as_ref() == "embedded_fonts";
        }
    }
    false
}

/// Ensure lib_symbols section has the required symbol definition
fn ensure_lib_symbols(elements: &mut Vec<Value>, lib_id: &str) {
    use crate::kicad_library::{load_symbol_from_library, create_generic_symbol};
    
    info!("    🔍 Looking for symbol: {}", lib_id);
    
    // Get the symbol definition
    let mut symbol = if let Ok(Some(mut loaded_symbol)) = load_symbol_from_library(lib_id) {
        // Found the real symbol definition
        info!("    ✅ Using actual KiCad library symbol");
        // Fix the symbol name to be Library:Symbol format
        fix_symbol_name(&mut loaded_symbol, lib_id);
        loaded_symbol
    } else if lib_id == "Device:R" {
        // Use our hard-coded Device:R
        info!("    📎 Using hard-coded Device:R symbol");
        create_device_r_symbol()
    } else {
        // Create a generic symbol as last resort
        let pin_count = guess_pin_count(lib_id);
        warn!("    ⚠️ Creating generic symbol with {} pins", pin_count);
        create_generic_symbol(lib_id, pin_count)
    };
    
    // Find or create lib_symbols section
    for elem in elements.iter_mut() {
        if let Value::Cons(cons) = elem {
            if let Value::Symbol(sym) = cons.car() {
                if sym.as_ref() == "lib_symbols" {
                    // Found existing lib_symbols - add symbol to it if not already present
                    info!("    🔄 Updating existing lib_symbols section");
                    
                    // Check if this symbol already exists
                    let mut current = cons.cdr();
                    while let Value::Cons(c) = current {
                        if let Value::Cons(symbol_cons) = c.car() {
                            if let Value::Symbol(s) = symbol_cons.car() {
                                if s.as_ref() == "symbol" {
                                    // Check the symbol name
                                    if let Value::Cons(name_cons) = symbol_cons.cdr() {
                                        if let Value::String(name) = name_cons.car() {
                                            if name.as_ref() == lib_id {
                                                info!("    ⚠️ Symbol {} already exists, skipping", lib_id);
                                                return;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        current = c.cdr();
                    }
                    
                    // Symbol not found, add it to the existing lib_symbols
                    let mut symbols = vec![Value::symbol("lib_symbols")];
                    
                    // Collect existing symbols
                    let mut current = cons.cdr();
                    while let Value::Cons(c) = current {
                        symbols.push(c.car().clone());
                        current = c.cdr();
                    }
                    
                    // Add the new symbol
                    symbols.push(symbol);
                    
                    // Replace the element with the updated list
                    *elem = Value::list(symbols);
                    return;
                }
            }
        }
    }
    
    // No lib_symbols found, create it
    info!("    ➕ Creating new lib_symbols section");
    let lib_symbols = Value::list(vec![
        Value::symbol("lib_symbols"),
        symbol,
    ]);
    
    // Find position to insert (after paper, before first symbol)
    let mut insert_pos = 0;
    for (i, elem) in elements.iter().enumerate() {
        if let Value::Cons(cons) = elem {
            if let Value::Symbol(sym) = cons.car() {
                if sym.as_ref() == "paper" {
                    insert_pos = i + 1;
                } else if sym.as_ref() == "symbol" {
                    break;
                }
            }
        }
    }
    
    elements.insert(insert_pos, lib_symbols);
}

/// Fix the symbol name to be in Library:Symbol format
fn fix_symbol_name(symbol: &mut Value, lib_id: &str) {
    // The symbol is a list starting with (symbol "name" ...)
    // We need to change the name to be the full Library:Symbol format
    if let Value::Cons(cons) = symbol {
        let mut current = cons.cdr();
        if let Value::Cons(name_cons) = current {
            if let Value::String(_) = name_cons.car() {
                // Replace the name with the full lib_id
                let mut new_items = vec![Value::symbol("symbol"), Value::string(lib_id)];
                
                // Collect the rest of the items
                let mut rest = name_cons.cdr();
                while let Value::Cons(c) = rest {
                    new_items.push(c.car().clone());
                    rest = c.cdr();
                }
                
                // Rebuild the symbol with the corrected name
                *symbol = Value::list(new_items);
                debug!("    Fixed symbol name to: {}", lib_id);
            }
        }
    }
}

/// Guess the number of pins for a component based on its lib_id
fn guess_pin_count(lib_id: &str) -> usize {
    if lib_id.contains(":R") || lib_id.contains(":C") || lib_id.contains(":L") {
        2  // Passive components typically have 2 pins
    } else if lib_id.contains(":LED") || lib_id.contains(":D") {
        2  // Diodes have 2 pins
    } else if lib_id.contains("_NPN") || lib_id.contains("_PNP") || lib_id.contains(":Q") {
        3  // Transistors typically have 3 pins
    } else {
        4  // Default to 4 pins for ICs
    }
}

/// Create Device:R symbol definition (without lib_symbols wrapper)
fn create_device_r_symbol() -> Value {
    debug!("    Creating Device:R symbol definition");
    Value::list(vec![
        Value::symbol("symbol"),
        Value::string("Device:R"),
        Value::list(vec![
            Value::symbol("pin_numbers"),
            Value::list(vec![Value::symbol("hide"), Value::symbol("yes")]),
        ]),
        Value::list(vec![
            Value::symbol("pin_names"),
            Value::list(vec![Value::symbol("offset"), Value::from(0)]),
        ]),
        Value::list(vec![Value::symbol("exclude_from_sim"), Value::symbol("no")]),
        Value::list(vec![Value::symbol("in_bom"), Value::symbol("yes")]),
        Value::list(vec![Value::symbol("on_board"), Value::symbol("yes")]),
        Value::list(vec![
            Value::symbol("property"),
            Value::string("Reference"),
            Value::string("R"),
            Value::list(vec![Value::symbol("at"), Value::from(2.032), Value::from(0), Value::from(90)]),
            Value::list(vec![
                Value::symbol("effects"),
                Value::list(vec![
                    Value::symbol("font"),
                    Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                ]),
            ]),
        ]),
        Value::list(vec![
            Value::symbol("property"),
            Value::string("Value"),
            Value::string("R"),
            Value::list(vec![Value::symbol("at"), Value::from(0), Value::from(0), Value::from(90)]),
            Value::list(vec![
                Value::symbol("effects"),
                Value::list(vec![
                    Value::symbol("font"),
                    Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                ]),
            ]),
        ]),
        Value::list(vec![
            Value::symbol("property"),
            Value::string("Footprint"),
            Value::string(""),
            Value::list(vec![Value::symbol("at"), Value::from(-1.778), Value::from(0), Value::from(90)]),
            Value::list(vec![
                Value::symbol("effects"),
                Value::list(vec![
                    Value::symbol("font"),
                    Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                ]),
                Value::list(vec![Value::symbol("hide"), Value::symbol("yes")]),
            ]),
        ]),
        Value::list(vec![
            Value::symbol("property"),
            Value::string("Datasheet"),
            Value::string("~"),
            Value::list(vec![Value::symbol("at"), Value::from(0), Value::from(0), Value::from(0)]),
            Value::list(vec![
                Value::symbol("effects"),
                Value::list(vec![
                    Value::symbol("font"),
                    Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                ]),
                Value::list(vec![Value::symbol("hide"), Value::symbol("yes")]),
            ]),
        ]),
        Value::list(vec![
            Value::symbol("property"),
            Value::string("Description"),
            Value::string("Resistor"),
            Value::list(vec![Value::symbol("at"), Value::from(0), Value::from(0), Value::from(0)]),
            Value::list(vec![
                Value::symbol("effects"),
                Value::list(vec![
                    Value::symbol("font"),
                    Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                ]),
                Value::list(vec![Value::symbol("hide"), Value::symbol("yes")]),
            ]),
        ]),
        Value::list(vec![
            Value::symbol("property"),
            Value::string("ki_keywords"),
            Value::string("R res resistor"),
            Value::list(vec![Value::symbol("at"), Value::from(0), Value::from(0), Value::from(0)]),
            Value::list(vec![
                Value::symbol("effects"),
                Value::list(vec![
                    Value::symbol("font"),
                    Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                ]),
                Value::list(vec![Value::symbol("hide"), Value::symbol("yes")]),
            ]),
        ]),
        Value::list(vec![
            Value::symbol("property"),
            Value::string("ki_fp_filters"),
            Value::string("R_*"),
            Value::list(vec![Value::symbol("at"), Value::from(0), Value::from(0), Value::from(0)]),
            Value::list(vec![
                Value::symbol("effects"),
                Value::list(vec![
                    Value::symbol("font"),
                    Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                ]),
                Value::list(vec![Value::symbol("hide"), Value::symbol("yes")]),
            ]),
        ]),
        Value::list(vec![
            Value::symbol("symbol"),
            Value::string("R_0_1"),
            Value::list(vec![
                Value::symbol("rectangle"),
                Value::list(vec![Value::symbol("start"), Value::from(-1.016), Value::from(-2.54)]),
                Value::list(vec![Value::symbol("end"), Value::from(1.016), Value::from(2.54)]),
                Value::list(vec![
                    Value::symbol("stroke"),
                    Value::list(vec![Value::symbol("width"), Value::from(0.254)]),
                    Value::list(vec![Value::symbol("type"), Value::symbol("default")]),
                ]),
                Value::list(vec![
                    Value::symbol("fill"),
                    Value::list(vec![Value::symbol("type"), Value::symbol("none")]),
                ]),
            ]),
        ]),
        Value::list(vec![
            Value::symbol("symbol"),
            Value::string("R_1_1"),
            Value::list(vec![
                Value::symbol("pin"),
                Value::symbol("passive"),
                Value::symbol("line"),
                Value::list(vec![Value::symbol("at"), Value::from(0), Value::from(3.81), Value::from(270)]),
                Value::list(vec![Value::symbol("length"), Value::from(1.27)]),
                Value::list(vec![
                    Value::symbol("name"),
                    Value::string("~"),
                    Value::list(vec![
                        Value::symbol("effects"),
                        Value::list(vec![
                            Value::symbol("font"),
                            Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                        ]),
                    ]),
                ]),
                Value::list(vec![
                    Value::symbol("number"),
                    Value::string("1"),
                    Value::list(vec![
                        Value::symbol("effects"),
                        Value::list(vec![
                            Value::symbol("font"),
                            Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                        ]),
                    ]),
                ]),
            ]),
            Value::list(vec![
                Value::symbol("pin"),
                Value::symbol("passive"),
                Value::symbol("line"),
                Value::list(vec![Value::symbol("at"), Value::from(0), Value::from(-3.81), Value::from(90)]),
                Value::list(vec![Value::symbol("length"), Value::from(1.27)]),
                Value::list(vec![
                    Value::symbol("name"),
                    Value::string("~"),
                    Value::list(vec![
                        Value::symbol("effects"),
                        Value::list(vec![
                            Value::symbol("font"),
                            Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                        ]),
                    ]),
                ]),
                Value::list(vec![
                    Value::symbol("number"),
                    Value::string("2"),
                    Value::list(vec![
                        Value::symbol("effects"),
                        Value::list(vec![
                            Value::symbol("font"),
                            Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                        ]),
                    ]),
                ]),
            ]),
        ]),
    ])
}

/// Create Device:R library symbol definition
fn create_device_r_lib_symbols() -> Value {
    Value::list(vec![
        Value::symbol("lib_symbols"),
        Value::list(vec![
            Value::symbol("symbol"),
            Value::string("Device:R"),
            Value::list(vec![
                Value::symbol("pin_numbers"),
                Value::list(vec![Value::symbol("hide"), Value::symbol("yes")]),
            ]),
            Value::list(vec![
                Value::symbol("pin_names"),
                Value::list(vec![Value::symbol("offset"), Value::from(0)]),
            ]),
            Value::list(vec![Value::symbol("exclude_from_sim"), Value::symbol("no")]),
            Value::list(vec![Value::symbol("in_bom"), Value::symbol("yes")]),
            Value::list(vec![Value::symbol("on_board"), Value::symbol("yes")]),
            Value::list(vec![
                Value::symbol("property"),
                Value::string("Reference"),
                Value::string("R"),
                Value::list(vec![Value::symbol("at"), Value::from(2.032), Value::from(0), Value::from(90)]),
                Value::list(vec![
                    Value::symbol("effects"),
                    Value::list(vec![
                        Value::symbol("font"),
                        Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                    ]),
                ]),
            ]),
            Value::list(vec![
                Value::symbol("property"),
                Value::string("Value"),
                Value::string("R"),
                Value::list(vec![Value::symbol("at"), Value::from(0), Value::from(0), Value::from(90)]),
                Value::list(vec![
                    Value::symbol("effects"),
                    Value::list(vec![
                        Value::symbol("font"),
                        Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                    ]),
                ]),
            ]),
            Value::list(vec![
                Value::symbol("property"),
                Value::string("Footprint"),
                Value::string(""),
                Value::list(vec![Value::symbol("at"), Value::from(-1.778), Value::from(0), Value::from(90)]),
                Value::list(vec![
                    Value::symbol("effects"),
                    Value::list(vec![
                        Value::symbol("font"),
                        Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                    ]),
                    Value::list(vec![Value::symbol("hide"), Value::symbol("yes")]),
                ]),
            ]),
            Value::list(vec![
                Value::symbol("property"),
                Value::string("Datasheet"),
                Value::string("~"),
                Value::list(vec![Value::symbol("at"), Value::from(0), Value::from(0), Value::from(0)]),
                Value::list(vec![
                    Value::symbol("effects"),
                    Value::list(vec![
                        Value::symbol("font"),
                        Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                    ]),
                    Value::list(vec![Value::symbol("hide"), Value::symbol("yes")]),
                ]),
            ]),
            Value::list(vec![
                Value::symbol("property"),
                Value::string("Description"),
                Value::string("Resistor"),
                Value::list(vec![Value::symbol("at"), Value::from(0), Value::from(0), Value::from(0)]),
                Value::list(vec![
                    Value::symbol("effects"),
                    Value::list(vec![
                        Value::symbol("font"),
                        Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                    ]),
                    Value::list(vec![Value::symbol("hide"), Value::symbol("yes")]),
                ]),
            ]),
            Value::list(vec![
                Value::symbol("property"),
                Value::string("ki_keywords"),
                Value::string("R res resistor"),
                Value::list(vec![Value::symbol("at"), Value::from(0), Value::from(0), Value::from(0)]),
                Value::list(vec![
                    Value::symbol("effects"),
                    Value::list(vec![
                        Value::symbol("font"),
                        Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                    ]),
                    Value::list(vec![Value::symbol("hide"), Value::symbol("yes")]),
                ]),
            ]),
            Value::list(vec![
                Value::symbol("property"),
                Value::string("ki_fp_filters"),
                Value::string("R_*"),
                Value::list(vec![Value::symbol("at"), Value::from(0), Value::from(0), Value::from(0)]),
                Value::list(vec![
                    Value::symbol("effects"),
                    Value::list(vec![
                        Value::symbol("font"),
                        Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                    ]),
                    Value::list(vec![Value::symbol("hide"), Value::symbol("yes")]),
                ]),
            ]),
            Value::list(vec![
                Value::symbol("symbol"),
                Value::string("R_0_1"),
                Value::list(vec![
                    Value::symbol("rectangle"),
                    Value::list(vec![Value::symbol("start"), Value::from(-1.016), Value::from(-2.54)]),
                    Value::list(vec![Value::symbol("end"), Value::from(1.016), Value::from(2.54)]),
                    Value::list(vec![
                        Value::symbol("stroke"),
                        Value::list(vec![Value::symbol("width"), Value::from(0.254)]),
                        Value::list(vec![Value::symbol("type"), Value::symbol("default")]),
                    ]),
                    Value::list(vec![
                        Value::symbol("fill"),
                        Value::list(vec![Value::symbol("type"), Value::symbol("none")]),
                    ]),
                ]),
            ]),
            Value::list(vec![
                Value::symbol("symbol"),
                Value::string("R_1_1"),
                Value::list(vec![
                    Value::symbol("pin"),
                    Value::symbol("passive"),
                    Value::symbol("line"),
                    Value::list(vec![Value::symbol("at"), Value::from(0), Value::from(3.81), Value::from(270)]),
                    Value::list(vec![Value::symbol("length"), Value::from(1.27)]),
                    Value::list(vec![
                        Value::symbol("name"),
                        Value::string("~"),
                        Value::list(vec![
                            Value::symbol("effects"),
                            Value::list(vec![
                                Value::symbol("font"),
                                Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                            ]),
                        ]),
                    ]),
                    Value::list(vec![
                        Value::symbol("number"),
                        Value::string("1"),
                        Value::list(vec![
                            Value::symbol("effects"),
                            Value::list(vec![
                                Value::symbol("font"),
                                Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                            ]),
                        ]),
                    ]),
                ]),
                Value::list(vec![
                    Value::symbol("pin"),
                    Value::symbol("passive"),
                    Value::symbol("line"),
                    Value::list(vec![Value::symbol("at"), Value::from(0), Value::from(-3.81), Value::from(90)]),
                    Value::list(vec![Value::symbol("length"), Value::from(1.27)]),
                    Value::list(vec![
                        Value::symbol("name"),
                        Value::string("~"),
                        Value::list(vec![
                            Value::symbol("effects"),
                            Value::list(vec![
                                Value::symbol("font"),
                                Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                            ]),
                        ]),
                    ]),
                    Value::list(vec![
                        Value::symbol("number"),
                        Value::string("2"),
                        Value::list(vec![
                            Value::symbol("effects"),
                            Value::list(vec![
                                Value::symbol("font"),
                                Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                            ]),
                        ]),
                    ]),
                ]),
            ]),
            Value::list(vec![Value::symbol("embedded_fonts"), Value::symbol("no")]),
        ]),
    ])
}

/// Ensure sheet_instances exists
fn ensure_sheet_instances(elements: &mut Vec<Value>, uuid: &str) {
    // Check if sheet_instances already exists
    for elem in elements.iter() {
        if is_sheet_instances(elem) {
            return;
        }
    }
    
    // Add sheet_instances before embedded_fonts or at end
    let sheet_instances = Value::list(vec![
        Value::symbol("sheet_instances"),
        Value::list(vec![
            Value::symbol("path"),
            Value::string("/"),
            Value::list(vec![Value::symbol("page"), Value::string("1")]),
        ]),
    ]);
    
    // Find position to insert (before embedded_fonts or at end)
    let mut insert_pos = elements.len();
    for (i, elem) in elements.iter().enumerate() {
        if is_embedded_fonts(elem) {
            insert_pos = i;
            break;
        }
    }
    
    elements.insert(insert_pos, sheet_instances);
}

/// Ensure embedded_fonts exists
fn ensure_embedded_fonts(elements: &mut Vec<Value>) {
    // Check if embedded_fonts already exists
    for elem in elements.iter() {
        if is_embedded_fonts(elem) {
            return;
        }
    }
    
    // Add at end with proper formatting
    elements.push(Value::list(vec![Value::symbol("embedded_fonts"), Value::symbol("no")]));
}

/// Create a component S-expression
fn create_component_sexp(component: &SimpleComponent, schematic_uuid: &str) -> Result<Value, SchematicError> {
    let component_uuid = Uuid::new_v4().to_string();
    debug!("  Creating component sexp: ref={}, lib_id={}, pos=({},{})", 
           component.reference, component.lib_id, component.x, component.y);
    
    // Build the component as a Value::list
    let component_sexp = Value::list(vec![
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
        Value::list(vec![Value::symbol("uuid"), Value::string(component_uuid.clone())]),
        Value::list(vec![
            Value::symbol("property"),
            Value::string("Reference"),
            Value::string(component.reference.clone()),
            Value::list(vec![
                Value::symbol("at"),
                Value::from(component.x + 2.54),
                Value::from(component.y - 3.81),
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
                Value::from(component.x + 2.54),
                Value::from(component.y + 2.54),
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
        // Add Footprint property  
        Value::list(vec![
            Value::symbol("property"),
            Value::string("Footprint"),
            Value::string(component.footprint.clone().unwrap_or_else(|| "Resistor_SMD:R_0603_1608Metric".to_string())),
            Value::list(vec![
                Value::symbol("at"),
                Value::from(component.x - 1.778),
                Value::from(component.y),
                Value::from(90),
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
                Value::list(vec![Value::symbol("hide"), Value::symbol("yes")]),
            ]),
        ]),
        // Add Datasheet property
        Value::list(vec![
            Value::symbol("property"),
            Value::string("Datasheet"),
            Value::string("~"),
            Value::list(vec![
                Value::symbol("at"),
                Value::from(component.x),
                Value::from(component.y),
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
                Value::list(vec![Value::symbol("hide"), Value::symbol("yes")]),
            ]),
        ]),
        // Add Description property
        Value::list(vec![
            Value::symbol("property"),
            Value::string("Description"),
            Value::string("Resistor"),
            Value::list(vec![
                Value::symbol("at"),
                Value::from(component.x),
                Value::from(component.y),
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
                Value::list(vec![Value::symbol("hide"), Value::symbol("yes")]),
            ]),
        ]),
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
        Value::list(vec![
            Value::symbol("instances"),
            Value::list(vec![
                Value::symbol("project"),
                Value::string("kicad_reference"),  // Use kicad_reference as project name
                Value::list(vec![
                    Value::symbol("path"),
                    Value::string(format!("/{}", schematic_uuid)),
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
    
    Ok(component_sexp)
}


/// Format an S-expression with proper indentation for KiCad
fn format_sexp(sexp: &Value) -> String {
    let mut result = String::new();
    format_sexp_inner(sexp, &mut result, 0);
    result
}

/// Inner recursive function for formatting S-expressions
fn format_sexp_inner(sexp: &Value, output: &mut String, indent: usize) {
    let indent_str = "\t".repeat(indent);
    
    match sexp {
        Value::Cons(cons) => {
            output.push('(');
            
            // Check if first element is a symbol to determine formatting
            if let Value::Symbol(sym) = cons.car() {
                output.push_str(sym.as_ref());
                
                // Check if this is a simple expression
                let mut rest = cons.cdr();
                
                // Special handling for specific keywords
                let keyword = sym.as_ref();
                
                // Keywords that should have their first argument on the same line
                let same_line_keywords = ["pin", "property", "symbol", "project", "path"];
                
                // Keywords that are always simple (stay on one line)
                let simple_keywords = ["at", "size", "uuid", "unit", "hide", "offset", 
                                       "justify", "reference", "page", "version", 
                                       "generator", "generator_version", "paper",
                                       "exclude_from_sim", "in_bom", "on_board", "dnp",
                                       "fields_autoplaced", "lib_id", "width", "type",
                                       "length", "start", "end", "fill", "stroke"];
                
                if simple_keywords.contains(&keyword) {
                    // Format inline - everything on same line
                    while let Value::Cons(c) = rest {
                        output.push(' ');
                        format_sexp_value(c.car(), output);
                        rest = c.cdr();
                    }
                } else if same_line_keywords.contains(&keyword) {
                    // First argument on same line, rest indented
                    if let Value::Cons(first_cons) = rest {
                        // First argument on same line
                        output.push(' ');
                        format_sexp_value(first_cons.car(), output);
                        
                        // Rest on new lines
                        let mut remaining = first_cons.cdr();
                        while let Value::Cons(c) = remaining {
                            output.push('\n');
                            output.push_str(&"\t".repeat(indent + 1));
                            format_sexp_inner(c.car(), output, indent + 1);
                            remaining = c.cdr();
                        }
                    }
                    output.push('\n');
                    output.push_str(&indent_str);
                } else {
                    // Default: Format with newlines for each element
                    while let Value::Cons(c) = rest {
                        output.push('\n');
                        output.push_str(&"\t".repeat(indent + 1));
                        format_sexp_inner(c.car(), output, indent + 1);
                        rest = c.cdr();
                    }
                    output.push('\n');
                    output.push_str(&indent_str);
                }
            } else {
                // Not a symbol-led list
                format_sexp_inner(cons.car(), output, indent);
                let mut rest = cons.cdr();
                while let Value::Cons(c) = rest {
                    output.push(' ');
                    format_sexp_inner(c.car(), output, indent);
                    rest = c.cdr();
                }
            }
            
            output.push(')');
        }
        _ => format_sexp_value(sexp, output),
    }
}

/// Format a simple S-expression value
fn format_sexp_value(value: &Value, output: &mut String) {
    match value {
        Value::Symbol(s) => output.push_str(s.as_ref()),
        Value::String(s) => {
            output.push('"');
            output.push_str(s);
            output.push('"');
        }
        Value::Number(n) => {
            if n.is_i64() {
                output.push_str(&n.as_i64().unwrap().to_string());
            } else if n.is_u64() {
                output.push_str(&n.as_u64().unwrap().to_string());
            } else {
                output.push_str(&n.as_f64().unwrap().to_string());
            }
        }
        Value::Bool(b) => output.push_str(if *b { "yes" } else { "no" }),
        Value::Null => {},
        Value::Cons(_) => {
            // Nested list - recurse
            format_sexp_inner(value, output, 0);
        }
        _ => {
            // Fallback to lexpr's to_string for other types
            output.push_str(&lexpr::to_string(value).unwrap_or_default());
        }
    }
}

/// Extract component references from the schematic
fn extract_components(sexp: &Value, components: &mut Vec<String>) {
    if let Value::Cons(cons) = sexp {
        // Check if this is a symbol element
        if let Value::Symbol(sym) = cons.car() {
            if sym.as_ref() == "symbol" {
                // Try to extract the reference
                if let Some(reference) = extract_reference_from_symbol(cons) {
                    components.push(reference);
                }
            }
        }
        
        // Recursively check all elements
        extract_components(cons.car(), components);
        let mut current = cons.cdr();
        while let Value::Cons(c) = current {
            extract_components(c.car(), components);
            current = c.cdr();
        }
    }
}

/// Extract the reference from a symbol element
fn extract_reference_from_symbol(symbol: &lexpr::Cons) -> Option<String> {
    let mut current = symbol.cdr();
    
    while let Value::Cons(item) = current {
        if let Value::Symbol(sym) = item.car() {
            if sym.as_ref() == "property" {
                // Check if this is the Reference property
                if let Value::Cons(prop_cons) = item.cdr() {
                    if let Value::String(prop_name) = prop_cons.car() {
                        if prop_name.as_ref() == "Reference" {
                            // Get the value
                            if let Value::Cons(val_cons) = prop_cons.cdr() {
                                if let Value::String(ref_value) = val_cons.car() {
                                    return Some(ref_value.to_string());
                                }
                            }
                        }
                    }
                }
            }
        }
        current = item.cdr();
    }
    
    None
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_load_and_add_component() {
        // Create a minimal schematic first
        let minimal = "(kicad_sch (version 20250114) (generator \"test\") (uuid \"test-uuid\") (paper \"A4\") (lib_symbols) (sheet_instances (path \"/\" (page \"1\"))))";
        
        // Load it
        let mut editor = SchematicEditor::load_from_string(minimal).unwrap();
        
        // Add a component
        let component = SimpleComponent {
            reference: "R1".to_string(),
            lib_id: "Device:R".to_string(),
            value: "10k".to_string(),
            x: 100.0,
            y: 50.0,
            rotation: 0.0,
            footprint: Some("Resistor_SMD:R_0603_1608Metric".to_string()),
        };
        
        editor.add_component(&component).unwrap();
        
        // Check that the component was added
        let result = editor.to_string();
        assert!(result.contains("\"R1\""));
        assert!(result.contains("\"10k\""));
        assert!(result.contains("(at 100"));
    }
}