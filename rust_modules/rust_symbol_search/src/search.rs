//! Main search engine implementation
//!
//! This module provides the high-level search interface that combines
//! indexing, fuzzy matching, and scoring to deliver fast, accurate results.

use crate::fuzzy::FuzzyMatcher;
use crate::index::SymbolIndex;
use crate::types::{
    is_common_component, MatchDetails, MatchType, SearchConfig, SearchResult, SearchStats,
    SymbolData,
};
use ahash::AHashSet;
use rayon::prelude::*;
use std::time::Instant;

/// High-performance search engine for symbols
#[derive(Debug)]
pub struct SearchEngine {
    /// Symbol index for fast candidate retrieval
    index: SymbolIndex,

    /// Fuzzy matcher for string similarity
    fuzzy_matcher: FuzzyMatcher,

    /// Search configuration
    config: SearchConfig,

    /// Performance statistics
    stats: SearchStats,
}

impl SearchEngine {
    /// Create a new search engine
    pub fn new() -> Self {
        Self {
            index: SymbolIndex::new(),
            fuzzy_matcher: FuzzyMatcher::default(),
            config: SearchConfig::default(),
            stats: SearchStats::default(),
        }
    }

    /// Create a search engine with custom configuration
    pub fn with_config(config: SearchConfig) -> Self {
        Self {
            index: SymbolIndex::new(),
            fuzzy_matcher: FuzzyMatcher::new(config.fuzzy_threshold),
            config,
            stats: SearchStats::default(),
        }
    }

    /// Build the search index from symbol data
    pub fn build_index(
        &mut self,
        symbols: Vec<SymbolData>,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let start_time = Instant::now();

        self.index.build_index(symbols)?;

        let build_time = start_time.elapsed();
        self.stats.index_build_time_ns = build_time.as_nanos() as u64;
        self.stats.symbol_count = self.index.get_all_symbols().len();

        Ok(())
    }

