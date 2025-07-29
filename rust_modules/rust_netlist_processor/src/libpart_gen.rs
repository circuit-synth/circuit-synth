//! Library parts processing with efficient deduplication
//!
//! This module implements high-performance library parts generation,
//! targeting 35x performance improvement through optimized parsing
//! and efficient deduplication using HashSet.

use crate::data_transform::{Circuit, Component, PinInfo};
use crate::errors::{NetlistError, Result};
use std::collections::{HashMap, HashSet};
use std::time::Instant;

/// High-performance libpart generator
pub struct LibpartGenerator {
    /// Performance tracking
    last_processing_time: Option<std::time::Duration>,
    /// Memory usage estimation
    estimated_memory_usage: usize,
}

impl LibpartGenerator {
    /// Create a new libpart generator
    pub fn new() -> Self {
        Self {
            last_processing_time: None,
            estimated_memory_usage: 0,
        }
    }

    /// Get last processing time in milliseconds
    pub fn last_processing_time_ms(&self) -> f64 {
        self.last_processing_time
            .map(|d| d.as_secs_f64() * 1000.0)
            .unwrap_or(0.0)
    }

    /// Get estimated memory usage
    pub fn memory_usage(&self) -> usize {
        self.estimated_memory_usage
    }

    /// Generate the libparts section for KiCad netlist
    pub fn generate_libparts_section(&mut self, circuit: &Circuit) -> Result<String> {
        let start_time = Instant::now();

        // Collect unique libparts from all components
        let unique_libparts = self.collect_unique_libparts(circuit)?;

        // Generate formatted libparts section
        let libparts_content = self.format_libparts_section(&unique_libparts)?;

        self.last_processing_time = Some(start_time.elapsed());
        self.update_memory_usage(&unique_libparts);

        Ok(libparts_content)
    }

    /// Generate the libraries section for KiCad netlist
    pub fn generate_libraries_section(&mut self, circuit: &Circuit) -> Result<String> {
        let start_time = Instant::now();

        // Extract unique libraries from all components
        let unique_libraries = self.extract_unique_libraries(circuit)?;

        // Generate formatted libraries section
        let libraries_content = self.format_libraries_section(&unique_libraries)?;

        // Update timing (don't overwrite libparts timing)
        if self.last_processing_time.is_none() {
            self.last_processing_time = Some(start_time.elapsed());
        }

        Ok(libraries_content)
    }

    /// Collect unique libparts from the circuit hierarchy
    fn collect_unique_libparts(&self, circuit: &Circuit) -> Result<Vec<LibpartEntry>> {
        let mut unique_libparts = HashMap::new();
        let mut processed_symbols = HashSet::new();

        // Collect all components recursively
        let all_components = circuit.all_components();

        for component in all_components.values() {
            let (lib, part) = self.parse_symbol(&component.symbol)?;
            let libpart_key = format!("{}:{}", lib, part);

            // Skip if we've already processed this libpart
            if processed_symbols.contains(&libpart_key) {
                continue;
            }

            processed_symbols.insert(libpart_key.clone());

            let libpart_entry = LibpartEntry {
                library: lib.to_string(),
                part: part.to_string(),
                description: component.description.clone(),
                datasheet: if component.datasheet.is_empty() {
                    "~".to_string()
                } else {
                    component.datasheet.clone()
                },
                footprint: component.footprint.clone(),
                footprint_filters: component
                    .properties
                    .get("ki_fp_filters")
                    .cloned()
                    .unwrap_or_default(),
                pins: component.pins.clone(),
                properties: component.properties.clone(),
                reference_component: component.reference.clone(),
            };

            unique_libparts.insert(libpart_key, libpart_entry);
        }

        // Convert to sorted vector for deterministic output
        let mut libparts: Vec<_> = unique_libparts.into_values().collect();
        libparts.sort_by(|a, b| a.library.cmp(&b.library).then_with(|| a.part.cmp(&b.part)));

        Ok(libparts)
    }

    /// Extract unique libraries from the circuit
    fn extract_unique_libraries(&self, circuit: &Circuit) -> Result<Vec<String>> {
        let mut unique_libraries = HashSet::new();

        // Collect all components recursively
        let all_components = circuit.all_components();

        for component in all_components.values() {
            let (lib, _) = self.parse_symbol(&component.symbol)?;
            unique_libraries.insert(lib.to_string());
        }

        // Convert to sorted vector
        let mut libraries: Vec<_> = unique_libraries.into_iter().collect();
        libraries.sort();

        Ok(libraries)
    }

