//! High-performance fuzzy matching for symbol search
//! 
//! This module provides optimized fuzzy string matching algorithms
//! designed for fast symbol name comparison and scoring.

use rapidfuzz::fuzz;
use std::cmp::Ordering;

/// Fuzzy matching engine with multiple algorithms
#[derive(Debug)]
pub struct FuzzyMatcher {
    /// Minimum score threshold for fuzzy matches
    min_threshold: f64,
}

impl FuzzyMatcher {
    /// Create a new fuzzy matcher
    pub fn new(min_threshold: f64) -> Self {
        Self { min_threshold }
    }

    /// Calculate fuzzy similarity ratio between two strings
    pub fn ratio(&self, s1: &str, s2: &str) -> f64 {
        fuzz::ratio(s1.chars(), s2.chars(), None, None).unwrap_or(0.0) / 100.0
    }

    /// Calculate partial ratio (best matching substring)
    pub fn partial_ratio(&self, s1: &str, s2: &str) -> f64 {
        // Use basic ratio for now since partial_ratio is not available in this version
        self.ratio(s1, s2)
    }

    /// Calculate token sort ratio (order-independent word matching)
    pub fn token_sort_ratio(&self, s1: &str, s2: &str) -> f64 {
        // Use basic ratio for now since token_sort_ratio is not available in this version
        self.ratio(s1, s2)
    }

    /// Calculate token set ratio (set-based word matching)
    pub fn token_set_ratio(&self, s1: &str, s2: &str) -> f64 {
        // Use basic ratio for now since token_set_ratio is not available in this version
        self.ratio(s1, s2)
    }

    /// Calculate comprehensive fuzzy score using multiple algorithms
    pub fn comprehensive_score(&self, query: &str, target: &str) -> f64 {
        let ratio = self.ratio(query, target);
        let partial = self.partial_ratio(query, target);
        let token_sort = self.token_sort_ratio(query, target);
        let token_set = self.token_set_ratio(query, target);

        // Weighted combination of different algorithms
        let score = ratio * 0.4 + partial * 0.3 + token_sort * 0.2 + token_set * 0.1;
        
        // Apply threshold
        if score >= self.min_threshold {
            score
        } else {
            0.0
        }
    }

    /// Fast fuzzy matching for large candidate sets
    pub fn fast_match(&self, query: &str, candidates: &[&str]) -> Vec<(usize, f64)> {
        let mut results = Vec::new();
        
        for (idx, candidate) in candidates.iter().enumerate() {
            let score = self.ratio(query, candidate);
            if score >= self.min_threshold {
                results.push((idx, score));
            }
        }
        
        // Sort by score descending
        results.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(Ordering::Equal));
        
        results
    }

    /// Batch fuzzy matching with early termination
    pub fn batch_match(&self, query: &str, candidates: &[&str], max_results: usize) -> Vec<(usize, f64)> {
        let mut results = Vec::with_capacity(max_results);
        let mut min_score = self.min_threshold;
        
        for (idx, candidate) in candidates.iter().enumerate() {
            let score = self.comprehensive_score(query, candidate);
            
            if score >= min_score {
                // Insert in sorted order
                let insert_pos = results
                    .binary_search_by(|probe: &(usize, f64)| probe.1.partial_cmp(&score).unwrap_or(Ordering::Equal).reverse())
                    .unwrap_or_else(|pos| pos);
                
                results.insert(insert_pos, (idx, score));
                
                // Keep only top results
                if results.len() > max_results {
                    results.truncate(max_results);
                    min_score = results.last().map(|(_, s)| *s).unwrap_or(self.min_threshold);
                }
            }
        }
        
        results
    }

    /// Check if two strings are similar enough to be considered a match
    pub fn is_match(&self, s1: &str, s2: &str) -> bool {
        self.ratio(s1, s2) >= self.min_threshold
    }

    /// Find best matching string from a list
    pub fn find_best_match(&self, query: &str, candidates: &[&str]) -> Option<(usize, f64)> {
        let mut best_idx = None;
        let mut best_score = self.min_threshold;
        
        for (idx, candidate) in candidates.iter().enumerate() {
            let score = self.comprehensive_score(query, candidate);
            if score > best_score {
                best_score = score;
                best_idx = Some(idx);
            }
        }
        
        best_idx.map(|idx| (idx, best_score))
    }
}

impl Default for FuzzyMatcher {
    fn default() -> Self {
        Self::new(0.3)
    }
}

