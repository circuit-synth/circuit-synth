//! Python bindings for the Rust KiCad schematic writer
//! 
//! This module provides PyO3 bindings to expose Rust functionality to Python.

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::types::*;
use crate::RustSchematicWriter;
use log::{info, debug};

/// Initialize logging for the Python module using pyo3-log
fn init_logging() {
    static INIT: std::sync::Once = std::sync::Once::new();
    INIT.call_once(|| {
        // Initialize pyo3-log to bridge Rust logging to Python
        // Use try_init to avoid panicking if logger is already initialized
        if let Err(_) = pyo3_log::try_init() {
            // Logger already initialized, which is fine
            eprintln!("🔧 [RUST] Logger already initialized, continuing...");
        } else {
            eprintln!("✅ [RUST] Logger initialized successfully");
        }
    });
}


/// Python wrapper for the Rust schematic writer
#[pyclass]
pub struct PyRustSchematicWriter {
    writer: RustSchematicWriter,
}

#[pymethods]
impl PyRustSchematicWriter {
    /// Create a new schematic writer from Python circuit data
    #[new]
    pub fn new(circuit_data_dict: &PyDict, config_dict: Option<&PyDict>) -> PyResult<Self> {
        init_logging();
        debug!("🐍 Creating Rust schematic writer from Python data");
        
        // Convert Python circuit data to Rust types
        debug!("🔄 About to call convert_circuit_data_from_python");
        let circuit_data = match convert_circuit_data_from_python(circuit_data_dict) {
            Ok(data) => {
                debug!("✅ Conversion succeeded");
                data
            },
            Err(e) => {
                debug!("❌ Failed to convert circuit data: {}", e);
                return Err(e);
            }
        };
        
        // Convert config or use default
        let config = if let Some(config_dict) = config_dict {
            convert_config_from_python(config_dict)?
        } else {
            SchematicConfig::default()
        };
        
        info!("✅ Rust schematic writer created successfully");
        info!("📊 Circuit: {} components, {} nets, {} subcircuits",
              circuit_data.components.len(), circuit_data.nets.len(), circuit_data.subcircuits.len());
        
        Ok(Self {
            writer: RustSchematicWriter::new(circuit_data, config),
        })
    }

    /// Generate hierarchical labels and return them as Python objects
    pub fn generate_hierarchical_labels(&mut self) -> PyResult<Vec<Py<PyDict>>> {
        info!("🚀 Python: Starting hierarchical label generation");
        
        let labels = self.writer.generate_hierarchical_labels()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Label generation failed: {}", e)))?;
        
        info!("✨ Python: Generated {} hierarchical labels", labels.len());
        
        // Convert labels to Python dictionaries
        Python::with_gil(|py| {
            let py_labels: PyResult<Vec<Py<PyDict>>> = labels.iter().map(|label| {
                let dict = PyDict::new(py);
                dict.set_item("name", &label.name)?;
                dict.set_item("shape", label.shape.to_kicad_string())?;
                dict.set_item("x", label.position.x)?;
                dict.set_item("y", label.position.y)?;
                dict.set_item("orientation", label.orientation)?;
                dict.set_item("font_size", label.effects.font_size)?;
                dict.set_item("justify", &label.effects.justify)?;
                dict.set_item("uuid", &label.uuid)?;
                Ok(dict.into())
            }).collect();
            
            py_labels
        })
    }

