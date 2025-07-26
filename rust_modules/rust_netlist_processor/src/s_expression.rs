//! High-performance S-expression formatting engine
//!
//! This module implements a zero-copy, high-performance S-expression formatter
//! specifically optimized for KiCad netlist generation. It targets 50x performance
//! improvement over the Python implementation through:
//!
//! - Pre-allocated string buffers with capacity management
//! - Direct buffer writing using write! macro
//! - Zero-copy string operations where possible
//! - Specialized formatting for KiCad's exact S-expression structure
//! - Efficient indentation management

use std::fmt::Write;
use std::time::Instant;
use crate::data_transform::{Circuit, Component, Net, NetNode};
use crate::errors::{NetlistError, Result};

/// High-performance S-expression formatter with pre-allocated buffers
pub struct SExprFormatter {
    /// Main output buffer (pre-allocated for performance)
    buffer: String,
    /// Current indentation level
    indent_level: usize,
    /// Indentation string cache (for performance)
    indent_cache: Vec<String>,
    /// Performance tracking
    last_processing_time: Option<std::time::Duration>,
    /// Buffer capacity tracking
    initial_capacity: usize,
}

impl SExprFormatter {
    /// Create a new formatter with optimized default settings
    pub fn new() -> Self {
        Self::with_capacity(1024 * 1024) // 1MB initial capacity
    }

    /// Create a formatter with specific initial capacity
    pub fn with_capacity(capacity: usize) -> Self {
        let mut indent_cache = Vec::with_capacity(32); // Support up to 32 levels of nesting
        
        // Pre-populate indent cache for common levels
        for i in 0..32 {
            indent_cache.push("  ".repeat(i));
        }

        Self {
            buffer: String::with_capacity(capacity),
            indent_level: 0,
            indent_cache,
            last_processing_time: None,
            initial_capacity: capacity,
        }
    }

    /// Reset the formatter for reuse
    pub fn reset(&mut self) {
        self.buffer.clear();
        self.indent_level = 0;
        self.last_processing_time = None;
    }

    /// Get current buffer capacity
    pub fn buffer_capacity(&self) -> usize {
        self.buffer.capacity()
    }

    /// Get last processing time in milliseconds
    pub fn last_processing_time_ms(&self) -> f64 {
        self.last_processing_time
            .map(|d| d.as_secs_f64() * 1000.0)
            .unwrap_or(0.0)
    }

    /// Get current indentation string (cached for performance)
    fn indent(&self) -> &str {
        self.indent_cache.get(self.indent_level)
            .map(|s| s.as_str())
            .unwrap_or("")
    }

    /// Increase indentation level
    fn indent_in(&mut self) {
        self.indent_level += 1;
        
        // Extend cache if needed
        if self.indent_level >= self.indent_cache.len() {
            self.indent_cache.push("  ".repeat(self.indent_level));
        }
    }

    /// Decrease indentation level
    fn indent_out(&mut self) {
        if self.indent_level > 0 {
            self.indent_level -= 1;
        }
    }

    /// Format a complete KiCad netlist
    pub fn format_complete_netlist(
        &mut self,
        design_section: &str,
        components_section: &str,
        libparts_section: &str,
        libraries_section: &str,
        nets_section: &str,
    ) -> Result<String> {
        let start_time = Instant::now();
        
        self.reset();
        
        // Write export header with version
        writeln!(self.buffer, "(export (version \"E\")")?;
        
        // Write design section
        write!(self.buffer, "{}", design_section)?;
        
        // Write components section with proper wrapper
        writeln!(self.buffer, "    (components")?;
        write!(self.buffer, "{}", components_section)?;
        writeln!(self.buffer, "    )")?;
        
        // Write libparts section with proper wrapper
        writeln!(self.buffer, "    (libparts")?;
        write!(self.buffer, "{}", libparts_section)?;
        writeln!(self.buffer, "    )")?;
        
        // Write libraries section with proper wrapper
        writeln!(self.buffer, "    (libraries")?;
        write!(self.buffer, "{}", libraries_section)?;
        writeln!(self.buffer, "    )")?;
        
        // Write nets section with proper wrapper
        writeln!(self.buffer, "    (nets")?;
        write!(self.buffer, "{}", nets_section)?;
        writeln!(self.buffer, "    )")?;
        
        // Close export
        write!(self.buffer, ")")?;
        
        self.last_processing_time = Some(start_time.elapsed());
        Ok(self.buffer.clone())
    }

