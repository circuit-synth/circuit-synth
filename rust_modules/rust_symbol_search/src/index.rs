//! High-performance indexing for symbol search
//!
//! This module implements memory-efficient inverted indexing and n-gram generation
//! optimized for fast symbol lookup and fuzzy matching.

use crate::types::{SearchStats, SymbolData};
use ahash::{AHashMap, AHashSet};
use smallvec::SmallVec;
use std::time::Instant;

/// Token type for indexing - uses SmallVec to avoid heap allocation for short tokens
type Token = SmallVec<[char; 16]>;

/// High-performance symbol index using inverted indexing and n-grams
#[derive(Debug)]
pub struct SymbolIndex {
    /// Map from symbol name to library name
    symbol_to_library: AHashMap<String, String>,

    /// Inverted index: token -> set of symbol indices
    inverted_index: AHashMap<String, AHashSet<usize>>,

    /// N-gram index: ngram -> set of symbol indices  
    ngram_index: AHashMap<String, AHashSet<usize>>,

    /// Exact match index: normalized_string -> symbol_index
    exact_matches: AHashMap<String, usize>,

    /// Symbol data array for fast access by index
    symbols: Vec<SymbolData>,

    /// Index metadata
    build_time_ns: u64,
    index_built: bool,
}

impl SymbolIndex {
    /// Create a new empty index
    pub fn new() -> Self {
        Self {
            symbol_to_library: AHashMap::new(),
            inverted_index: AHashMap::new(),
            ngram_index: AHashMap::new(),
            exact_matches: AHashMap::new(),
            symbols: Vec::new(),
            build_time_ns: 0,
            index_built: false,
        }
    }

    /// Build the index from symbol data
    pub fn build_index(
        &mut self,
        symbols: Vec<SymbolData>,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let start_time = Instant::now();

        // Clear existing data
        self.clear();

        // Reserve capacity for better performance
        let symbol_count = symbols.len();
        self.symbols.reserve(symbol_count);
        self.symbol_to_library.reserve(symbol_count);
        self.exact_matches.reserve(symbol_count * 2); // symbol + lib_id matches

        // Build core mappings
        for (idx, symbol) in symbols.into_iter().enumerate() {
            self.symbol_to_library
                .insert(symbol.name.clone(), symbol.library.clone());

            // Index symbol name tokens
            self.index_tokens(&symbol.name, idx);

            // Index library name tokens
            self.index_tokens(&symbol.library, idx);

            // Build n-gram index for fuzzy matching
            self.index_ngrams(&symbol.name.to_lowercase(), idx, 3);
            self.index_ngrams(&symbol.library.to_lowercase(), idx, 3);

            // Add exact matches
            self.exact_matches.insert(symbol.name.to_lowercase(), idx);
            self.exact_matches.insert(symbol.lib_id.to_lowercase(), idx);

            self.symbols.push(symbol);
        }

        self.build_time_ns = start_time.elapsed().as_nanos() as u64;
        self.index_built = true;

        Ok(())
    }

    /// Clear all index data
    fn clear(&mut self) {
        self.symbol_to_library.clear();
        self.inverted_index.clear();
        self.ngram_index.clear();
        self.exact_matches.clear();
        self.symbols.clear();
        self.index_built = false;
    }

    /// Index tokens from text
    fn index_tokens(&mut self, text: &str, symbol_idx: usize) {
        let tokens = self.tokenize(text);

        for token in tokens {
            self.inverted_index
                .entry(token)
                .or_insert_with(AHashSet::new)
                .insert(symbol_idx);
        }
    }

    /// Index n-grams from text
    fn index_ngrams(&mut self, text: &str, symbol_idx: usize, n: usize) {
        let ngrams = self.generate_ngrams(text, n);

        for ngram in ngrams {
            self.ngram_index
                .entry(ngram)
                .or_insert_with(AHashSet::new)
                .insert(symbol_idx);
        }
    }

    /// Tokenize text into searchable tokens
    fn tokenize(&self, text: &str) -> Vec<String> {
        let mut tokens = Vec::new();

        // Split on common delimiters and extract alphanumeric tokens
        let base_tokens: Vec<&str> = text
            .split(|c: char| !c.is_alphanumeric())
            .filter(|s| !s.is_empty())
            .collect();

        for token in base_tokens {
            let lower_token = token.to_lowercase();
            tokens.push(lower_token.clone());

            // Add prefix tokens for partial matching (length 2+)
            if lower_token.len() > 2 {
                for i in 2..=lower_token.len() {
                    tokens.push(lower_token[..i].to_string());
                }
            }
        }

        tokens
    }

    /// Generate n-grams from text
    fn generate_ngrams(&self, text: &str, n: usize) -> Vec<String> {
        if text.len() < n {
            return vec![text.to_string()];
        }

        let chars: Vec<char> = text.chars().collect();
        let mut ngrams = Vec::new();

        for i in 0..=chars.len().saturating_sub(n) {
            let ngram: String = chars[i..i + n].iter().collect();
            ngrams.push(ngram);
        }

        ngrams
    }

    /// Find exact matches for a query
    pub fn find_exact_matches(&self, query: &str) -> Vec<usize> {
        let normalized_query = query.to_lowercase();

        if let Some(&symbol_idx) = self.exact_matches.get(&normalized_query) {
            vec![symbol_idx]
        } else {
            Vec::new()
        }
    }