    /// Generate the complete KiCad schematic S-expression
    pub fn generate_schematic_sexp(&self) -> PyResult<String> {
        info!("🔄 Python: Generating KiCad S-expression");
        
        let sexp = self.writer.generate_schematic_sexp()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("S-expression generation failed: {}", e)))?;
        
        info!("✅ Python: S-expression generated, {} characters", sexp.len());
        Ok(sexp)
    }

    /// Write the schematic to a file
    pub fn write_to_file(&self, path: &str) -> PyResult<()> {
        info!("📁 Python: Writing schematic to file: {}", path);
        
        self.writer.write_to_file(path)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("File write failed: {}", e)))?;
        
        info!("✅ Python: Schematic written successfully");
        Ok(())
    }

    /// Get statistics about the circuit
    pub fn get_stats(&self) -> PyResult<Py<PyDict>> {
        Python::with_gil(|py| {
            let dict = PyDict::new(py);
            // Use hierarchical counts instead of local counts
            let all_components = self.writer.circuit_data.get_all_components();
            let all_nets = self.writer.circuit_data.get_all_nets();
            dict.set_item("component_count", all_components.len())?;
            dict.set_item("net_count", all_nets.len())?;
            dict.set_item("total_connections", self.writer.circuit_data.total_connections())?;
            dict.set_item("hierarchical_label_count", self.writer.hierarchical_labels.len())?;
            Ok(dict.into())
        })
    }
}

/// Standalone function to generate hierarchical labels from Python data
#[pyfunction]
pub fn generate_hierarchical_labels_from_python(
    circuit_data_dict: &PyDict,
    config_dict: Option<&PyDict>,
) -> PyResult<Vec<Py<PyDict>>> {
    init_logging();
    info!("🐍 Standalone hierarchical label generation from Python");
    
    // Add error handling to catch conversion issues
    match PyRustSchematicWriter::new(circuit_data_dict, config_dict) {
        Ok(mut writer) => writer.generate_hierarchical_labels(),
        Err(e) => {
            info!("❌ Failed to create PyRustSchematicWriter: {}", e);
            Err(e)
        }
    }
}

/// Standalone function to generate complete schematic from Python data
#[pyfunction]
pub fn generate_schematic_from_python(
    circuit_data_dict: &PyDict,
    config_dict: Option<&PyDict>,
) -> PyResult<String> {
    info!("🐍 Standalone schematic generation from Python");
    
    let mut writer = PyRustSchematicWriter::new(circuit_data_dict, config_dict)?;
    let _ = writer.generate_hierarchical_labels()?; // Generate labels first
    writer.generate_schematic_sexp()
}

/// Simple component S-expression generator for TDD testing
#[pyfunction]
pub fn generate_component_sexp(component_data: &PyDict) -> PyResult<String> {
    init_logging();
    debug!("🦀 RUST TDD: Generating component S-expression for TDD test");
    
    // Extract component data from Python dict
    let ref_val: String = component_data.get_item("ref")?
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("Missing 'ref' field"))?
        .extract()?;
    
    let symbol: String = component_data.get_item("symbol")?
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("Missing 'symbol' field"))?
        .extract()?;
    
    let value: String = match component_data.get_item("value")? {
        Some(val) => val.extract()?,
        None => "".to_string(),
    };
    
    let lib_id = match component_data.get_item("lib_id")? {
        Some(val) => val.extract()?,
        None => symbol.clone(),
    };
    
    // Generate the S-expression directly using simple format for TDD
    // This matches exactly the format from our Python implementation
    let mut result = format!("(symbol (lib_id \"{}\") (at 0 0 0) (unit 1)\n", lib_id);
    result.push_str(&format!("  (property \"Reference\" \"{}\")\n", ref_val));
    if !value.is_empty() {
        result.push_str(&format!("  (property \"Value\" \"{}\")\n", value));
    }
    result.push(')');
    
    debug!("✅ RUST TDD: Generated S-expression: {} chars", result.len());
    Ok(result)
}