    /// Generate the design section
    pub fn generate_design_section(&mut self, circuit: &Circuit) -> Result<String> {
        let mut section = String::with_capacity(4096);
        
        writeln!(section, "  (design")?;
        
        // Source file
        let source_file = if circuit.source_file.is_empty() {
            format!("{}.kicad_sch", circuit.name)
        } else {
            circuit.source_file.clone()
        };
        writeln!(section, "    (source \"{}\")", source_file)?;
        
        // Date with timezone
        let now = chrono::Utc::now();
        let date_str = now.format("%Y-%m-%dT%H:%M:%S%z").to_string();
        writeln!(section, "    (date \"{}\")", date_str)?;
        
        // Tool information
        writeln!(section, "    (tool \"Circuit-Synth Rust Netlist Processor v0.1.0\")")?;
        
        // Generate hierarchical sheet structure to match reference netlist
        self.generate_hierarchical_sheets(&mut section, circuit, &source_file)?;
        writeln!(section, "  )")?;     // Close design
        
        Ok(section)
    }

    /// Format the components section
    pub fn format_components_section(&mut self, components_data: &str) -> Result<String> {
        let mut section = String::with_capacity(components_data.len() + 1024);
        writeln!(section, "  (components")?;
        write!(section, "{}", components_data)?;
        writeln!(section, "  )")?;
        Ok(section)
    }

    /// Format the nets section
    pub fn format_nets_section(&mut self, nets_data: &str) -> Result<String> {
        let mut section = String::with_capacity(nets_data.len() + 1024);
        writeln!(section, "  (nets")?;
        write!(section, "{}", nets_data)?;
        writeln!(section, "  )")?;
        Ok(section)
    }

    /// Generate hierarchical sheet structure to match reference netlist format
    fn generate_hierarchical_sheets(&self, section: &mut String, circuit: &Circuit, source_file: &str) -> std::fmt::Result {
        // Generate root sheet
        writeln!(section, "      (sheet (number \"1\") (name \"root\") (tstamps \"/f3e12ede-c85d-44c9-ba6c-ecb32182f3db/\")")?;
        self.write_title_block(section, source_file)?;
        writeln!(section, "      )")?; // Close sheet
        
        // Generate subcircuit sheets
        let mut sheet_number = 2;
        self.generate_subcircuit_sheets(section, circuit, "root", &mut sheet_number, source_file)?;
        
        Ok(())
    }
    
    /// Recursively generate sheets for subcircuits
    fn generate_subcircuit_sheets(&self, section: &mut String, circuit: &Circuit, parent_path: &str, sheet_number: &mut i32, source_file: &str) -> std::fmt::Result {
        for subcircuit in &circuit.subcircuits {
            let sheet_name = format!("{}/{}", parent_path, subcircuit.name);
            writeln!(section, "      (sheet (number \"{}\") (name \"{}\") (tstamps \"/74b770b4-18a0-4978-a763-fae590825f0d/\")", sheet_number, sheet_name)?;
            self.write_title_block(section, source_file)?;
            writeln!(section, "      )")?; // Close sheet
            
            *sheet_number += 1;
            
            // Recursively process nested subcircuits
            self.generate_subcircuit_sheets(section, subcircuit, &sheet_name, sheet_number, source_file)?;
        }
        Ok(())
    }
    
    /// Write title block for a sheet
    fn write_title_block(&self, section: &mut String, source_file: &str) -> std::fmt::Result {
        writeln!(section, "      (title_block")?;
        writeln!(section, "        (title)")?;
        writeln!(section, "        (company)")?;
        writeln!(section, "        (rev)")?;
        writeln!(section, "        (date)")?;
        writeln!(section, "        (source \"{}\")", source_file)?;
        
        // Standard comment fields
        for i in 1..=9 {
            writeln!(section, "        (comment (number \"{}\") (value \"\"))", i)?;
        }
        
        writeln!(section, "      )")?; // Close title_block
        Ok(())
    }