    /// Search for symbols matching the query
    pub fn search(&mut self, query: &str, max_results: usize, min_score: f64) -> Vec<SearchResult> {
        let start_time = Instant::now();

        // Normalize query
        let query_lower = query.to_lowercase().trim().to_string();
        if query_lower.is_empty() {
            return Vec::new();
        }

        // Try exact matches first
        let exact_results = self.find_exact_matches(&query_lower);
        if !exact_results.is_empty() {
            self.update_search_stats(start_time.elapsed().as_nanos() as u64);
            return exact_results.into_iter().take(max_results).collect();
        }

        // Find candidates using index
        let candidates = self.index.find_candidates(&query_lower);

        // If no candidates from index, use fuzzy fallback
        let candidates = if candidates.is_empty() {
            self.fuzzy_fallback(&query_lower)
        } else {
            candidates
        };

        // Score and rank candidates
        let mut results = self.score_candidates(&query_lower, &candidates, min_score);

        // Sort by score descending
        results.sort_by(|a, b| {
            b.score
                .partial_cmp(&a.score)
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        // Limit results
        results.truncate(max_results);

        self.update_search_stats(start_time.elapsed().as_nanos() as u64);
        results
    }

    /// Find exact matches for the query
    fn find_exact_matches(&self, query: &str) -> Vec<SearchResult> {
        let exact_indices = self.index.find_exact_matches(query);

        exact_indices
            .into_iter()
            .filter_map(|idx| self.index.get_symbol(idx))
            .map(|symbol| SearchResult {
                lib_id: symbol.lib_id.clone(),
                symbol_name: symbol.name.clone(),
                library_name: symbol.library.clone(),
                score: 1.0,
                match_type: MatchType::Exact,
                match_details: MatchDetails {
                    symbol_exact: 1.0,
                    ..Default::default()
                },
            })
            .collect()
    }

    /// Fuzzy fallback when no index hits found
    fn fuzzy_fallback(&self, query: &str) -> AHashSet<usize> {
        let mut candidates = AHashSet::new();

        // Use parallel processing for large symbol sets
        let symbols = self.index.get_all_symbols();
        if symbols.len() > 1000 {
            // Parallel fuzzy matching for large datasets
            let matches: Vec<usize> = symbols
                .par_iter()
                .enumerate()
                .filter_map(|(idx, symbol)| {
                    let score = self.fuzzy_matcher.ratio(query, &symbol.name.to_lowercase());
                    if score >= self.config.fuzzy_threshold {
                        Some(idx)
                    } else {
                        None
                    }
                })
                .collect::<Vec<_>>()
                .into_iter()
                .take(50) // Limit to maintain performance
                .collect();

            candidates.extend(matches);
        } else {
            // Sequential processing for smaller datasets
            for (idx, symbol) in symbols.iter().enumerate() {
                let score = self.fuzzy_matcher.ratio(query, &symbol.name.to_lowercase());
                if score >= self.config.fuzzy_threshold {
                    candidates.insert(idx);
                    if candidates.len() >= 50 {
                        break;
                    }
                }
            }
        }

        candidates
    }

    /// Score and filter candidates
    fn score_candidates(
        &self,
        query: &str,
        candidates: &AHashSet<usize>,
        min_score: f64,
    ) -> Vec<SearchResult> {
        let mut results = Vec::new();

        for &symbol_idx in candidates {
            if let Some(symbol) = self.index.get_symbol(symbol_idx) {
                let scores = self.calculate_match_scores(query, symbol);

                // Combined score with weights
                let combined_score = self.calculate_combined_score(&scores);

                // Boost for common components
                let final_score = if self.config.boost_common_components
                    && is_common_component(&symbol.name, &symbol.library)
                {
                    combined_score * 1.1
                } else {
                    combined_score
                };

                if final_score >= min_score {
                    let match_type = self.determine_match_type(&scores);

                    results.push(SearchResult {
                        lib_id: symbol.lib_id.clone(),
                        symbol_name: symbol.name.clone(),
                        library_name: symbol.library.clone(),
                        score: final_score,
                        match_type,
                        match_details: scores,
                    });
                }
            }
        }

        results
    }

    /// Calculate various match scores for a symbol
    fn calculate_match_scores(&self, query: &str, symbol: &SymbolData) -> MatchDetails {
        let symbol_name_lower = symbol.name.to_lowercase();
        let library_name_lower = symbol.library.to_lowercase();
        let lib_id_lower = symbol.lib_id.to_lowercase();

        MatchDetails {
            symbol_exact: if query == symbol_name_lower { 1.0 } else { 0.0 },
            symbol_fuzzy: if self.config.enable_fuzzy_matching {
                self.fuzzy_matcher.ratio(query, &symbol_name_lower)
            } else {
                0.0
            },
            library_fuzzy: if self.config.enable_fuzzy_matching {
                self.fuzzy_matcher.ratio(query, &library_name_lower)
            } else {
                0.0
            },
            lib_id_fuzzy: if self.config.enable_fuzzy_matching {
                self.fuzzy_matcher.ratio(query, &lib_id_lower)
            } else {
                0.0
            },
            symbol_substring: if self.config.enable_substring_matching
                && symbol_name_lower.contains(query)
            {
                1.0
            } else {
                0.0
            },
            library_substring: if self.config.enable_substring_matching
                && library_name_lower.contains(query)
            {
                1.0
            } else {
                0.0
            },
            ngram_score: if self.config.enable_ngram_matching {
                crate::fuzzy::ngram_similarity(query, &symbol_name_lower, self.config.ngram_size)
            } else {
                0.0
            },
        }
    }

    /// Calculate combined score from individual match scores
    fn calculate_combined_score(&self, scores: &MatchDetails) -> f64 {
        scores.symbol_exact * 0.4
            + scores.symbol_fuzzy * 0.25
            + scores.library_fuzzy * 0.15
            + scores.lib_id_fuzzy * 0.1
            + scores.symbol_substring * 0.05
            + scores.library_substring * 0.03
            + scores.ngram_score * 0.02
    }

    /// Determine match type based on scores
    fn determine_match_type(&self, scores: &MatchDetails) -> MatchType {
        if scores.symbol_exact > 0.9 {
            MatchType::Exact
        } else if scores.symbol_fuzzy > 0.8 {
            MatchType::HighFuzzy
        } else if scores.symbol_substring > 0.0 || scores.library_substring > 0.0 {
            MatchType::Substring
        } else if scores.ngram_score > 0.5 {
            MatchType::NGram
        } else {
            MatchType::Fuzzy
        }
    }

    /// Update search performance statistics
    fn update_search_stats(&mut self, search_time_ns: u64) {
        self.stats.total_searches += 1;

        // Update rolling average
        let total = self.stats.total_searches;
        let current_avg = self.stats.avg_search_time_ns;

        self.stats.avg_search_time_ns = (current_avg * (total - 1) + search_time_ns) / total;
    }

    /// Get search engine statistics
    pub fn get_stats(&self) -> serde_json::Value {
        let mut index_stats = self.index.get_stats();
        index_stats.total_searches = self.stats.total_searches;
        index_stats.avg_search_time_ns = self.stats.avg_search_time_ns;

        serde_json::to_value(&index_stats).unwrap_or_default()
    }

    /// Check if the search engine is ready
    pub fn is_ready(&self) -> bool {
        self.index.is_built()
    }

    /// Get configuration
    pub fn get_config(&self) -> &SearchConfig {
        &self.config
    }

    /// Update configuration
    pub fn set_config(&mut self, config: SearchConfig) {
        self.fuzzy_matcher = FuzzyMatcher::new(config.fuzzy_threshold);
        self.config = config;
    }
}

impl Default for SearchEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::SymbolData;

    fn create_test_symbols() -> Vec<SymbolData> {
        vec![
            SymbolData::new("R".to_string(), "Device".to_string()),
            SymbolData::new("C".to_string(), "Device".to_string()),
            SymbolData::new("L".to_string(), "Device".to_string()),
            SymbolData::new("LM7805_TO220".to_string(), "Regulator_Linear".to_string()),
            SymbolData::new("USB_C_Receptacle".to_string(), "Connector_USB".to_string()),
            SymbolData::new("ESP32-WROOM-32".to_string(), "RF_Module".to_string()),
        ]
    }

    #[test]
    fn test_search_engine_basic() {
        let mut engine = SearchEngine::new();
        engine.build_index(create_test_symbols()).unwrap();

        assert!(engine.is_ready());

        // Test exact match
        let results = engine.search("Device:R", 5, 0.3);
        assert!(!results.is_empty());
        assert_eq!(results[0].symbol_name, "R");
        assert_eq!(results[0].match_type, MatchType::Exact);

        // Test fuzzy match
        let results = engine.search("resistor", 5, 0.3);
        assert!(!results.is_empty());
    }

    #[test]
    fn test_search_performance() {
        let mut engine = SearchEngine::new();

        // Create large symbol set
        let mut symbols = Vec::new();
        for i in 0..10000 {
            symbols.push(SymbolData::new(
                format!("Symbol_{}", i),
                "TestLib".to_string(),
            ));
        }

        let start = Instant::now();
        engine.build_index(symbols).unwrap();
        let build_time = start.elapsed();

        println!("Build time for 10k symbols: {:?}", build_time);
        assert!(build_time.as_millis() < 50);

        let start = Instant::now();
        let _results = engine.search("Symbol_1234", 10, 0.3);
        let search_time = start.elapsed();

        println!("Search time: {:?}", search_time);
        assert!(search_time.as_millis() < 5);
    }

    #[test]
    fn test_fuzzy_fallback() {
        let mut engine = SearchEngine::new();
        engine.build_index(create_test_symbols()).unwrap();

        // Search for something that won't match index but should fuzzy match
        let results = engine.search("resitor", 5, 0.3); // Typo in "resistor"
        assert!(!results.is_empty());
    }

    #[test]
    fn test_scoring_and_ranking() {
        let mut engine = SearchEngine::new();
        engine.build_index(create_test_symbols()).unwrap();

        let results = engine.search("regulator", 5, 0.1);
        assert!(!results.is_empty());

        // Results should be sorted by score
        for i in 1..results.len() {
            assert!(results[i - 1].score >= results[i].score);
        }
    }

    #[test]
    fn test_common_component_boosting() {
        let mut config = SearchConfig::default();
        config.boost_common_components = true;

        let mut engine = SearchEngine::with_config(config);
        engine.build_index(create_test_symbols()).unwrap();

        let results = engine.search("r", 5, 0.1);
        assert!(!results.is_empty());

        // "R" from Device library should be boosted
        let r_result = results.iter().find(|r| r.symbol_name == "R");
        assert!(r_result.is_some());
    }

    #[test]
    fn test_statistics() {
        let mut engine = SearchEngine::new();
        engine.build_index(create_test_symbols()).unwrap();

        // Perform some searches
        engine.search("resistor", 5, 0.3);
        engine.search("capacitor", 5, 0.3);

        let stats = engine.get_stats();
        assert!(stats["total_searches"].as_u64().unwrap() >= 2);
        assert!(stats["symbol_count"].as_u64().unwrap() > 0);
        assert!(stats["index_build_time_ns"].as_u64().unwrap() > 0);
    }
}
