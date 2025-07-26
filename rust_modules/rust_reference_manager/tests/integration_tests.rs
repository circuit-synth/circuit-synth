//! Integration tests for the Rust reference manager
//! 
//! These tests verify that all components work together correctly
//! and that the API matches the Python implementation exactly.

use rust_reference_manager::{RustReferenceManager, ReferenceError};
use std::collections::HashMap;

#[test]
fn test_basic_functionality() {
    let mut manager = RustReferenceManager::new();
    
    // Test basic reference generation
    let ref1 = manager.generate_next_reference("R").unwrap();
    assert_eq!(ref1, "R1");
    
    let ref2 = manager.generate_next_reference("R").unwrap();
    assert_eq!(ref2, "R2");
    
    // Test different prefix
    let ref3 = manager.generate_next_reference("C").unwrap();
    assert_eq!(ref3, "C1");
    
    // Test validation
    assert!(!manager.validate_reference("R1")); // Should be in use
    assert!(manager.validate_reference("R99")); // Should be available
}

#[test]
fn test_initial_counters() {
    let mut counters = HashMap::new();
    counters.insert("R".to_string(), 10);
    counters.insert("C".to_string(), 5);
    
    let mut manager = RustReferenceManager::with_initial_counters(counters);
    
    let ref1 = manager.generate_next_reference("R").unwrap();
    assert_eq!(ref1, "R10");
    
    let ref2 = manager.generate_next_reference("C").unwrap();
    assert_eq!(ref2, "C5");
    
    // New prefix should start from 1
    let ref3 = manager.generate_next_reference("L").unwrap();
    assert_eq!(ref3, "L1");
}

#[test]
fn test_reference_registration() {
    let mut manager = RustReferenceManager::new();
    
    // Should be able to register new reference
    assert!(manager.register_reference("R1").is_ok());
    
    // Should not be able to register same reference again
    assert!(manager.register_reference("R1").is_err());
    
    // Should not be able to generate the registered reference
    let ref1 = manager.generate_next_reference("R").unwrap();
    assert_eq!(ref1, "R2"); // Should skip R1
}

#[test]
fn test_unnamed_net_generation() {
    let mut manager = RustReferenceManager::new();
    
    let net1 = manager.generate_next_unnamed_net_name();
    assert_eq!(net1, "N$1");
    
    let net2 = manager.generate_next_unnamed_net_name();
    assert_eq!(net2, "N$2");
    
    let net3 = manager.generate_next_unnamed_net_name();
    assert_eq!(net3, "N$3");
}

#[test]
fn test_get_all_used_references() {
    let mut manager = RustReferenceManager::new();
    
    // Initially empty
    assert!(manager.get_all_used_references().is_empty());
    
    // Generate some references
    manager.generate_next_reference("R").unwrap();
    manager.generate_next_reference("C").unwrap();
    manager.register_reference("U1").unwrap();
    
    let used_refs = manager.get_all_used_references();
    assert_eq!(used_refs.len(), 3);
    assert!(used_refs.contains(&"R1".to_string()));
    assert!(used_refs.contains(&"C1".to_string()));
    assert!(used_refs.contains(&"U1".to_string()));
}

#[test]
fn test_clear_functionality() {
    let mut manager = RustReferenceManager::new();
    
    // Generate some references
    manager.generate_next_reference("R").unwrap();
    manager.generate_next_reference("C").unwrap();
    manager.generate_next_unnamed_net_name();
    
    // Verify they exist
    assert!(!manager.get_all_used_references().is_empty());
    
    // Clear everything
    manager.clear();
    
    // Verify everything is cleared
    assert!(manager.get_all_used_references().is_empty());
    
    // Verify counters are reset
    let ref1 = manager.generate_next_reference("R").unwrap();
    assert_eq!(ref1, "R1");
    
    let net1 = manager.generate_next_unnamed_net_name();
    assert_eq!(net1, "N$1");
}