    /// Format the complete libparts section
    fn format_libparts_section(&self, libparts: &[LibpartEntry]) -> Result<String> {
        let mut section = String::with_capacity(libparts.len() * 2048);

        for libpart in libparts {
            let formatted_libpart = self.format_single_libpart(libpart)?;
            section.push_str(&formatted_libpart);
            section.push('\n');
        }

        Ok(section)
    }

    /// Format the complete libraries section
    fn format_libraries_section(&self, libraries: &[String]) -> Result<String> {
        let mut section = String::with_capacity(libraries.len() * 256);

        for library in libraries {
            let formatted_library = self.format_single_library(library)?;
            section.push_str(&formatted_library);
            section.push('\n');
        }

        Ok(section)
    }

    /// Format a single libpart entry
    fn format_single_libpart(&self, libpart: &LibpartEntry) -> Result<String> {
        let mut formatted = String::with_capacity(2048);

        // Libpart header
        formatted.push_str(&format!(
            "    (libpart (lib \"{}\") (part \"{}\")",
            libpart.library, libpart.part
        ));

        // Description
        if !libpart.description.is_empty() {
            formatted.push_str(&format!(
                "\n      (description \"{}\")",
                self.escape_string(&libpart.description)
            ));
        }

        // Docs (datasheet)
        formatted.push_str(&format!("\n      (docs \"{}\")", libpart.datasheet));

        // Footprints (footprint filters)
        if !libpart.footprint_filters.is_empty() {
            formatted.push_str("\n      (footprints");
            for filter in libpart.footprint_filters.split_whitespace() {
                if !filter.is_empty() {
                    formatted.push_str(&format!("\n        (fp \"{}\")", filter));
                }
            }
            formatted.push_str("\n      )"); // Close footprints
        }

        // Fields section
        formatted.push_str("\n      (fields");

        // Standard fields
        let ref_prefix = libpart.reference_component.chars().next().unwrap_or('?');

        formatted.push_str(&format!(
            "\n        (field (name \"Reference\") \"{}\")",
            ref_prefix
        ));
        formatted.push_str(&format!(
            "\n        (field (name \"Value\") \"{}\")",
            libpart.part
        ));
        formatted.push_str(&format!(
            "\n        (field (name \"Footprint\") \"{}\")",
            libpart.footprint
        ));
        formatted.push_str(&format!(
            "\n        (field (name \"Datasheet\") \"{}\")",
            if libpart.datasheet == "~" {
                ""
            } else {
                &libpart.datasheet
            }
        ));

        // Additional KiCad fields from properties
        for (key, value) in &libpart.properties {
            if key.starts_with("ki_") && !["ki_fp_filters", "ki_footprint"].contains(&key.as_str())
            {
                let field_name = self.format_field_name(key);
                formatted.push_str(&format!(
                    "\n        (field (name \"{}\") \"{}\")",
                    field_name,
                    self.escape_string(value)
                ));
            }
        }

        formatted.push_str("\n      )"); // Close fields

        // Pins section
        formatted.push_str("\n      (pins");

        // Sort pins for deterministic output
        let mut sorted_pins = libpart.pins.clone();
        sorted_pins.sort_by(|a, b| {
            // Try numeric sort first, then alphabetic
            match (a.number.parse::<u32>(), b.number.parse::<u32>()) {
                (Ok(a_num), Ok(b_num)) => a_num.cmp(&b_num),
                _ => a.number.cmp(&b.number),
            }
        });

        for pin in &sorted_pins {
            let pin_name = if pin.name.is_empty() { "~" } else { &pin.name };
            formatted.push_str(&format!(
                "\n        (pin (num \"{}\") (name \"{}\") (type \"{}\"))",
                pin.number,
                pin_name,
                pin.pin_type.to_kicad_str()
            ));
        }

        formatted.push_str("\n      )"); // Close pins
        formatted.push_str("\n    )"); // Close libpart

        Ok(formatted)
    }