    /// Format a single component entry with KiCad's exact structure
    pub fn format_component_entry(&mut self, component: &Component) -> Result<String> {
        let mut entry = String::with_capacity(2048);
        
        // Component header: (comp (ref "R1")
        write!(entry, "    (comp (ref \"{}\")", component.reference)?;
        
        // Value on new line if present
        if !component.value.is_empty() {
            write!(entry, "\n      (value \"{}\")", component.value)?;
        }
        
        // Footprint on new line if present
        if !component.footprint.is_empty() {
            write!(entry, "\n      (footprint \"{}\")", component.footprint)?;
        }
        
        // Description on new line if present
        if !component.description.is_empty() {
            write!(entry, "\n      (description \"{}\")", component.description)?;
        }
        
        // Fields section
        if !component.footprint.is_empty() || !component.datasheet.is_empty() || !component.properties.is_empty() {
            write!(entry, "\n      (fields")?;
            
            if !component.footprint.is_empty() {
                write!(entry, "\n        (field (name \"Footprint\") \"{}\")", component.footprint)?;
            }
            
            if !component.datasheet.is_empty() {
                write!(entry, "\n        (field (name \"Datasheet\") \"{}\")", component.datasheet)?;
            }
            
            if !component.description.is_empty() {
                write!(entry, "\n        (field (name \"Description\") \"{}\")", component.description)?;
            }
            
            write!(entry, "\n      )")?; // Close fields
        }
        
        // Libsource
        let (lib, part) = component.library()
            .and_then(|lib| component.part().map(|part| (lib, part)))
            .map_err(|e| NetlistError::formatting_error(format!("Invalid component symbol: {}", e)))?;
        
        write!(entry, "\n      (libsource (lib \"{}\") (part \"{}\")", lib, part)?;
        if !component.description.is_empty() {
            write!(entry, " (description \"{}\")", component.description)?;
        }
        write!(entry, ")")?;
        
        // Properties
        write!(entry, "\n      (property (name \"Sheetname\") (value \"/\"))")?;
        write!(entry, "\n      (property (name \"Sheetfile\") (value \"{}.kicad_sch\"))", "circuit")?;
        
        // Additional properties
        for (key, value) in &component.properties {
            write!(entry, "\n      (property (name \"{}\") (value \"{}\"))", key, value)?;
        }
        
        // Sheetpath
        write!(entry, "\n      (sheetpath (names \"/\") (tstamps \"/{}/)\")", component.timestamp.as_deref().unwrap_or("default"))?;
        
        // Component timestamp
        write!(entry, "\n      (tstamps \"{}\")", component.timestamp.as_deref().unwrap_or("default"))?;
        
        write!(entry, "\n    )")?; // Close component
        
        Ok(entry)
    }

    /// Format a single net entry with optimized node processing
    pub fn format_net_entry(&mut self, net: &Net, net_code: u32) -> Result<String> {
        let mut entry = String::with_capacity(1024 + net.nodes.len() * 256);
        
        // Net header: (net (code "1") (name "VCC")
        write!(entry, "    (net (code \"{}\") (name \"{}\")", net_code, net.name)?;
        
        // Process nodes efficiently
        for node in &net.nodes {
            write!(entry, "\n      (node (ref \"{}\") (pin \"{}\") (pintype \"{}\")",
                node.normalized_component_ref(),
                node.pin.number,
                node.pin.pin_type.to_kicad_str()
            )?;
            
            // Add pin function if available and not default
            if !node.pin.name.is_empty() && node.pin.name != "~" {
                write!(entry, " (pinfunction \"{}\")", node.pin.name)?;
            }
            
            write!(entry, ")")?; // Close node
        }
        
        write!(entry, "\n    )")?; // Close net
        
        Ok(entry)
    }

    /// Format a libpart entry
    pub fn format_libpart_entry(&mut self, lib: &str, part: &str, component: &Component) -> Result<String> {
        let mut entry = String::with_capacity(2048);
        
        // Libpart header
        write!(entry, "    (libpart (lib \"{}\") (part \"{}\")", lib, part)?;
        
        // Description
        if !component.description.is_empty() {
            write!(entry, "\n      (description \"{}\")", component.description)?;
        }
        
        // Docs (datasheet)
        let datasheet = if component.datasheet.is_empty() { "~" } else { &component.datasheet };
        write!(entry, "\n      (docs \"{}\")", datasheet)?;
        
        // Footprints (if any filters specified)
        if let Some(fp_filters) = component.properties.get("ki_fp_filters") {
            if !fp_filters.is_empty() {
                write!(entry, "\n      (footprints")?;
                for filter in fp_filters.split_whitespace() {
                    write!(entry, "\n        (fp \"{}\")", filter)?;
                }
                write!(entry, "\n      )")?; // Close footprints
            }
        }
        
        // Fields section
        write!(entry, "\n      (fields")?;
        let ref_prefix = component.reference.chars().next().unwrap_or('?');
        write!(entry, "\n        (field (name \"Reference\") \"{}\")", ref_prefix)?;
        write!(entry, "\n        (field (name \"Value\") \"{}\")", component.value)?;
        write!(entry, "\n        (field (name \"Footprint\") \"{}\")", component.footprint)?;
        write!(entry, "\n        (field (name \"Datasheet\") \"{}\")", datasheet)?;
        
        // Additional KiCad fields
        for (key, value) in &component.properties {
            if key.starts_with("ki_") && !["ki_fp_filters", "ki_footprint"].contains(&key.as_str()) {
                let field_name = key[3..].replace('_', " ");
                let field_name = field_name.split_whitespace()
                    .map(|word| {
                        let mut chars = word.chars();
                        match chars.next() {
                            None => String::new(),
                            Some(first) => first.to_uppercase().collect::<String>() + chars.as_str(),
                        }
                    })
                    .collect::<Vec<_>>()
                    .join(" ");
                write!(entry, "\n        (field (name \"{}\") \"{}\")", field_name, value)?;
            }
        }
        write!(entry, "\n      )")?; // Close fields
        
        // Pins section
        write!(entry, "\n      (pins")?;
        let mut sorted_pins = component.pins.clone();
        sorted_pins.sort_by(|a, b| {
            // Try to sort numerically first, then alphabetically
            match (a.number.parse::<u32>(), b.number.parse::<u32>()) {
                (Ok(a_num), Ok(b_num)) => a_num.cmp(&b_num),
                _ => a.number.cmp(&b.number),
            }
        });
        
        for pin in &sorted_pins {
            let pin_name = if pin.name.is_empty() { "~" } else { &pin.name };
            write!(entry, "\n        (pin (num \"{}\") (name \"{}\") (type \"{}\"))",
                pin.number, pin_name, pin.pin_type.to_kicad_str())?;
        }
        write!(entry, "\n      )")?; // Close pins
        
        write!(entry, "\n    )")?; // Close libpart
        
        Ok(entry)
    }