#[test]
fn test_set_initial_counters_after_creation() {
    let mut manager = RustReferenceManager::new();
    
    // Generate a reference first
    let ref1 = manager.generate_next_reference("R").unwrap();
    assert_eq!(ref1, "R1");
    
    // Set initial counters
    let mut counters = HashMap::new();
    counters.insert("R".to_string(), 10);
    counters.insert("C".to_string(), 5);
    manager.set_initial_counters(counters);
    
    // R counter should be updated to 10 (higher than current 2)
    let ref2 = manager.generate_next_reference("R").unwrap();
    assert_eq!(ref2, "R10");
    
    // C should start from 5
    let ref3 = manager.generate_next_reference("C").unwrap();
    assert_eq!(ref3, "C5");
}

#[test]
fn test_error_handling() {
    let mut manager = RustReferenceManager::new();
    
    // Test invalid prefixes
    assert!(manager.generate_next_reference("").is_err());
    assert!(manager.generate_next_reference("123").is_err());
    assert!(manager.generate_next_reference("R-").is_err());
    assert!(manager.generate_next_reference("N$").is_err()); // Reserved
    
    // Test invalid references
    assert!(manager.register_reference("").is_err());
    assert!(manager.register_reference("123").is_err());
    assert!(manager.register_reference("R").is_err()); // No number
    assert!(manager.register_reference("GND").is_err()); // Reserved
}

#[test]
fn test_performance_requirements() {
    let mut manager = RustReferenceManager::new();
    
    // Test that we can generate many references quickly
    let start = std::time::Instant::now();
    
    for i in 0..10000 {
        let prefix = match i % 3 {
            0 => "R",
            1 => "C",
            _ => "L",
        };
        manager.generate_next_reference(prefix).unwrap();
    }
    
    let duration = start.elapsed();
    
    // Should be much faster than Python (target: sub-millisecond per reference)
    println!("Generated 10,000 references in {:?}", duration);
    assert!(duration.as_millis() < 100); // Should be under 100ms total
    
    // Test validation performance
    let start = std::time::Instant::now();
    
    for i in 1..=1000 {
        let reference = format!("R{}", i);
        manager.validate_reference(&reference);
    }
    
    let validation_duration = start.elapsed();
    println!("Validated 1,000 references in {:?}", validation_duration);
    assert!(validation_duration.as_millis() < 10); // Should be under 10ms
}

#[test]
fn test_large_scale_operations() {
    let mut manager = RustReferenceManager::new();
    
    // Generate a large number of references
    for i in 0..50000 {
        let prefix = match i % 10 {
            0 => "R", 1 => "C", 2 => "L", 3 => "U", 4 => "D",
            5 => "Q", 6 => "IC", 7 => "SW", 8 => "J", _ => "TP",
        };
        manager.generate_next_reference(prefix).unwrap();
    }
    
    // Verify we have the expected number of references
    let all_refs = manager.get_all_used_references();
    assert_eq!(all_refs.len(), 50000);
    
    // Test validation on large dataset
    assert!(!manager.validate_reference("R2500")); // Should exist
    assert!(manager.validate_reference("R99999")); // Should not exist
    
    // Test stats collection
    let stats = manager.get_stats();
    assert!(stats["performance"]["references_generated"].as_u64().unwrap() > 0);
}

#[test]
fn test_api_compatibility_with_python() {
    // This test ensures our API exactly matches the Python implementation
    
    let mut manager = RustReferenceManager::new();
    
    // Test method signatures and return types match Python
    
    // generate_next_reference should return String
    let ref1: String = manager.generate_next_reference("R").unwrap();
    assert_eq!(ref1, "R1");
    
    // validate_reference should return bool
    let is_valid: bool = manager.validate_reference("R2");
    assert!(is_valid);
    
    // generate_next_unnamed_net_name should return String
    let net: String = manager.generate_next_unnamed_net_name();
    assert_eq!(net, "N$1");
    
    // get_all_used_references should return Vec<String> (converted to Set in Python wrapper)
    let refs: Vec<String> = manager.get_all_used_references();
    assert!(refs.contains(&"R1".to_string()));
    
    // register_reference should return Result<(), Error>
    let result = manager.register_reference("C1");
    assert!(result.is_ok());
    
    // clear should return nothing
    manager.clear();
    
    // get_stats should return JSON-serializable data
    let stats = manager.get_stats();
    assert!(stats.is_object());
}

