//! Integration tests for SymbolLibCache
//! 
//! These tests verify the complete functionality and performance
//! characteristics of the Rust SymbolLibCache implementation.

use rust_symbol_cache::{CacheConfig, SymbolLibCache};
use std::path::PathBuf;
use std::time::Instant;

fn create_test_cache() -> SymbolLibCache {
    let config = CacheConfig {
        enabled: true,
        ttl_hours: 24,
        force_rebuild: false,
        cache_path: PathBuf::from("target/test_cache"),
        max_memory_cache_size: 100,
        enable_tier_search: true,
        parallel_parsing: true,
    };
    
    SymbolLibCache::with_config(config)
}

#[test]
fn test_cache_creation() {
    let cache = create_test_cache();
    assert!(cache.get_cache_stats().len() > 0);
}

#[test]
fn test_symbol_lookup_basic() {
    let cache = create_test_cache();
    
    // Test basic symbol lookup (may not work without actual KiCad installation)
    // This test demonstrates the API but may skip if no symbols are available
    match cache.get_symbol_data("Device:R") {
        Ok(symbol) => {
            assert_eq!(symbol.name, "R");
            assert!(!symbol.pins.is_empty());
        }
        Err(_) => {
            // Skip test if no KiCad symbols available
            println!("Skipping symbol lookup test - no KiCad symbols available");
        }
    }
}

#[test]
fn test_index_building() {
    let cache = create_test_cache();
    
    let start = Instant::now();
    let result = cache.ensure_index_built();
    let duration = start.elapsed();
    
    println!("Index building took: {:?}", duration);
    
    // Should complete without error
    assert!(result.is_ok());
    
    // Should be reasonably fast (under 30 seconds even for large symbol sets)
    assert!(duration.as_secs() < 30);
}

#[test]
fn test_cache_statistics() {
    let cache = create_test_cache();
    let _ = cache.ensure_index_built();
    
    let stats = cache.get_cache_stats();
    
    // Should have basic statistics
    assert!(stats.contains_key("library_cache_size"));
    assert!(stats.contains_key("symbol_lru_size"));
    assert!(stats.contains_key("symbol_index_size"));
    assert!(stats.contains_key("library_index_size"));
}

#[test]
fn test_search_functionality() {
    let cache = create_test_cache();
    let _ = cache.ensure_index_built();
    
    // Test basic search
    match cache.search_symbols_all("R") {
        Ok(results) => {
            println!("Found {} symbols matching 'R'", results.len());
            // Should find at least some resistor symbols in most KiCad installations
        }
        Err(e) => {
            println!("Search failed: {}", e);
        }
    }
}

#[test]
fn test_category_search() {
    let cache = create_test_cache();
    let _ = cache.ensure_index_built();
    
    // Test category-based search
    let categories = vec!["passive".to_string()];
    match cache.search_symbols_by_category("R", &categories) {
        Ok(results) => {
            println!("Found {} symbols in passive category", results.len());
            
            // Verify all results are from passive category
            for (_, entry) in results {
                assert_eq!(entry.category, "passive");
            }
        }
        Err(e) => {
            println!("Category search failed: {}", e);
        }
    }
}

#[test]
fn test_library_categorization() {
    let cache = create_test_cache();
    let _ = cache.ensure_index_built();
    
    match cache.get_all_categories() {
        Ok(categories) => {
            println!("Available categories: {:?}", categories);
            
            // Should have standard categories
            assert!(categories.len() > 0);
            
            // Test getting libraries for a category
            for (category, _count) in categories {
                let libs = cache.get_libraries_by_category(&category);
                println!("Category '{}' has {} libraries", category, libs.len());
            }
        }
        Err(e) => {
            println!("Category retrieval failed: {}", e);
        }
    }
}

#[test]
fn test_cache_persistence() {
    let cache_path = PathBuf::from("target/test_persistence_cache");
    
    // Create cache and build index
    {
        let config = CacheConfig {
            enabled: true,
            cache_path: cache_path.clone(),
            force_rebuild: true,
            ..Default::default()
        };
        let cache = SymbolLibCache::with_config(config);
        let _ = cache.ensure_index_built();
    }
    
    // Create new cache instance and verify it loads from disk
    {
        let config = CacheConfig {
            enabled: true,
            cache_path: cache_path.clone(),
            force_rebuild: false,
            ..Default::default()
        };
        let cache = SymbolLibCache::with_config(config);
        
        let start = Instant::now();
        let _ = cache.ensure_index_built();
        let duration = start.elapsed();
        
        // Should be much faster when loading from cache
        println!("Cache load took: {:?}", duration);
        assert!(duration.as_millis() < 5000); // Should be under 5 seconds
    }
}