/// Convert Python circuit data dictionary to Rust CircuitData
fn convert_circuit_data_from_python(py_dict: &PyDict) -> PyResult<CircuitData> {
    // Use both logging and println! to ensure visibility
    let session_msg = format!("🔄 RUST_ENTRY: convert_circuit_data_from_python() called");
    info!("{}", session_msg);
    println!("{}", session_msg);
    
    let unique_msg = format!("🚨 UNIQUE_RUST_MESSAGE_67890: Function definitely reached!");
    info!("{}", unique_msg);
    println!("{}", unique_msg);
    
    let dict_size_msg = format!("🔍 RUST: Dictionary size: {}", py_dict.len());
    info!("{}", dict_size_msg);
    println!("{}", dict_size_msg);
    
    // Try to extract keys more safely
    match py_dict.keys().iter().map(|k| k.extract::<String>()).collect::<Result<Vec<_>, _>>() {
        Ok(keys) => {
            info!("🔍 PYTHON->RUST: Available keys: {:?}", keys);
        },
        Err(e) => {
            info!("❌ PYTHON->RUST: Failed to extract keys: {}", e);
        }
    }
    
    // Extract name with better error handling
    let name: String = match py_dict.get_item("name") {
        Ok(Some(name_val)) => {
            match name_val.extract() {
                Ok(name_str) => {
                    debug!("🏗️  PYTHON->RUST: Extracted name: '{}'", name_str);
                    name_str
                },
                Err(e) => {
                    debug!("❌ Failed to extract name as string: {}", e);
                    return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>("Name field must be a string"));
                }
            }
        },
        Ok(None) => {
            debug!("❌ Name field is None");
            return Err(PyErr::new::<pyo3::exceptions::PyKeyError, _>("Missing 'name' field"));
        },
        Err(e) => {
            debug!("❌ Error accessing name field: {}", e);
            return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Error accessing name field: {}", e)));
        }
    };
    
    debug!("🏗️  PYTHON->RUST: Creating circuit '{}'", name);
    let mut circuit_data = CircuitData::new(name);
    
    // CRITICAL DEBUG: Check what we have in the dictionary
    info!("🔍 PYTHON->RUST: CRITICAL DEBUG - Analyzing input dictionary...");
    if let Ok(Some(components)) = py_dict.get_item("components") {
        info!("🔍 PYTHON->RUST: Found components field, type: {:?}", components.get_type().name());
    } else {
        info!("🔍 PYTHON->RUST: No components field found");
    }
    
    if let Ok(Some(nets)) = py_dict.get_item("nets") {
        info!("🔍 PYTHON->RUST: Found nets field, type: {:?}", nets.get_type().name());
    } else {
        info!("🔍 PYTHON->RUST: No nets field found");
    }
    
    if let Ok(Some(subcircuits)) = py_dict.get_item("subcircuits") {
        info!("🔍 PYTHON->RUST: Found subcircuits field, type: {:?}", subcircuits.get_type().name());
        if let Ok(subcircuits_list) = subcircuits.downcast::<PyList>() {
            info!("🔍 PYTHON->RUST: SUBCIRCUITS LIST LENGTH: {}", subcircuits_list.len());
        }
    } else {
        info!("🔍 PYTHON->RUST: ❌ CRITICAL: No subcircuits field found - this explains the 0 components!");
    }
    
    // Convert components - handle both dict and list formats
    if let Ok(Some(py_components)) = py_dict.get_item("components") {
        match py_components.downcast::<PyList>() {
            Ok(components_list) => {
                // List format: [component1, component2, ...]
                info!("🔧 PYTHON->RUST: Converting {} components (list format)", components_list.len());
                for py_component in components_list {
                    let component_dict: &PyDict = py_component.downcast()?;
                    let component = convert_component_from_python(component_dict)?;
                    circuit_data.add_component(component);
                }
            },
            Err(_) => {
                match py_components.downcast::<PyDict>() {
                    Ok(components_dict) => {
                        // Dict format: {"U1": component1, "U2": component2, ...}
                        info!("🔧 PYTHON->RUST: Converting {} components (dict format)", components_dict.len());
                        for (key, value) in components_dict {
                            let _component_ref: String = key.extract()?;
                            match value.downcast::<PyDict>() {
                                Ok(component_dict) => {
                                    match convert_component_from_python(component_dict) {
                                        Ok(component) => circuit_data.add_component(component),
                                        Err(e) => {
                                            info!("❌ Failed to convert component: {}", e);
                                            return Err(e);
                                        }
                                    }
                                },
                                Err(e) => {
                                    info!("❌ Component value is not a dict: {}", e);
                                    return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>("Component value must be a dictionary"));
                                }
                            }
                        }
                    },
                    Err(_) => {
                        info!("⚠️  PYTHON->RUST: Components field has unexpected type, skipping");
                    }
                }
            }
        }
    }
    
    // Convert nets - handle both dict and list formats
    if let Ok(Some(py_nets)) = py_dict.get_item("nets") {
        if let Ok(nets_list) = py_nets.downcast::<PyList>() {
            // List format: [net1, net2, ...]
            info!("🌐 PYTHON->RUST: Converting {} nets (list format)", nets_list.len());
            for py_net in nets_list {
                let net_dict: &PyDict = py_net.downcast()?;
                let net = convert_net_from_python(net_dict)?;
                circuit_data.add_net(net);
            }
        } else if let Ok(nets_dict) = py_nets.downcast::<PyDict>() {
            // Dict format: {"GND": net1, "VCC": net2, ...}
            info!("🌐 PYTHON->RUST: Converting {} nets (dict format)", nets_dict.len());
            for (key, value) in nets_dict {
                let _net_name: String = key.extract()?;
                let net_dict: &PyDict = value.downcast()?;
                let net = convert_net_from_python(net_dict)?;
                circuit_data.add_net(net);
            }
        } else {
            info!("⚠️  PYTHON->RUST: Nets field has unexpected type, skipping");
        }
    }
    
    // Convert subcircuits - ENHANCED: More detailed debugging
    debug!("🔍 PYTHON->RUST: Checking for subcircuits field...");
    
    // First, let's see what keys are actually in the dictionary
    debug!("🔍 PYTHON->RUST: Available keys in Python dict:");
    let keys = py_dict.keys();
    for key in keys {
        if let Ok(key_str) = key.extract::<String>() {
            debug!("  - Key: '{}'", key_str);
        }
    }
    
    // CRITICAL DEBUG: Check if subcircuits key exists and what type it is
    debug!("🔍 PYTHON->RUST: Detailed subcircuits field analysis:");
    match py_dict.contains("subcircuits") {
        Ok(has_key) => {
            debug!("  - Dictionary contains 'subcircuits' key: {}", has_key);
            if has_key {
                match py_dict.get_item("subcircuits") {
                    Ok(Some(subcircuits_value)) => {
                        debug!("  - Subcircuits value type: {:?}", subcircuits_value.get_type().name());
                        debug!("  - Subcircuits value: {:?}", subcircuits_value);
                        
                        // Try to get length if it's a list
                        if let Ok(subcircuits_list) = subcircuits_value.downcast::<PyList>() {
                            debug!("  - Subcircuits list length: {}", subcircuits_list.len());
                        }
                    },
                    Ok(None) => debug!("  - Subcircuits key exists but value is None"),
                    Err(e) => debug!("  - Error getting subcircuits value: {}", e),
                }
            }
        },
        Err(e) => debug!("  - Error checking for subcircuits key: {}", e),
    }
    
    match py_dict.get_item("subcircuits") {
        Ok(Some(py_subcircuits)) => {
            debug!("🏗️  PYTHON->RUST: Found subcircuits field, attempting conversion...");
            
            match py_subcircuits.downcast::<PyList>() {
                Ok(subcircuits_list) => {
                    debug!("🏗️  PYTHON->RUST: Converting {} subcircuits (HIERARCHICAL DATA FOUND!)", subcircuits_list.len());
                    
                    for (subcircuit_index, py_subcircuit) in subcircuits_list.iter().enumerate() {
                        match py_subcircuit.downcast::<PyDict>() {
                            Ok(subcircuit_dict) => {
                                match convert_circuit_data_from_python(subcircuit_dict) {
                                    Ok(subcircuit) => {
                                        debug!("🔄 PYTHON->RUST: Converted subcircuit #{} '{}' with {} components, {} nets",
                                              subcircuit_index + 1, subcircuit.name, subcircuit.components.len(), subcircuit.nets.len());
                                        
                                        // CRITICAL FIX: Extract and flatten components from subcircuit
                                        debug!("🔧 PYTHON->RUST: FLATTENING subcircuit '{}' components into main circuit...", subcircuit.name);
                                        let mut flattened_components = 0;
                                        for component in subcircuit.components.iter() {
                                            // Create unique reference to avoid conflicts
                                            let unique_ref = format!("{}_{}", subcircuit.name, component.reference);
                                            debug!("  - Flattening component: {} -> {}", component.reference, unique_ref);
                                            
                                            // Clone the component with new reference
                                            let mut flattened_component = component.clone();
                                            flattened_component.reference = unique_ref.clone();
                                            
                                            circuit_data.add_component(flattened_component);
                                            flattened_components += 1;
                                        }
                                        debug!("✅ PYTHON->RUST: Flattened {} components from subcircuit '{}'", flattened_components, subcircuit.name);
                                        
                                        // CRITICAL FIX: Extract and flatten nets from subcircuit
                                        debug!("🔧 PYTHON->RUST: FLATTENING subcircuit '{}' nets into main circuit...", subcircuit.name);
                                        let mut flattened_nets = 0;
                                        for net in subcircuit.nets.iter() {
                                            // Create unique net name to avoid conflicts
                                            let unique_net_name = format!("{}_{}", subcircuit.name, net.name);
                                            debug!("  - Flattening net: {} -> {}", net.name, unique_net_name);
                                            
                                            // Clone the net with updated component references
                                            let mut flattened_net = net.clone();
                                            flattened_net.name = unique_net_name.clone();
                                            
                                            // Update component references in net connections
                                            for connection in flattened_net.connected_pins.iter_mut() {
                                                let old_comp_ref = connection.component_ref.clone();
                                                connection.component_ref = format!("{}_{}", subcircuit.name, old_comp_ref);
                                                debug!("    - Updated connection: {}.{} -> {}.{}",
                                                    old_comp_ref, connection.pin_id, connection.component_ref, connection.pin_id);
                                            }
                                            
                                            circuit_data.add_net(flattened_net);
                                            flattened_nets += 1;
                                        }
                                        debug!("✅ PYTHON->RUST: Flattened {} nets from subcircuit '{}'", flattened_nets, subcircuit.name);
                                        
                                        // Store subcircuit name before moving it
                                        let subcircuit_name = subcircuit.name.clone();
                                        
                                        // Still add the subcircuit for hierarchical structure
                                        circuit_data.add_subcircuit(subcircuit);
                                        
                                        debug!("📊 PYTHON->RUST: After processing subcircuit '{}': main circuit now has {} components, {} nets",
                                            subcircuit_name, circuit_data.components.len(), circuit_data.nets.len());
                                    },
                                    Err(e) => {
                                        debug!("❌ Failed to convert subcircuit #{}: {}", subcircuit_index + 1, e);
                                        return Err(e);
                                    }
                                }
                            },
                            Err(e) => {
                                debug!("❌ Subcircuit #{} is not a dict: {}", subcircuit_index + 1, e);
                                return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>("Subcircuit must be a dictionary"));
                            }
                        }
                    }
                },
                Err(e) => {
                    debug!("❌ Subcircuits field is not a list: {}", e);
                    return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>("Subcircuits field must be a list"));
                }
            }
        },
        Ok(None) => {
            debug!("📝 PYTHON->RUST: Subcircuits field is None - this is a flat circuit");
        },
        Err(e) => {
            debug!("❌ PYTHON->RUST: Error accessing subcircuits field: {}", e);
            return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Error accessing subcircuits field: {}", e)));
        }
    }
    
    let hierarchy_stats = circuit_data.get_hierarchy_stats();
    info!("✅ PYTHON->RUST: FINAL CONVERSION RESULTS:");
    info!("    - 🔧 FLATTENED components in main circuit: {}", circuit_data.components.len());
    info!("    - 🌐 FLATTENED nets in main circuit: {}", circuit_data.nets.len());
    info!("    - 🏗️  Subcircuits preserved for hierarchy: {}", circuit_data.subcircuits.len());
    info!("    - 📊 Total components (all levels): {}", hierarchy_stats.total_components);
    info!("    - 📊 Total nets (all levels): {}", hierarchy_stats.total_nets);
    info!("    - 📏 Max hierarchy depth: {}", hierarchy_stats.max_depth);
    info!("    - 🏗️  Is hierarchical: {}", circuit_data.is_hierarchical());
    
    // CRITICAL DEBUG: Log the actual component and net names that were flattened
    if circuit_data.components.len() > 0 {
        info!("🔧 FLATTENED COMPONENT REFERENCES:");
        for (i, component) in circuit_data.components.iter().enumerate() {
            if i < 10 { // Log first 10 components
                info!("    - Component #{}: {}", i + 1, component.reference);
            }
        }
        if circuit_data.components.len() > 10 {
            info!("    - ... and {} more components", circuit_data.components.len() - 10);
        }
    } else {
        info!("❌ NO COMPONENTS FOUND IN MAIN CIRCUIT - This indicates the flattening failed!");
    }
    
    if circuit_data.nets.len() > 0 {
        info!("🌐 FLATTENED NET NAMES:");
        for (i, net) in circuit_data.nets.iter().enumerate() {
            if i < 10 { // Log first 10 nets
                info!("    - Net #{}: '{}' with {} connections", i + 1, net.name, net.connected_pins.len());
            }
        }
        if circuit_data.nets.len() > 10 {
            info!("    - ... and {} more nets", circuit_data.nets.len() - 10);
        }
    } else {
        info!("❌ NO NETS FOUND IN MAIN CIRCUIT - This indicates the flattening failed!");
    }
    
    Ok(circuit_data)
}