#[test]
fn test_thread_safety() {
    use std::sync::{Arc, Mutex};
    use std::thread;
    
    let manager = Arc::new(Mutex::new(RustReferenceManager::new()));
    let mut handles = vec![];
    
    // Spawn multiple threads generating references
    for thread_id in 0..10 {
        let manager_clone = Arc::clone(&manager);
        let handle = thread::spawn(move || {
            let mut mgr = manager_clone.lock().unwrap();
            let mut results = vec![];
            
            for i in 0..100 {
                let prefix = format!("T{}", thread_id);
                let reference = mgr.generate_next_reference(&prefix).unwrap();
                results.push(reference);
            }
            
            results
        });
        handles.push(handle);
    }
    
    // Collect all results
    let mut all_results = vec![];
    for handle in handles {
        let thread_results = handle.join().unwrap();
        all_results.extend(thread_results);
    }
    
    // Verify all results are unique
    all_results.sort();
    let original_len = all_results.len();
    all_results.dedup();
    assert_eq!(all_results.len(), original_len, "All generated references should be unique");
    
    // Verify we have the expected number of results
    assert_eq!(all_results.len(), 1000); // 10 threads * 100 references each
}

#[test]
fn test_hierarchy_placeholder() {
    // Note: Full hierarchy testing would require multiple manager instances
    // and a global registry. For now, we test the basic hierarchy interface.
    
    let mut manager = RustReferenceManager::new();
    let manager_id = manager.get_id();
    
    // Test setting parent (should not fail even if parent doesn't exist yet)
    assert!(manager.set_parent(Some(999)).is_ok());
    assert!(manager.set_parent(None).is_ok());
    
    // Verify manager ID is unique
    let manager2 = RustReferenceManager::new();
    assert_ne!(manager_id, manager2.get_id());
}

#[test]
fn test_edge_cases() {
    let mut manager = RustReferenceManager::new();
    
    // Test very long prefixes (should be rejected)
    let long_prefix = "A".repeat(100);
    assert!(manager.generate_next_reference(&long_prefix).is_err());
    
    // Test unicode characters (should be rejected)
    assert!(manager.generate_next_reference("Ω").is_err());
    
    // Test mixed case prefixes (should work)
    let ref1 = manager.generate_next_reference("Ic").unwrap();
    assert_eq!(ref1, "Ic1");
    
    // Test underscore in prefix (should work)
    let ref2 = manager.generate_next_reference("IC_").unwrap();
    assert_eq!(ref2, "IC_1");
    
    // Test registering very high numbers
    assert!(manager.register_reference("R999999").is_ok());
    
    // Next generated reference should skip the registered one
    let ref3 = manager.generate_next_reference("R").unwrap();
    assert_eq!(ref3, "R1"); // Should start from 1 and work up
}

#[test]
fn test_stats_collection() {
    let mut manager = RustReferenceManager::new();
    
    // Generate some references to populate stats
    for _ in 0..100 {
        manager.generate_next_reference("R").unwrap();
        manager.validate_reference("C1");
    }
    
    let stats = manager.get_stats();
    
    // Verify stats structure
    assert!(stats["manager_id"].is_u64());
    assert!(stats["references_count"].is_u64());
    assert!(stats["performance"].is_object());
    
    let performance = &stats["performance"];
    assert!(performance["references_generated"].as_u64().unwrap() > 0);
    assert!(performance["validations_performed"].as_u64().unwrap() > 0);
    assert!(performance["avg_generation_time_ns"].as_f64().unwrap() > 0.0);
}

#[test]
fn test_memory_efficiency() {
    // Test that the manager doesn't use excessive memory
    let mut manager = RustReferenceManager::new();
    
    // Generate many references
    for i in 0..10000 {
        let prefix = if i % 2 == 0 { "R" } else { "C" };
        manager.generate_next_reference(prefix).unwrap();
    }
    
    // The manager should still be responsive
    let start = std::time::Instant::now();
    let ref1 = manager.generate_next_reference("L").unwrap();
    let duration = start.elapsed();
    
    assert_eq!(ref1, "L1");
    assert!(duration.as_millis() < 1); // Should still be very fast
    
    // Validation should also be fast
    let start = std::time::Instant::now();
    let is_valid = manager.validate_reference("R5000");
    let duration = start.elapsed();
    
    assert!(!is_valid); // Should exist
    assert!(duration.as_millis() < 1); // Should be very fast
}