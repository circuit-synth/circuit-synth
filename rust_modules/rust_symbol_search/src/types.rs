//! Core data types for the symbol search engine

use serde::{Deserialize, Serialize};

/// Represents a KiCad symbol
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Symbol {
    pub name: String,
    pub library: String,
    pub lib_id: String,
}

/// Symbol data for indexing
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct SymbolData {
    pub name: String,
    pub library: String,
    pub lib_id: String,
}

impl SymbolData {
    pub fn new(name: String, library: String) -> Self {
        let lib_id = format!("{}:{}", library, name);
        Self {
            name,
            library,
            lib_id,
        }
    }
}

/// Search result with scoring information
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SearchResult {
    pub lib_id: String,
    pub symbol_name: String,
    pub library_name: String,
    pub score: f64,
    pub match_type: MatchType,
    pub match_details: MatchDetails,
}

/// Type of match found
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum MatchType {
    Exact,
    HighFuzzy,
    Fuzzy,
    Substring,
    NGram,
}

/// Detailed match information
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MatchDetails {
    pub symbol_exact: f64,
    pub symbol_fuzzy: f64,
    pub library_fuzzy: f64,
    pub lib_id_fuzzy: f64,
    pub symbol_substring: f64,
    pub library_substring: f64,
    pub ngram_score: f64,
}

impl Default for MatchDetails {
    fn default() -> Self {
        Self {
            symbol_exact: 0.0,
            symbol_fuzzy: 0.0,
            library_fuzzy: 0.0,
            lib_id_fuzzy: 0.0,
            symbol_substring: 0.0,
            library_substring: 0.0,
            ngram_score: 0.0,
        }
    }
}

/// Search statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchStats {
    pub total_searches: u64,
    pub avg_search_time_ns: u64,
    pub index_build_time_ns: u64,
    pub symbol_count: usize,
    pub index_size_bytes: usize,
}

impl Default for SearchStats {
    fn default() -> Self {
        Self {
            total_searches: 0,
            avg_search_time_ns: 0,
            index_build_time_ns: 0,
            symbol_count: 0,
            index_size_bytes: 0,
        }
    }
}

/// Configuration for search behavior
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchConfig {
    pub min_score: f64,
    pub max_results: usize,
    pub fuzzy_threshold: f64,
    pub ngram_size: usize,
    pub enable_substring_matching: bool,
    pub enable_fuzzy_matching: bool,
    pub enable_ngram_matching: bool,
    pub boost_common_components: bool,
}

impl Default for SearchConfig {
    fn default() -> Self {
        Self {
            min_score: 0.3,
            max_results: 10,
            fuzzy_threshold: 0.6,
            ngram_size: 3,
            enable_substring_matching: true,
            enable_fuzzy_matching: true,
            enable_ngram_matching: true,
            boost_common_components: true,
        }
    }
}

/// Common component types for boosting
pub const COMMON_SYMBOLS: &[&str] = &["R", "C", "L", "D", "Q", "U", "J", "SW"];
pub const COMMON_LIBRARIES: &[&str] = &["Device", "Connector", "Switch", "Diode", "Transistor"];
pub const COMMON_KEYWORDS: &[&str] = &["resistor", "capacitor", "inductor", "diode", "transistor"];

/// Check if a symbol should be boosted as a common component
pub fn is_common_component(symbol_name: &str, library_name: &str) -> bool {
    COMMON_SYMBOLS.contains(&symbol_name) ||
    COMMON_LIBRARIES.contains(&library_name) ||
    COMMON_KEYWORDS.iter().any(|keyword| {
        symbol_name.to_lowercase().contains(keyword) ||
        library_name.to_lowercase().contains(keyword)
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_symbol_data_creation() {
        let symbol = SymbolData::new("R".to_string(), "Device".to_string());
        assert_eq!(symbol.name, "R");
        assert_eq!(symbol.library, "Device");
        assert_eq!(symbol.lib_id, "Device:R");
    }

    #[test]
    fn test_common_component_detection() {
        assert!(is_common_component("R", "Device"));
        assert!(is_common_component("USB_Connector", "Connector"));
        assert!(is_common_component("MyResistor", "CustomLib"));
        assert!(!is_common_component("CustomIC", "CustomLib"));
    }

    #[test]
    fn test_search_result_serialization() {
        let result = SearchResult {
            lib_id: "Device:R".to_string(),
            symbol_name: "R".to_string(),
            library_name: "Device".to_string(),
            score: 0.95,
            match_type: MatchType::Exact,
            match_details: MatchDetails::default(),
        };

        let json = serde_json::to_string(&result).unwrap();
        let deserialized: SearchResult = serde_json::from_str(&json).unwrap();
        assert_eq!(result, deserialized);
    }
}