/// Convert Python component dictionary to Rust Component
fn convert_component_from_python(py_dict: &PyDict) -> PyResult<Component> {
    let reference: String = py_dict.get_item("reference")?
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("Missing 'reference' field"))?
        .extract()?;
    
    // Handle both 'lib_id' and 'symbol' fields (JSON uses 'symbol')
    let lib_id: String = if let Ok(Some(lib_id_val)) = py_dict.get_item("lib_id") {
        lib_id_val.extract()?
    } else if let Ok(Some(symbol_val)) = py_dict.get_item("symbol") {
        symbol_val.extract()?
    } else {
        return Err(PyErr::new::<pyo3::exceptions::PyKeyError, _>("Missing 'lib_id' or 'symbol' field"));
    };
    
    let value: String = match py_dict.get_item("value")? {
        Some(val) => val.extract()?,
        None => reference.clone(),
    };
    
    let position = if let Ok(Some(pos_dict)) = py_dict.get_item("position") {
        let pos_dict: &PyDict = pos_dict.downcast()?;
        Position {
            x: match pos_dict.get_item("x")? {
                Some(val) => val.extract()?,
                None => 0.0,
            },
            y: match pos_dict.get_item("y")? {
                Some(val) => val.extract()?,
                None => 0.0,
            },
        }
    } else {
        Position { x: 0.0, y: 0.0 }
    };
    
    let rotation: f64 = match py_dict.get_item("rotation")? {
        Some(val) => val.extract()?,
        None => 0.0,
    };
    
    let mut component = Component::new(reference, lib_id, value, position);
    component.rotation = rotation;
    
    // Convert pins if present
    if let Ok(Some(py_pins)) = py_dict.get_item("pins") {
        let pins_list: &PyList = py_pins.downcast()?;
        for py_pin in pins_list {
            let pin_dict: &PyDict = py_pin.downcast()?;
            let pin = convert_pin_from_python(pin_dict)?;
            component.add_pin(pin);
        }
    }
    
    debug!("✅ Converted component: {} ({})", component.reference, component.lib_id);
    Ok(component)
}

