//! KiCad Symbol Library Parser
//! 
//! This module provides functionality to search and parse KiCad symbol libraries
//! to extract symbol definitions for inclusion in schematics.

use std::fs;
use std::path::{Path, PathBuf};
use lexpr::{Value, parse};
use crate::types::SchematicError;
use log::{debug, info, warn};

/// Common KiCad library paths on different systems (same as Python implementation)
const KICAD_LIBRARY_PATHS: &[&str] = &[
    // macOS
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols",
    "/Library/Application Support/kicad/symbols",
    // Linux (KiCad 6+)
    "/usr/share/kicad/symbols",
    "/usr/local/share/kicad/symbols",
    // Linux (KiCad 5)
    "/usr/share/kicad/library",
    "/usr/local/share/kicad/library",
    // macOS Homebrew
    "/opt/homebrew/Caskroom/kicad/*/KiCad.app/Contents/SharedSupport/symbols",
    "/usr/local/Caskroom/kicad/*/KiCad.app/Contents/SharedSupport/symbols",
    // Windows
    "C:\\Program Files\\KiCad\\share\\kicad\\symbols",
    "C:\\Program Files (x86)\\KiCad\\share\\kicad\\symbols",
];

/// Find the KiCad symbol library path on the current system
pub fn find_kicad_library_path() -> Option<PathBuf> {
    info!("🔍 Searching for KiCad symbol library paths...");
    
    for path in KICAD_LIBRARY_PATHS {
        let p = Path::new(path);
        debug!("  Checking path: {}", path);
        if p.exists() && p.is_dir() {
            info!("✅ Found KiCad library at: {}", path);
            return Some(p.to_path_buf());
        }
        
        // Handle wildcards in paths (for Homebrew installations)
        if path.contains('*') {
            if let Some(parent) = Path::new(path).parent() {
                if let Some(pattern) = Path::new(path).file_name() {
                    if let Ok(entries) = fs::read_dir(parent) {
                        for entry in entries.flatten() {
                            let full_path = entry.path().join("KiCad.app/Contents/SharedSupport/symbols");
                            if full_path.exists() && full_path.is_dir() {
                                return Some(full_path);
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Try to find via environment variable
    if let Ok(kicad_path) = std::env::var("KICAD_SYMBOL_DIR") {
        debug!("  Checking KICAD_SYMBOL_DIR: {}", kicad_path);
        let p = Path::new(&kicad_path);
        if p.exists() && p.is_dir() {
            info!("✅ Found KiCad library via env var: {}", kicad_path);
            return Some(p.to_path_buf());
        }
    }
    
    warn!("⚠️ No KiCad symbol library path found on system");
    None
}

/// Load a symbol definition from KiCad libraries
/// 
/// # Arguments
/// * `lib_id` - Library ID in format "Library:Symbol" (e.g., "Device:R", "Device:C")
/// 
/// # Returns
/// The symbol S-expression as a Value, or None if not found
pub fn load_symbol_from_library(lib_id: &str) -> Result<Option<Value>, SchematicError> {
    info!("🔎 Loading symbol from library: {}", lib_id);
    
    // Parse lib_id to get library and symbol names
    let parts: Vec<&str> = lib_id.split(':').collect();
    if parts.len() != 2 {
        return Err(SchematicError::InvalidData(
            format!("Invalid lib_id format: {}. Expected 'Library:Symbol'", lib_id)
        ));
    }
    
    let library_name = parts[0];
    let symbol_name = parts[1];
    debug!("  Library: {}, Symbol: {}", library_name, symbol_name);
    
    // Find KiCad library path
    let lib_path = find_kicad_library_path()
        .ok_or_else(|| {
            warn!("❌ KiCad symbol library not found on system");
            SchematicError::InvalidData("KiCad symbol library not found".to_string())
        })?;
    
    // Look for the library file
    let library_file = lib_path.join(format!("{}.kicad_sym", library_name));
    debug!("  Looking for library file: {:?}", library_file);
    if !library_file.exists() {
        warn!("  Library file not found: {:?}", library_file);
        return Ok(None);
    }
    info!("  Found library file: {:?}", library_file);
    
    // Read and parse the library file
    let content = fs::read_to_string(&library_file)
        .map_err(|e| SchematicError::IoError(format!("Failed to read library file: {}", e)))?;
    
    let lib_sexp = parse::from_str(&content)
        .map_err(|e| SchematicError::InvalidData(format!("Failed to parse library: {}", e)))?;
    
    // Search for the symbol in the library
    if let Value::Cons(cons) = &lib_sexp {
        if let Value::Symbol(sym) = cons.car() {
            if sym.as_ref() == "kicad_symbol_lib" {
                // Iterate through library contents
                let mut current = cons.cdr();
                while let Value::Cons(c) = current {
                    if let Value::Cons(item_cons) = c.car() {
                        if let Value::Symbol(item_sym) = item_cons.car() {
                            if item_sym.as_ref() == "symbol" {
                                // Check if this is our symbol
                                if let Some(name) = get_symbol_name(item_cons) {
                                    debug!("    Checking symbol: {}", name);
                                    // Also check for exact match without library prefix
                                    if name == symbol_name || name == lib_id || 
                                       name.ends_with(&format!(":{}", symbol_name)) {
                                        // Found it! Return the symbol definition
                                        info!("✅ Found symbol '{}' in library", name);
                                        return Ok(Some(c.car().clone()));
                                    }
                                }
                            }
                        }
                    }
                    current = c.cdr();
                }
            }
        }
    }
    
    warn!("❌ Symbol '{}' not found in library file", symbol_name);
    Ok(None)
}

/// Extract symbol name from a symbol S-expression
fn get_symbol_name(symbol_cons: &lexpr::Cons) -> Option<String> {
    let mut current = symbol_cons.cdr();
    
    // First element after "symbol" should be the name
    if let Value::Cons(c) = current {
        if let Value::String(name) = c.car() {
            return Some(name.to_string());
        }
    }
    
    None
}

/// Create a generic symbol definition for common components
/// This is a fallback when the actual symbol can't be found
pub fn create_generic_symbol(lib_id: &str, pin_count: usize) -> Value {
    info!("🔨 Creating generic symbol for: {} with {} pins", lib_id, pin_count);
    let parts: Vec<&str> = lib_id.split(':').collect();
    let symbol_type = if parts.len() > 1 { parts[1] } else { "Generic" };
    
    let description = match symbol_type {
        "R" => "Resistor",
        "C" => "Capacitor", 
        "L" => "Inductor",
        "D" | "LED" => "Diode",
        "Q" => "Transistor",
        "U" => "Integrated Circuit",
        _ => "Electronic Component",
    };
    
    let mut symbol_items = vec![
        Value::symbol("symbol"),
        Value::string(lib_id),
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
        // Standard properties
        Value::list(vec![
            Value::symbol("property"),
            Value::string("Reference"),
            Value::string(&symbol_type[0..1]),
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
            Value::string(symbol_type),
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
            Value::string(description),
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
    ];
    
    // Add generic graphical representation
    symbol_items.push(Value::list(vec![
        Value::symbol("symbol"),
        Value::string(format!("{}_0_1", symbol_type)),
        Value::list(vec![
            Value::symbol("rectangle"),
            Value::list(vec![Value::symbol("start"), Value::from(-2.54), Value::from(-2.54)]),
            Value::list(vec![Value::symbol("end"), Value::from(2.54), Value::from(2.54)]),
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
    ]));
    
    // Add pin definitions
    let mut pins_section = vec![
        Value::symbol("symbol"),
        Value::string(format!("{}_1_1", symbol_type)),
    ];
    
    for i in 1..=pin_count {
        pins_section.push(Value::list(vec![
            Value::symbol("pin"),
            Value::symbol("passive"),
            Value::symbol("line"),
            Value::list(vec![
                Value::symbol("at"),
                Value::from(if i == 1 { 0.0 } else { 5.08 * (i as f64 - 1.0) }),
                Value::from(if i % 2 == 1 { 3.81 } else { -3.81 }),
                Value::from(if i % 2 == 1 { 270 } else { 90 }),
            ]),
            Value::list(vec![Value::symbol("length"), Value::from(1.27)]),
            Value::list(vec![
                Value::symbol("name"),
                Value::string(format!("~")),
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
                Value::string(i.to_string()),
                Value::list(vec![
                    Value::symbol("effects"),
                    Value::list(vec![
                        Value::symbol("font"),
                        Value::list(vec![Value::symbol("size"), Value::from(1.27), Value::from(1.27)]),
                    ]),
                ]),
            ]),
        ]));
    }
    
    symbol_items.push(Value::list(pins_section));
    symbol_items.push(Value::list(vec![Value::symbol("embedded_fonts"), Value::symbol("no")]));
    
    Value::list(symbol_items)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_find_library_path() {
        if let Some(path) = find_kicad_library_path() {
            println!("Found KiCad library at: {:?}", path);
            assert!(path.exists());
        } else {
            println!("KiCad library not found on this system");
        }
    }
    
    #[test]
    fn test_load_resistor_symbol() {
        if find_kicad_library_path().is_some() {
            let result = load_symbol_from_library("Device:R");
            assert!(result.is_ok());
            if let Ok(Some(symbol)) = result {
                println!("Successfully loaded Device:R symbol");
            }
        }
    }
    
    #[test]
    fn test_create_generic_symbol() {
        let symbol = create_generic_symbol("Device:R", 2);
        let sexp_str = lexpr::to_string(&symbol).unwrap();
        assert!(sexp_str.contains("Device:R"));
        assert!(sexp_str.contains("Resistor"));
    }
}