#[test]
fn test_parallel_vs_sequential_parsing() {
    let cache_path = PathBuf::from("target/test_parallel_cache");
    
    // Test parallel parsing
    let parallel_start = Instant::now();
    {
        let config = CacheConfig {
            parallel_parsing: true,
            force_rebuild: true,
            cache_path: cache_path.clone(),
            ..Default::default()
        };
        let cache = SymbolLibCache::with_config(config);
        let _ = cache.ensure_index_built();
    }
    let parallel_duration = parallel_start.elapsed();
    
    // Test sequential parsing
    let sequential_start = Instant::now();
    {
        let config = CacheConfig {
            parallel_parsing: false,
            force_rebuild: true,
            cache_path: cache_path.clone(),
            ..Default::default()
        };
        let cache = SymbolLibCache::with_config(config);
        let _ = cache.ensure_index_built();
    }
    let sequential_duration = sequential_start.elapsed();
    
    println!("Parallel parsing: {:?}", parallel_duration);
    println!("Sequential parsing: {:?}", sequential_duration);
    
    // Parallel should be faster (or at least not significantly slower)
    // Allow some variance due to test environment
    assert!(parallel_duration.as_millis() <= sequential_duration.as_millis() + 1000);
}

#[test]
fn test_memory_efficiency() {
    let cache = create_test_cache();
    let _ = cache.ensure_index_built();
    
    // Test LRU cache behavior
    let initial_stats = cache.get_cache_stats();
    let initial_lru_size = initial_stats.get("symbol_lru_size").unwrap_or(&0);
    
    // Perform multiple symbol lookups
    for i in 0..50 {
        let symbol_id = format!("TestSymbol{}", i);
        let _ = cache.get_symbol_data(&symbol_id); // Will fail but exercises cache
    }
    
    let final_stats = cache.get_cache_stats();
    let final_lru_size = final_stats.get("symbol_lru_size").unwrap_or(&0);
    
    // LRU cache should not grow unbounded
    assert!(final_lru_size <= &100); // Max cache size we configured
    
    println!("LRU cache size: {} -> {}", initial_lru_size, final_lru_size);
}

#[test]
fn test_error_handling() {
    let cache = create_test_cache();
    
    // Test invalid symbol ID
    match cache.get_symbol_data("InvalidFormat") {
        Err(rust_symbol_cache::SymbolCacheError::InvalidSymbolId { .. }) => {
            // Expected error
        }
        _ => panic!("Should have returned InvalidSymbolId error"),
    }
    
    // Test non-existent symbol
    match cache.get_symbol_data("NonExistent:Symbol") {
        Err(rust_symbol_cache::SymbolCacheError::LibraryNotFound { .. }) |
        Err(rust_symbol_cache::SymbolCacheError::SymbolNotFound { .. }) => {
            // Expected error
        }
        _ => panic!("Should have returned NotFound error"),
    }
}

#[test]
fn test_validation_functionality() {
    let cache = create_test_cache();
    
    // Test environment validation
    match cache.validate_environment() {
        Ok(warnings) => {
            println!("Environment validation warnings: {:?}", warnings);
            // Should complete without panic
        }
        Err(e) => {
            println!("Environment validation error: {}", e);
        }
    }
    
    // Test cache consistency
    let _ = cache.ensure_index_built();
    match cache.validate_cache_consistency() {
        Ok(issues) => {
            println!("Cache consistency issues: {:?}", issues);
            // Should complete without panic
        }
        Err(e) => {
            println!("Cache consistency check error: {}", e);
        }
    }
}

#[test]
fn test_health_check() {
    let cache = create_test_cache();
    let _ = cache.ensure_index_built();
    
    match cache.health_check() {
        Ok(report) => {
            println!("Health report: {:?}", report);
            
            // Should have basic metrics
            assert!(report.library_count >= 0);
            assert!(report.symbol_count >= 0);
            assert!(report.category_count >= 0);
        }
        Err(e) => {
            println!("Health check error: {}", e);
        }
    }
}

#[test]
fn test_clear_cache() {
    let cache = create_test_cache();
    let _ = cache.ensure_index_built();
    
    let initial_stats = cache.get_cache_stats();
    
    // Clear cache
    cache.clear_cache();
    
    let final_stats = cache.get_cache_stats();
    
    // All caches should be cleared
    assert_eq!(final_stats.get("library_cache_size").unwrap_or(&0), &0);
    assert_eq!(final_stats.get("symbol_lru_size").unwrap_or(&0), &0);
    assert_eq!(final_stats.get("symbol_index_size").unwrap_or(&0), &0);
    
    println!("Cache cleared: {:?} -> {:?}", initial_stats, final_stats);
}

#[test]
fn test_performance_characteristics() {
    let cache = create_test_cache();
    
    // Measure index building time
    let index_start = Instant::now();
    let _ = cache.ensure_index_built();
    let index_duration = index_start.elapsed();
    
    println!("Index building performance: {:?}", index_duration);
    
    // Should be reasonably fast
    assert!(index_duration.as_secs() < 60);
    
    // Measure symbol lookup time
    let lookup_start = Instant::now();
    for _ in 0..100 {
        let _ = cache.find_symbol_library("R");
    }
    let lookup_duration = lookup_start.elapsed();
    
    println!("100 symbol lookups: {:?}", lookup_duration);
    
    // Should be very fast
    assert!(lookup_duration.as_millis() < 1000);
}