    /// Find candidate symbols using inverted index
    pub fn find_candidates(&self, query: &str) -> AHashSet<usize> {
        let mut candidates = AHashSet::new();

        // Tokenize query and find candidates for each token
        let query_tokens = self.tokenize(query);

        for token in query_tokens {
            if let Some(token_candidates) = self.inverted_index.get(&token) {
                candidates.extend(token_candidates);
            }
        }

        // Also check n-grams for partial matches
        let query_ngrams = self.generate_ngrams(&query.to_lowercase(), 3);
        for ngram in query_ngrams {
            if let Some(ngram_candidates) = self.ngram_index.get(&ngram) {
                candidates.extend(ngram_candidates);
            }
        }

        candidates
    }

    /// Get symbol data by index
    pub fn get_symbol(&self, idx: usize) -> Option<&SymbolData> {
        self.symbols.get(idx)
    }

    /// Get all symbols
    pub fn get_all_symbols(&self) -> &[SymbolData] {
        &self.symbols
    }

    /// Check if index is built
    pub fn is_built(&self) -> bool {
        self.index_built
    }

    /// Get index statistics
    pub fn get_stats(&self) -> SearchStats {
        SearchStats {
            total_searches: 0,     // This will be tracked by the search engine
            avg_search_time_ns: 0, // This will be tracked by the search engine
            index_build_time_ns: self.build_time_ns,
            symbol_count: self.symbols.len(),
            index_size_bytes: self.estimate_memory_usage(),
        }
    }

    /// Estimate memory usage of the index
    fn estimate_memory_usage(&self) -> usize {
        let mut size = 0;

        // Symbol data
        size += self.symbols.len() * std::mem::size_of::<SymbolData>();
        size += self
            .symbols
            .iter()
            .map(|s| s.name.len() + s.library.len() + s.lib_id.len())
            .sum::<usize>();

        // Inverted index
        size += self.inverted_index.len() * std::mem::size_of::<(String, AHashSet<usize>)>();
        size += self.inverted_index.keys().map(|k| k.len()).sum::<usize>();
        size += self
            .inverted_index
            .values()
            .map(|v| v.len() * std::mem::size_of::<usize>())
            .sum::<usize>();

        // N-gram index
        size += self.ngram_index.len() * std::mem::size_of::<(String, AHashSet<usize>)>();
        size += self.ngram_index.keys().map(|k| k.len()).sum::<usize>();
        size += self
            .ngram_index
            .values()
            .map(|v| v.len() * std::mem::size_of::<usize>())
            .sum::<usize>();

        // Exact matches
        size += self.exact_matches.len() * std::mem::size_of::<(String, usize)>();
        size += self.exact_matches.keys().map(|k| k.len()).sum::<usize>();

        size
    }
}

impl Default for SymbolIndex {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_symbols() -> Vec<SymbolData> {
        vec![
            SymbolData::new("R".to_string(), "Device".to_string()),
            SymbolData::new("C".to_string(), "Device".to_string()),
            SymbolData::new("LM7805_TO220".to_string(), "Regulator_Linear".to_string()),
            SymbolData::new("USB_C_Receptacle".to_string(), "Connector_USB".to_string()),
        ]
    }

    #[test]
    fn test_index_building() {
        let mut index = SymbolIndex::new();
        let symbols = create_test_symbols();

        assert!(!index.is_built());

        index.build_index(symbols).unwrap();

        assert!(index.is_built());
        assert_eq!(index.symbols.len(), 4);
        assert!(index.build_time_ns > 0);
    }

    #[test]
    fn test_exact_matches() {
        let mut index = SymbolIndex::new();
        index.build_index(create_test_symbols()).unwrap();

        let matches = index.find_exact_matches("r");
        assert_eq!(matches.len(), 1);
        assert_eq!(index.get_symbol(matches[0]).unwrap().name, "R");

        let matches = index.find_exact_matches("device:r");
        assert_eq!(matches.len(), 1);
        assert_eq!(index.get_symbol(matches[0]).unwrap().name, "R");
    }

    #[test]
    fn test_candidate_finding() {
        let mut index = SymbolIndex::new();
        index.build_index(create_test_symbols()).unwrap();

        let candidates = index.find_candidates("resistor");
        assert!(!candidates.is_empty());

        let candidates = index.find_candidates("usb");
        assert!(!candidates.is_empty());

        // Should find USB connector
        let usb_found = candidates
            .iter()
            .any(|&idx| index.get_symbol(idx).unwrap().name.contains("USB"));
        assert!(usb_found);
    }

    #[test]
    fn test_tokenization() {
        let index = SymbolIndex::new();

        let tokens = index.tokenize("LM7805_TO220");
        assert!(tokens.contains(&"lm7805".to_string()));
        assert!(tokens.contains(&"to220".to_string()));
        assert!(tokens.contains(&"lm".to_string())); // prefix
        assert!(tokens.contains(&"lm7".to_string())); // prefix
    }

    #[test]
    fn test_ngram_generation() {
        let index = SymbolIndex::new();

        let ngrams = index.generate_ngrams("resistor", 3);
        assert!(ngrams.contains(&"res".to_string()));
        assert!(ngrams.contains(&"esi".to_string()));
        assert!(ngrams.contains(&"tor".to_string()));
    }

    #[test]
    fn test_performance() {
        let mut index = SymbolIndex::new();

        // Create a large symbol set
        let mut symbols = Vec::new();
        for i in 0..10000 {
            symbols.push(SymbolData::new(
                format!("Symbol_{}", i),
                "TestLib".to_string(),
            ));
        }

        let start = Instant::now();
        index.build_index(symbols).unwrap();
        let build_time = start.elapsed();

        println!("Index build time for 10k symbols: {:?}", build_time);
        assert!(build_time.as_millis() < 50); // Should be under 50ms

        let start = Instant::now();
        let _candidates = index.find_candidates("Symbol_1234");
        let search_time = start.elapsed();

        println!("Candidate search time: {:?}", search_time);
        assert!(search_time.as_micros() < 1000); // Should be under 1ms
    }
}