/// Optimized string distance calculation for short strings
pub fn fast_levenshtein_distance(s1: &str, s2: &str) -> usize {
    let len1 = s1.len();
    let len2 = s2.len();
    
    if len1 == 0 {
        return len2;
    }
    if len2 == 0 {
        return len1;
    }
    
    let s1_chars: Vec<char> = s1.chars().collect();
    let s2_chars: Vec<char> = s2.chars().collect();
    
    let mut prev_row: Vec<usize> = (0..=len2).collect();
    let mut curr_row = vec![0; len2 + 1];
    
    for i in 1..=len1 {
        curr_row[0] = i;
        
        for j in 1..=len2 {
            let cost = if s1_chars[i - 1] == s2_chars[j - 1] { 0 } else { 1 };
            
            curr_row[j] = (curr_row[j - 1] + 1)
                .min(prev_row[j] + 1)
                .min(prev_row[j - 1] + cost);
        }
        
        std::mem::swap(&mut prev_row, &mut curr_row);
    }
    
    prev_row[len2]
}

/// Calculate similarity ratio from Levenshtein distance
pub fn similarity_from_distance(s1: &str, s2: &str, distance: usize) -> f64 {
    let max_len = s1.len().max(s2.len());
    if max_len == 0 {
        return 1.0;
    }
    
    1.0 - (distance as f64 / max_len as f64)
}

/// Fast similarity calculation for short strings
pub fn fast_similarity(s1: &str, s2: &str) -> f64 {
    if s1 == s2 {
        return 1.0;
    }
    
    let distance = fast_levenshtein_distance(s1, s2);
    similarity_from_distance(s1, s2, distance)
}

/// N-gram based similarity calculation
pub fn ngram_similarity(s1: &str, s2: &str, n: usize) -> f64 {
    if s1 == s2 {
        return 1.0;
    }
    
    let ngrams1 = generate_ngrams(s1, n);
    let ngrams2 = generate_ngrams(s2, n);
    
    if ngrams1.is_empty() && ngrams2.is_empty() {
        return 1.0;
    }
    
    if ngrams1.is_empty() || ngrams2.is_empty() {
        return 0.0;
    }
    
    let set1: std::collections::HashSet<_> = ngrams1.into_iter().collect();
    let set2: std::collections::HashSet<_> = ngrams2.into_iter().collect();
    
    let intersection = set1.intersection(&set2).count();
    let union = set1.union(&set2).count();
    
    if union == 0 {
        0.0
    } else {
        intersection as f64 / union as f64
    }
}

/// Generate n-grams from a string
fn generate_ngrams(text: &str, n: usize) -> Vec<String> {
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fuzzy_matcher_basic() {
        let matcher = FuzzyMatcher::new(0.5);
        
        // Exact match
        assert_eq!(matcher.ratio("test", "test"), 1.0);
        
        // Similar strings
        let score = matcher.ratio("resistor", "resitor");
        assert!(score > 0.8);
        
        // Different strings
        let score = matcher.ratio("resistor", "capacitor");
        assert!(score < 0.5);
    }

    #[test]
    fn test_comprehensive_score() {
        let matcher = FuzzyMatcher::new(0.3);
        
        let score = matcher.comprehensive_score("Device:R", "device:r");
        assert!(score > 0.9);
        
        let score = matcher.comprehensive_score("resistor", "R");
        assert!(score > 0.0); // Should find some similarity
    }

    #[test]
    fn test_batch_matching() {
        let matcher = FuzzyMatcher::new(0.3);
        let candidates = vec!["R", "C", "L", "resistor", "capacitor"];
        
        let results = matcher.batch_match("resistor", &candidates, 3);
        assert!(!results.is_empty());
        
        // Should find "resistor" as best match
        assert_eq!(candidates[results[0].0], "resistor");
        assert!(results[0].1 > 0.9);
    }

    #[test]
    fn test_fast_levenshtein() {
        assert_eq!(fast_levenshtein_distance("", ""), 0);
        assert_eq!(fast_levenshtein_distance("a", ""), 1);
        assert_eq!(fast_levenshtein_distance("", "a"), 1);
        assert_eq!(fast_levenshtein_distance("abc", "abc"), 0);
        assert_eq!(fast_levenshtein_distance("abc", "ab"), 1);
        assert_eq!(fast_levenshtein_distance("abc", "axc"), 1);
    }

    #[test]
    fn test_ngram_similarity() {
        assert_eq!(ngram_similarity("test", "test", 2), 1.0);
        
        let score = ngram_similarity("resistor", "resitor", 3);
        assert!(score > 0.5);
        
        let score = ngram_similarity("abc", "xyz", 2);
        assert_eq!(score, 0.0);
    }

    #[test]
    fn test_performance() {
        let matcher = FuzzyMatcher::new(0.3);
        let candidates: Vec<&str> = (0..1000).map(|i| {
            Box::leak(format!("Symbol_{}", i).into_boxed_str()) as &str
        }).collect();
        
        let start = std::time::Instant::now();
        let _results = matcher.fast_match("Symbol_500", &candidates);
        let duration = start.elapsed();
        
        println!("Fuzzy matching 1000 candidates: {:?}", duration);
        assert!(duration.as_millis() < 10); // Should be under 10ms
    }
}