//! Advanced search functionality for symbol libraries
//!
//! This module provides tier-based search capabilities that reduce
//! search scope from 225+ libraries to 5-10 targeted libraries.

use crate::{Result, SymbolIndexEntry};
use std::collections::HashMap;
use tracing::{debug, info};

impl crate::SymbolLibCache {
    /// Advanced search with fuzzy matching and ranking
    pub fn search_symbols_advanced(
        &self,
        search_term: &str,
        categories: Option<&[String]>,
        max_results: Option<usize>,
        fuzzy_threshold: Option<f32>,
    ) -> Result<Vec<(String, SymbolIndexEntry, f32)>> {
        self.ensure_index_built()?;

        let search_lower = search_term.to_lowercase();
        let mut matches = Vec::new();
        let threshold = fuzzy_threshold.unwrap_or(0.3);

        // Determine target libraries
        let target_libraries = if let Some(cats) = categories {
            if self.inner.config.enable_tier_search {
                self.get_libraries_for_categories(cats)
            } else {
                self.get_all_library_names()
            }
        } else {
            self.get_all_library_names()
        };

        info!(
            "Advanced search: '{}' in {} libraries",
            search_term,
            target_libraries.len()
        );

        // Search and rank results
        for entry in self.inner.symbol_index.iter() {
            let (symbol_name, index_entry) = entry.pair();

            // Filter by target libraries if specified
            if !target_libraries.is_empty() && !target_libraries.contains(&index_entry.library_name)
            {
                continue;
            }

            // Calculate match score
            let score = self.calculate_match_score(&symbol_name.to_lowercase(), &search_lower);

            if score >= threshold {
                matches.push((symbol_name.clone(), index_entry.clone(), score));
            }
        }

        // Sort by score (descending)
        matches.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap_or(std::cmp::Ordering::Equal));

        // Limit results
        if let Some(limit) = max_results {
            matches.truncate(limit);
        }