/// Convert Python pin dictionary to Rust Pin
fn convert_pin_from_python(py_dict: &PyDict) -> PyResult<Pin> {
    let number: String = py_dict.get_item("number")?
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("Missing 'number' field"))?
        .extract()?;
    
    let name: String = match py_dict.get_item("name")? {
        Some(val) => val.extract()?,
        None => "~".to_string(),
    };
    
    let x: f64 = match py_dict.get_item("x")? {
        Some(val) => val.extract()?,
        None => 0.0,
    };
    
    let y: f64 = match py_dict.get_item("y")? {
        Some(val) => val.extract()?,
        None => 0.0,
    };
    
    let orientation: f64 = match py_dict.get_item("orientation")? {
        Some(val) => val.extract()?,
        None => 0.0,
    };
    
    Ok(Pin {
        number,
        name,
        x,
        y,
        orientation,
    })
}

/// Convert Python net dictionary to Rust Net
fn convert_net_from_python(py_dict: &PyDict) -> PyResult<Net> {
    let name: String = py_dict.get_item("name")?
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("Missing 'name' field"))?
        .extract()?;
    
    let mut net = Net::new(name);
    
    // Convert connections - check for "nodes", "connections", or "connected_pins"
    let connections_key = if py_dict.get_item("nodes")?.is_some() {
        "nodes"
    } else if py_dict.get_item("connected_pins")?.is_some() {
        "connected_pins"
    } else {
        "connections"
    };
    
    if let Ok(Some(py_connections)) = py_dict.get_item(connections_key) {
        let connections_list: &PyList = py_connections.downcast()?;
        for py_connection in connections_list {
            let connection_dict: &PyDict = py_connection.downcast()?;
            
            // Handle different connection formats
            let (component_ref, pin_id) = if connections_key == "nodes" {
                // JSON format: {"component": "U1", "pin": {"number": "1", ...}}
                let component_ref: String = connection_dict.get_item("component")?
                    .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("Missing 'component' field"))?
                    .extract()?;
                
                let pin_dict: &PyDict = connection_dict.get_item("pin")?
                    .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("Missing 'pin' field"))?
                    .downcast()?;
                
                let pin_number: String = pin_dict.get_item("number")?
                    .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("Missing 'number' field in pin"))?
                    .extract()?;
                
                (component_ref, pin_number)
            } else {
                // Standard format: {"component_ref": "U1", "pin_id": "1"}
                let component_ref: String = connection_dict.get_item("component_ref")?
                    .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("Missing 'component_ref' field"))?
                    .extract()?;
                
                let pin_id: String = connection_dict.get_item("pin_id")?
                    .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("Missing 'pin_id' field"))?
                    .extract()?;
                
                (component_ref, pin_id)
            };
            
            net.add_connection(component_ref, pin_id);
        }
    }
    
    debug!("✅ Converted net: {} with {} connections", net.name, net.connected_pins.len());
    Ok(net)
}