    /// Format a library entry
    pub fn format_library_entry(&mut self, lib_name: &str) -> Result<String> {
        // Determine KiCad symbol library path based on platform
        let symbol_path = self.get_kicad_symbol_path(lib_name);
        
        Ok(format!(
            "    (library (logical \"{}\")\n      (uri \"{}\"))",
            lib_name, symbol_path
        ))
    }

    /// Get KiCad symbol library path for the given library
    fn get_kicad_symbol_path(&self, lib_name: &str) -> String {
        // Cross-platform KiCad symbol library path detection
        let possible_paths = if cfg!(target_os = "macos") {
            vec![
                "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/",
                "/Applications/KiCad9/KiCad.app/Contents/SharedSupport/symbols/",
            ]
        } else if cfg!(target_os = "linux") {
            vec![
                "/usr/share/kicad/symbols/",
                "/usr/local/share/kicad/symbols/",
                "/snap/kicad/current/usr/share/kicad/symbols/",
            ]
        } else if cfg!(target_os = "windows") {
            vec![
                "C:\\Program Files\\KiCad\\share\\kicad\\symbols\\",
                "C:\\Program Files (x86)\\KiCad\\share\\kicad\\symbols\\",
            ]
        } else {
            vec!["/usr/share/kicad/symbols/"]
        };

        // Find the first existing path
        for path in possible_paths {
            if std::path::Path::new(path).exists() {
                return format!("{}{}.kicad_sym", path, lib_name);
            }
        }

        // Fallback to Linux default
        format!("/usr/share/kicad/symbols/{}.kicad_sym", lib_name)
    }
}

impl Default for SExprFormatter {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::data_transform::{Component, PinInfo, PinType};

    #[test]
    fn test_formatter_creation() {
        let formatter = SExprFormatter::new();
        assert!(formatter.buffer_capacity() >= 1024 * 1024);
        assert_eq!(formatter.indent_level, 0);
    }

    #[test]
    fn test_indentation() {
        let mut formatter = SExprFormatter::new();
        assert_eq!(formatter.indent(), "");
        
        formatter.indent_in();
        assert_eq!(formatter.indent(), "  ");
        
        formatter.indent_in();
        assert_eq!(formatter.indent(), "    ");
        
        formatter.indent_out();
        assert_eq!(formatter.indent(), "  ");
    }

    #[test]
    fn test_component_formatting() {
        let mut formatter = SExprFormatter::new();
        let mut component = Component::new("R1", "Device:R", "10k");
        component.footprint = "Resistor_SMD:R_0603_1608Metric".to_string();
        component.add_pin(PinInfo::new("1", "~", PinType::Passive));
        component.add_pin(PinInfo::new("2", "~", PinType::Passive));
        
        let result = formatter.format_component_entry(&component).unwrap();
        assert!(result.contains("(comp (ref \"R1\")"));
        assert!(result.contains("(value \"10k\")"));
        assert!(result.contains("(libsource (lib \"Device\") (part \"R\")"));
    }

    #[test]
    fn test_reset_functionality() {
        let mut formatter = SExprFormatter::new();
        formatter.buffer.push_str("test content");
        formatter.indent_in();
        
        formatter.reset();
        assert!(formatter.buffer.is_empty());
        assert_eq!(formatter.indent_level, 0);
    }

    #[test]
    fn test_library_path_generation() {
        let formatter = SExprFormatter::new();
        let path = formatter.get_kicad_symbol_path("Device");
        assert!(path.contains("Device.kicad_sym"));
    }
}