        info!("Advanced search found {} matches", matches.len());
        Ok(matches)
    }

    /// Calculate fuzzy match score between two strings
    fn calculate_match_score(&self, symbol_name: &str, search_term: &str) -> f32 {
        // Exact match gets highest score
        if symbol_name == search_term {
            return 1.0;
        }

        // Starts with search term gets high score
        if symbol_name.starts_with(search_term) {
            return 0.9;
        }

        // Contains search term gets medium score
        if symbol_name.contains(search_term) {
            return 0.7;
        }

        // Fuzzy matching using Levenshtein distance
        let distance = self.levenshtein_distance(symbol_name, search_term);
        let max_len = symbol_name.len().max(search_term.len());

        if max_len == 0 {
            return 0.0;
        }

        let similarity = 1.0 - (distance as f32 / max_len as f32);

        // Apply minimum threshold
        if similarity < 0.3 {
            0.0
        } else {
            similarity * 0.6 // Scale down fuzzy matches
        }
    }

    /// Calculate Levenshtein distance between two strings
    fn levenshtein_distance(&self, s1: &str, s2: &str) -> usize {
        let len1 = s1.len();
        let len2 = s2.len();

        if len1 == 0 {
            return len2;
        }
        if len2 == 0 {
            return len1;
        }

        let mut matrix = vec![vec![0; len2 + 1]; len1 + 1];

        // Initialize first row and column
        for i in 0..=len1 {
            matrix[i][0] = i;
        }
        for j in 0..=len2 {
            matrix[0][j] = j;
        }

        let s1_chars: Vec<char> = s1.chars().collect();
        let s2_chars: Vec<char> = s2.chars().collect();

        // Fill the matrix
        for i in 1..=len1 {
            for j in 1..=len2 {
                let cost = if s1_chars[i - 1] == s2_chars[j - 1] {
                    0
                } else {
                    1
                };

                matrix[i][j] = (matrix[i - 1][j] + 1)
                    .min(matrix[i][j - 1] + 1)
                    .min(matrix[i - 1][j - 1] + cost);
            }
        }

        matrix[len1][len2]
    }

    /// Get libraries for specified categories
    fn get_libraries_for_categories(&self, categories: &[String]) -> Vec<String> {
        let mut libraries = Vec::new();

        for category in categories {
            if let Some(libs) = self.inner.category_libraries.get(category) {
                libraries.extend(libs.clone());
            }
        }

        libraries.sort();
        libraries.dedup();
        libraries
    }

    /// Get all library names
    fn get_all_library_names(&self) -> Vec<String> {
        self.inner
            .library_index
            .iter()
            .map(|entry| entry.key().clone())
            .collect()
    }

    /// Search symbols with regex pattern
    pub fn search_symbols_regex(
        &self,
        pattern: &str,
        categories: Option<&[String]>,
        max_results: Option<usize>,
    ) -> Result<Vec<(String, SymbolIndexEntry)>> {
        use regex::Regex;

        self.ensure_index_built()?;

        let regex = Regex::new(pattern).map_err(|e| crate::SymbolCacheError::Validation {
            message: format!("Invalid regex pattern: {}", e),
        })?;

        let mut matches = Vec::new();

        // Determine target libraries
        let target_libraries = if let Some(cats) = categories {
            if self.inner.config.enable_tier_search {
                self.get_libraries_for_categories(cats)
            } else {
                Vec::new()
            }
        } else {
            Vec::new()
        };

        // Search with regex
        for entry in self.inner.symbol_index.iter() {
            let (symbol_name, index_entry) = entry.pair();

            // Filter by target libraries if specified
            if !target_libraries.is_empty() && !target_libraries.contains(&index_entry.library_name)
            {
                continue;
            }

            if regex.is_match(symbol_name) {
                matches.push((symbol_name.clone(), index_entry.clone()));

                // Check limit
                if let Some(limit) = max_results {
                    if matches.len() >= limit {
                        break;
                    }
                }
            }
        }

        info!(
            "Regex search found {} matches for pattern '{}'",
            matches.len(),
            pattern
        );
        Ok(matches)
    }

    /// Get symbol suggestions based on partial input
    pub fn get_symbol_suggestions(
        &self,
        partial_name: &str,
        max_suggestions: Option<usize>,
    ) -> Result<Vec<String>> {
        self.ensure_index_built()?;

        let partial_lower = partial_name.to_lowercase();
        let mut suggestions = Vec::new();
        let limit = max_suggestions.unwrap_or(10);

        // Collect matching symbols
        for entry in self.inner.symbol_index.iter() {
            let symbol_name = entry.key();

            if symbol_name.to_lowercase().starts_with(&partial_lower) {
                suggestions.push(symbol_name.clone());

                if suggestions.len() >= limit {
                    break;
                }
            }
        }

        // Sort suggestions
        suggestions.sort();

        debug!(
            "Generated {} suggestions for '{}'",
            suggestions.len(),
            partial_name
        );
        Ok(suggestions)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::SymbolLibCache;

    #[test]
    fn test_levenshtein_distance() {
        let cache = SymbolLibCache::new();

        assert_eq!(cache.levenshtein_distance("", ""), 0);
        assert_eq!(cache.levenshtein_distance("abc", ""), 3);
        assert_eq!(cache.levenshtein_distance("", "abc"), 3);
        assert_eq!(cache.levenshtein_distance("abc", "abc"), 0);
        assert_eq!(cache.levenshtein_distance("abc", "ab"), 1);
        assert_eq!(cache.levenshtein_distance("abc", "def"), 3);
    }

    #[test]
    fn test_match_score() {
        let cache = SymbolLibCache::new();

        // Exact match
        assert_eq!(cache.calculate_match_score("resistor", "resistor"), 1.0);

        // Starts with
        assert_eq!(cache.calculate_match_score("resistor", "resist"), 0.9);

        // Contains
        assert_eq!(cache.calculate_match_score("smd_resistor", "resist"), 0.7);

        // No match
        assert!(cache.calculate_match_score("capacitor", "resistor") < 0.3);
    }
}