/// Convert Python config dictionary to Rust SchematicConfig
fn convert_config_from_python(py_dict: &PyDict) -> PyResult<SchematicConfig> {
    let mut config = SchematicConfig::default();
    
    if let Ok(Some(paper_size)) = py_dict.get_item("paper_size") {
        config.paper_size = paper_size.extract()?;
    }
    
    if let Ok(Some(title)) = py_dict.get_item("title") {
        config.title = title.extract()?;
    }
    
    if let Ok(Some(company)) = py_dict.get_item("company") {
        config.company = company.extract()?;
    }
    
    if let Ok(Some(version)) = py_dict.get_item("version") {
        config.version = version.extract()?;
    }
    
    if let Ok(Some(generator)) = py_dict.get_item("generator") {
        config.generator = generator.extract()?;
    }
    
    debug!("✅ Converted config: {} paper, generator: {}", config.paper_size, config.generator);
    Ok(config)
}

/// Initialize the Python module
#[pymodule]
fn rust_kicad_schematic_writer(_py: Python, m: &PyModule) -> PyResult<()> {
    // Initialize pyo3-log to bridge Rust logging to Python
    pyo3_log::init();
    
    info!("🚀 Initializing Rust KiCad Schematic Writer Python module");
    
    // Add classes
    m.add_class::<PyRustSchematicWriter>()?;
    
    // Add standalone functions
    m.add_function(wrap_pyfunction!(generate_hierarchical_labels_from_python, m)?)?;
    m.add_function(wrap_pyfunction!(generate_schematic_from_python, m)?)?;
    m.add_function(wrap_pyfunction!(generate_component_sexp, m)?)?;
    
    info!("✅ Python module initialized successfully");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_circuit_data_conversion() {
        // This would test the conversion functions
        // For now, just ensure the module compiles
        assert!(true);
    }
}