    /// Format a single library entry
    fn format_single_library(&self, library: &str) -> Result<String> {
        let symbol_path = self.get_kicad_symbol_path(library);

        Ok(format!(
            "    (library (logical \"{}\")\n      (uri \"{}\"))",
            library, symbol_path
        ))
    }

    /// Parse symbol into library and part
    fn parse_symbol<'a>(&self, symbol: &'a str) -> Result<(&'a str, &'a str)> {
        let parts: Vec<&str> = symbol.split(':').collect();
        if parts.len() != 2 {
            return Err(NetlistError::libpart_error(format!(
                "Invalid symbol format '{}' - expected 'Library:Part'",
                symbol
            )));
        }
        Ok((parts[0], parts[1]))
    }

    /// Format field name from property key
    fn format_field_name(&self, key: &str) -> String {
        // Convert ki_keywords -> Keywords, ki_description -> Description, etc.
        let name = &key[3..]; // Remove "ki_" prefix
        name.split('_')
            .map(|word| {
                let mut chars = word.chars();
                match chars.next() {
                    None => String::new(),
                    Some(first) => first.to_uppercase().collect::<String>() + chars.as_str(),
                }
            })
            .collect::<Vec<_>>()
            .join(" ")
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

    /// Escape special characters in strings
    fn escape_string(&self, s: &str) -> String {
        s.replace('"', "\\\"")
    }

    /// Update memory usage estimation
    fn update_memory_usage(&mut self, libparts: &[LibpartEntry]) {
        self.estimated_memory_usage = libparts.len() * std::mem::size_of::<LibpartEntry>()
            + libparts
                .iter()
                .map(|l| {
                    l.library.len()
                        + l.part.len()
                        + l.description.len()
                        + l.datasheet.len()
                        + l.footprint.len()
                        + l.footprint_filters.len()
                        + l.reference_component.len()
                        + l.pins.len() * std::mem::size_of::<PinInfo>()
                        + l.properties
                            .iter()
                            .map(|(k, v)| k.len() + v.len())
                            .sum::<usize>()
                })
                .sum::<usize>();
    }
}

impl Default for LibpartGenerator {
    fn default() -> Self {
        Self::new()
    }
}

/// Libpart entry with all necessary information
#[derive(Debug, Clone)]
struct LibpartEntry {
    library: String,
    part: String,
    description: String,
    datasheet: String,
    footprint: String,
    footprint_filters: String,
    pins: Vec<PinInfo>,
    properties: HashMap<String, String>,
    reference_component: String, // For reference prefix extraction
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::data_transform::{Component, PinType};

    #[test]
    fn test_libpart_generator_creation() {
        let generator = LibpartGenerator::new();
        assert_eq!(generator.last_processing_time_ms(), 0.0);
        assert_eq!(generator.memory_usage(), 0);
    }

    #[test]
    fn test_symbol_parsing() {
        let generator = LibpartGenerator::new();

        let (lib, part) = generator.parse_symbol("Device:R").unwrap();
        assert_eq!(lib, "Device");
        assert_eq!(part, "R");

        let result = generator.parse_symbol("InvalidSymbol");
        assert!(result.is_err());
    }

    #[test]
    fn test_field_name_formatting() {
        let generator = LibpartGenerator::new();

        assert_eq!(generator.format_field_name("ki_keywords"), "Keywords");
        assert_eq!(generator.format_field_name("ki_description"), "Description");
        assert_eq!(generator.format_field_name("ki_fp_filters"), "Fp Filters");
    }

    #[test]
    fn test_string_escaping() {
        let generator = LibpartGenerator::new();

        assert_eq!(generator.escape_string("normal string"), "normal string");
        assert_eq!(
            generator.escape_string("string with \"quotes\""),
            "string with \\\"quotes\\\""
        );
    }

    #[test]
    fn test_kicad_symbol_path() {
        let generator = LibpartGenerator::new();
        let path = generator.get_kicad_symbol_path("Device");
        assert!(path.contains("Device.kicad_sym"));
    }

    #[test]
    fn test_library_formatting() {
        let generator = LibpartGenerator::new();
        let result = generator.format_single_library("Device").unwrap();
        assert!(result.contains("(library (logical \"Device\")"));
        assert!(result.contains("Device.kicad_sym"));
    }
}
