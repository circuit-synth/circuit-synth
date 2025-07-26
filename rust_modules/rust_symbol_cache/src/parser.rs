//! KiCad symbol file parser
//! 
//! This module provides high-performance parsing of .kicad_sym files
//! with support for:
//! - Fast regex-based symbol extraction
//! - Parallel symbol parsing
//! - Validation and error handling
//! - Pin data extraction

use crate::{PinData, Result, SymbolCacheError, SymbolData};
use regex::Regex;
use std::collections::HashMap;
use std::sync::OnceLock;
use tracing::{debug, warn};

/// Regex patterns for parsing KiCad symbols
struct ParserRegex {
    symbol_def: Regex,
    pin_def: Regex,
    property_def: Regex,
    description: Regex,
    datasheet: Regex,
    keywords: Regex,
    fp_filters: Regex,
    extends: Regex,
}

static PARSER_REGEX: OnceLock<ParserRegex> = OnceLock::new();

impl ParserRegex {
    fn get() -> &'static ParserRegex {
        PARSER_REGEX.get_or_init(|| {
            ParserRegex {
                symbol_def: Regex::new(r#"\(symbol\s+"([^"]+)""#).unwrap(),
                pin_def: Regex::new(
                    r#"\(pin\s+(\w+)\s+(\w+)\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s+(\d+)\)\s+\(length\s+([-\d.]+)\)"#
                ).unwrap(),
                property_def: Regex::new(
                    r#"\(property\s+"([^"]+)"\s+"([^"]*)""#
                ).unwrap(),
                description: Regex::new(r#"\(description\s+"([^"]*)""#).unwrap(),
                datasheet: Regex::new(r#"\(datasheet\s+"([^"]*)""#).unwrap(),
                keywords: Regex::new(r#"\(keywords\s+"([^"]*)""#).unwrap(),
                fp_filters: Regex::new(r#"\(fp_filters\s+"([^"]*)""#).unwrap(),
                extends: Regex::new(r#"\(extends\s+"([^"]*)""#).unwrap(),
            }
        })
    }
}

impl crate::SymbolLibCache {
    /// Extract symbol text blocks from library content
    pub(crate) fn extract_symbol_texts(&self, content: &str) -> Result<Vec<(String, String)>> {
        let regex = ParserRegex::get();
        let mut symbols = Vec::new();
        let mut depth = 0;
        let mut symbol_depth = 0;
        let mut current_symbol: Option<(String, usize)> = None;
        let lines: Vec<&str> = content.lines().collect();
        
        debug!("Starting symbol extraction from {} lines", lines.len());
        
        for (line_idx, line) in lines.iter().enumerate() {
            let trimmed = line.trim();
            
            // Count parentheses for this line
            let open_parens = trimmed.chars().filter(|&c| c == '(').count() as i32;
            let close_parens = trimmed.chars().filter(|&c| c == ')').count() as i32;
            
            // Update depth before processing
            depth += open_parens;
            
            // Check for symbol definition start
            if let Some(captures) = regex.symbol_def.captures(trimmed) {
                if let Some(symbol_name) = captures.get(1) {
                    let name = symbol_name.as_str().to_string();
                    if self.is_valid_symbol_name(&name) {
                        // If we have a current symbol, close it first
                        if let Some((prev_name, prev_start_idx)) = current_symbol.take() {
                            let symbol_text = lines[prev_start_idx..line_idx].join("\n");
                            debug!("Extracted symbol: {} (lines {}-{})", prev_name, prev_start_idx, line_idx - 1);
                            symbols.push((prev_name, symbol_text));
                        }
                        
                        // Start new symbol
                        current_symbol = Some((name.clone(), line_idx));
                        symbol_depth = depth;
                        debug!("Starting symbol: {} at line {} (depth {})", name, line_idx, depth);
                    }
                }
            }
            
            // Update depth after processing
            depth -= close_parens;
            
            // Check for symbol definition end - when we return to the same depth as when symbol started
            if let Some((name, start_idx)) = &current_symbol {
                if depth < symbol_depth {
                    let symbol_text = lines[*start_idx..=line_idx].join("\n");
                    symbols.push((name.clone(), symbol_text));
                    debug!("Completed symbol: {} (lines {}-{})", name, start_idx, line_idx);
                    current_symbol = None;
                }
            }
        }
        
        // Handle any remaining symbol at end of file
        if let Some((name, start_idx)) = current_symbol {
            let symbol_text = lines[start_idx..].join("\n");
            symbols.push((name.clone(), symbol_text));
            debug!("Final symbol: {} (lines {}-{})", name, start_idx, lines.len() - 1);
        }
        
        debug!("✓ Extracted {} symbol definitions from {} lines", symbols.len(), lines.len());
        Ok(symbols)
    }
    
    /// Parse a single symbol text block
    pub(crate) fn parse_symbol_text(&self, text: &str) -> Result<SymbolData> {
        let regex = ParserRegex::get();
        
        // Extract symbol name
        let name = regex.symbol_def.captures(text)
            .and_then(|caps| caps.get(1))
            .map(|m| m.as_str().to_string())
            .ok_or_else(|| SymbolCacheError::Validation {
                message: "Could not extract symbol name".to_string(),
            })?;
        
        // Extract properties
        let mut properties = HashMap::new();
        for caps in regex.property_def.captures_iter(text) {
            if let (Some(key), Some(value)) = (caps.get(1), caps.get(2)) {
                properties.insert(key.as_str().to_string(), value.as_str().to_string());
            }
        }
        
        // Extract description
        let description = regex.description.captures(text)
            .and_then(|caps| caps.get(1))
            .map(|m| m.as_str().to_string())
            .filter(|s| !s.is_empty());
        
        // Extract datasheet
        let datasheet = regex.datasheet.captures(text)
            .and_then(|caps| caps.get(1))
            .map(|m| m.as_str().to_string())
            .filter(|s| !s.is_empty());
        
        // Extract keywords
        let keywords = regex.keywords.captures(text)
            .and_then(|caps| caps.get(1))
            .map(|m| m.as_str().to_string())
            .filter(|s| !s.is_empty());
        
        // Extract footprint filters
        let fp_filters = regex.fp_filters.captures(text)
            .and_then(|caps| caps.get(1))
            .map(|m| {
                m.as_str()
                    .split_whitespace()
                    .map(|s| s.to_string())
                    .collect::<Vec<String>>()
            })
            .filter(|v| !v.is_empty());
        
        // Extract pins
        let pins = self.parse_pins(text)?;
        
        Ok(SymbolData {
            name,
            description,
            datasheet,
            keywords,
            fp_filters,
            pins,
            properties,
        })
    }
    
    /// Parse symbol with inheritance support
    pub(crate) fn parse_symbol_with_inheritance(&self, text: &str, all_symbols: &HashMap<String, String>) -> Result<SymbolData> {
        let regex = ParserRegex::get();
        
        // Extract symbol name
        let name = regex.symbol_def.captures(text)
            .and_then(|caps| caps.get(1))
            .map(|m| m.as_str().to_string())
            .ok_or_else(|| SymbolCacheError::Validation {
                message: "Could not extract symbol name".to_string(),
            })?;
        
        // Check if this symbol extends another symbol
        let extends_name = regex.extends.captures(text)
            .and_then(|caps| caps.get(1))
            .map(|m| m.as_str().to_string());
        
        debug!("Parsing symbol '{}' with extends: {:?}", name, extends_name);
        
        // Start with base symbol data if inheritance is used
        let has_inheritance = extends_name.is_some();
        let mut symbol_data = if let Some(parent_name) = extends_name {
            if let Some(parent_text) = all_symbols.get(&parent_name) {
                debug!("Found parent symbol '{}' for '{}'", parent_name, name);
                // Parse parent symbol recursively to handle nested inheritance
                let mut parent_data = self.parse_symbol_with_inheritance(parent_text, all_symbols)?;
                // Override name with current symbol name
                parent_data.name = name.clone();
                parent_data
            } else {
                warn!("Parent symbol '{}' not found for '{}'", parent_name, name);
                // Fall back to parsing current symbol without inheritance
                self.parse_symbol_text(text)?
            }
        } else {
            // No inheritance, parse normally
            self.parse_symbol_text(text)?
        };
        
        // Extract properties from current symbol (these override parent properties)
        let mut properties = HashMap::new();
        for caps in regex.property_def.captures_iter(text) {
            if let (Some(key), Some(value)) = (caps.get(1), caps.get(2)) {
                properties.insert(key.as_str().to_string(), value.as_str().to_string());
            }
        }
        
        // Merge properties (current symbol overrides parent)
        for (key, value) in properties {
            symbol_data.properties.insert(key, value);
        }
        
        // Override other fields if they exist in current symbol
        if let Some(description) = regex.description.captures(text)
            .and_then(|caps| caps.get(1))
            .map(|m| m.as_str().to_string())
            .filter(|s| !s.is_empty()) {
            symbol_data.description = Some(description);
        }
        
        if let Some(datasheet) = regex.datasheet.captures(text)
            .and_then(|caps| caps.get(1))
            .map(|m| m.as_str().to_string())
            .filter(|s| !s.is_empty()) {
            symbol_data.datasheet = Some(datasheet);
        }
        
        if let Some(keywords) = regex.keywords.captures(text)
            .and_then(|caps| caps.get(1))
            .map(|m| m.as_str().to_string())
            .filter(|s| !s.is_empty()) {
            symbol_data.keywords = Some(keywords);
        }
        
        if let Some(fp_filters) = regex.fp_filters.captures(text)
            .and_then(|caps| caps.get(1))
            .map(|m| {
                m.as_str()
                    .split_whitespace()
                    .map(|s| s.to_string())
                    .collect::<Vec<String>>()
            })
            .filter(|v| !v.is_empty()) {
            symbol_data.fp_filters = Some(fp_filters);
        }
        
        // Parse pins from current symbol (these override parent pins if any)
        let current_pins = self.parse_pins(text)?;
        if !current_pins.is_empty() {
            symbol_data.pins = current_pins;
        }
        
        debug!("Symbol '{}' parsed with {} pins (inheritance: {})", 
               name, symbol_data.pins.len(), has_inheritance);
        
        Ok(symbol_data)
    }
    
    /// Parse pin definitions from symbol text
    fn parse_pins(&self, text: &str) -> Result<Vec<PinData>> {
        let mut pins = Vec::new();
        
        debug!("Starting pin parsing for symbol");
        
        // Modern KiCad pin format:
        // (pin passive line
        //     (at 0 3.81 270)
        //     (length 1.27)
        //     (name "GPIO10"
        //         (effects ...))
        //     (number "10"
        //         (effects ...))
        // )
        
        // Parse modern format: extract name and number separately
        let name_regex = Regex::new(r#"\(name\s+"([^"]*)""#).unwrap();
        let number_regex = Regex::new(r#"\(number\s+"([^"]*)""#).unwrap();
        
        // First, collect all pin names and numbers
        let mut pin_names = Vec::new();
        let mut pin_numbers = Vec::new();
        
        for caps in name_regex.captures_iter(text) {
            if let Some(name) = caps.get(1) {
                pin_names.push(name.as_str().to_string());
            }
        }
        
        for caps in number_regex.captures_iter(text) {
            if let Some(number) = caps.get(1) {
                pin_numbers.push(number.as_str().to_string());
            }
        }
        
        debug!("Found {} pin names and {} pin numbers", pin_names.len(), pin_numbers.len());
        
        // Match names with numbers (they should be in the same order)
        let pin_count = pin_names.len().max(pin_numbers.len());
        for i in 0..pin_count {
            let pin_name = pin_names.get(i).cloned().unwrap_or_else(|| "~".to_string());
            let pin_number = pin_numbers.get(i).cloned().unwrap_or_else(|| (i + 1).to_string());
            
            debug!("Creating pin: name='{}', number='{}'", pin_name, pin_number);
            
            pins.push(PinData {
                name: pin_name,
                number: pin_number,
                pin_type: "passive".to_string(),
                unit: 1,
                x: 0.0,
                y: 0.0,
                length: 0.0,
                orientation: 0,
            });
        }
        
        // Ultimate fallback: Extract pin numbers from (number "X") patterns
        if pins.is_empty() {
            debug!("All pin parsing failed, using fallback number extraction");
            
            // Try different regex patterns to extract pin numbers
            let patterns = vec![
                r#"\(number\s+"([^"]*)"\s+\(effects"#,
                r#"\(number\s+"([^"]*)""#,
                r#"number\s+"([^"]*)""#,
            ];
            
            let mut pin_numbers = Vec::new();
            
            for pattern in patterns {
                let number_regex = Regex::new(pattern).unwrap();
                for caps in number_regex.captures_iter(text) {
                    if let Some(number) = caps.get(1) {
                        let num_str = number.as_str().to_string();
                        if !pin_numbers.contains(&num_str) {
                            pin_numbers.push(num_str);
                        }
                    }
                }
                
                if !pin_numbers.is_empty() {
                    debug!("Found {} pin numbers using pattern: {}", pin_numbers.len(), pattern);
                    break;
                }
            }
            
            // Create pins from found numbers
            for (_idx, number) in pin_numbers.iter().enumerate() {
                pins.push(PinData {
                    name: "~".to_string(),
                    number: number.clone(),
                    pin_type: "passive".to_string(),
                    unit: 1,
                    x: 0.0,
                    y: 0.0,
                    length: 0.0,
                    orientation: 0,
                });
            }
        }
        
        debug!("Parsed {} pins", pins.len());
        Ok(pins)
    }
    
    /// Validate symbol name for indexing
    pub(crate) fn is_valid_symbol_name(&self, symbol_name: &str) -> bool {
        if symbol_name.is_empty() {
            return false;
        }
        
        // Skip obviously programmatically generated names
        let invalid_suffixes = [
            "_MountingPin_",
            "_Row_Letter_First",
            "_Row_Letter_Last",
            "_Top_Bottom",
            "_Counter_Clockwise",
            "_Odd_Even",
        ];
        
        for suffix in &invalid_suffixes {
            if symbol_name.contains(suffix) {
                return false;
            }
        }
        
        // Skip symbols with excessive complexity
        if symbol_name.matches('_').count() > 6 {
            return false;
        }
        
        // Skip symbols ending with numeric patterns like _1_1, _2_3
        let numeric_pattern = Regex::new(r".*_\d+_\d+$").unwrap();
        if numeric_pattern.is_match(symbol_name) {
            return false;
        }
        
        true
    }
    
    /// Extract symbol names quickly without full parsing
    pub(crate) fn extract_symbol_names_fast(&self, content: &str) -> Vec<String> {
        let regex = ParserRegex::get();
        let mut names = Vec::new();
        
        for caps in regex.symbol_def.captures_iter(content) {
            if let Some(name_match) = caps.get(1) {
                let name = name_match.as_str().to_string();
                if self.is_valid_symbol_name(&name) {
                    names.push(name);
                }
            }
        }
        
        names
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::SymbolLibCache;
    
    #[test]
    fn test_symbol_name_validation() {
        let cache = SymbolLibCache::new();
        
        // Valid names
        assert!(cache.is_valid_symbol_name("R"));
        assert!(cache.is_valid_symbol_name("C_Small"));
        assert!(cache.is_valid_symbol_name("ESP32_WROOM_32"));
        
        // Invalid names
        assert!(!cache.is_valid_symbol_name(""));
        assert!(!cache.is_valid_symbol_name("Component_MountingPin_"));
        assert!(!cache.is_valid_symbol_name("Test_1_2"));
        assert!(!cache.is_valid_symbol_name("Very_Long_Name_With_Too_Many_Underscores_Here"));
    }
    
    #[test]
    fn test_symbol_id_parsing() {
        let cache = SymbolLibCache::new();
        
        // Valid symbol IDs
        let (lib, sym) = cache.parse_symbol_id("Device:R").unwrap();
        assert_eq!(lib, "Device");
        assert_eq!(sym, "R");
        
        // Invalid symbol IDs
        assert!(cache.parse_symbol_id("InvalidFormat").is_err());
        assert!(cache.parse_symbol_id("Too:Many:Colons").is_err());
    }
}