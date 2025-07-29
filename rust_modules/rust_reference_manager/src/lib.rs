//! High-performance reference manager for Circuit Synth
//!
//! This crate provides a Rust-based reference management implementation designed to replace
//! the Python ReferenceManager with significant performance improvements.
//!
//! Key features:
//! - Sub-millisecond reference generation and validation
//! - Thread-safe hierarchical reference management
//! - Memory-efficient data structures
//! - Python bindings via PyO3
//! - Integrated logging support

pub mod errors;
pub mod hierarchy;
pub mod manager;
pub mod validation;

#[cfg(feature = "python-bindings")]
pub mod python;

pub use errors::{ReferenceError, ValidationError};
pub use hierarchy::{HierarchyNode, ReferenceHierarchy};
pub use manager::ReferenceManager;
pub use validation::ReferenceValidator;

use std::collections::HashMap;

/// Main reference manager interface
#[derive(Debug)]
pub struct RustReferenceManager {
    manager: ReferenceManager,
}

impl RustReferenceManager {
    /// Create a new reference manager
    pub fn new() -> Self {
        Self {
            manager: ReferenceManager::new(),
        }
    }

    /// Create a new reference manager with initial counters
    pub fn with_initial_counters(counters: HashMap<String, u32>) -> Self {
        Self {
            manager: ReferenceManager::with_initial_counters(counters),
        }
    }

    /// Set parent reference manager
    pub fn set_parent(&mut self, parent_id: Option<u64>) -> Result<(), ReferenceError> {
        self.manager.set_parent(parent_id)
    }

    /// Register a new reference
    pub fn register_reference(&mut self, reference: &str) -> Result<(), ReferenceError> {
        self.manager.register_reference(reference)
    }

    /// Validate if a reference is available
    pub fn validate_reference(&self, reference: &str) -> bool {
        self.manager.validate_reference(reference)
    }

    /// Generate the next available reference for a prefix
    pub fn generate_next_reference(&mut self, prefix: &str) -> Result<String, ReferenceError> {
        self.manager.generate_next_reference(prefix)
    }

    /// Generate the next unnamed net name
    pub fn generate_next_unnamed_net_name(&mut self) -> String {
        self.manager.generate_next_unnamed_net_name()
    }

    /// Set initial counters for reference generation
    pub fn set_initial_counters(&mut self, counters: HashMap<String, u32>) {
        self.manager.set_initial_counters(counters);
    }

    /// Get all used references in the hierarchy
    pub fn get_all_used_references(&self) -> Vec<String> {
        self.manager.get_all_used_references()
    }

    /// Clear all references and reset state
    pub fn clear(&mut self) {
        self.manager.clear();
    }

    /// Get performance statistics
    pub fn get_stats(&self) -> serde_json::Value {
        self.manager.get_stats()
    }

    /// Get the manager ID
    pub fn get_id(&self) -> u64 {
        self.manager.get_id()
    }
}

impl Default for RustReferenceManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_reference_generation() {
        let mut manager = RustReferenceManager::new();

        let ref1 = manager.generate_next_reference("R").unwrap();
        assert_eq!(ref1, "R1");

        let ref2 = manager.generate_next_reference("R").unwrap();
        assert_eq!(ref2, "R2");

        let ref3 = manager.generate_next_reference("C").unwrap();
        assert_eq!(ref3, "C1");
    }

    #[test]
    fn test_reference_validation() {
        let mut manager = RustReferenceManager::new();

        // Initially available
        assert!(manager.validate_reference("R1"));

        // Register and check it's no longer available
        manager.register_reference("R1").unwrap();
        assert!(!manager.validate_reference("R1"));

        // Should fail to register again
        assert!(manager.register_reference("R1").is_err());
    }

    #[test]
    fn test_unnamed_net_generation() {
        let mut manager = RustReferenceManager::new();

        let net1 = manager.generate_next_unnamed_net_name();
        assert_eq!(net1, "N$1");

        let net2 = manager.generate_next_unnamed_net_name();
        assert_eq!(net2, "N$2");
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
    }

    #[test]
    fn test_performance() {
        let mut manager = RustReferenceManager::new();

        let start = std::time::Instant::now();

        // Generate 10,000 references
        for i in 0..10000 {
            let prefix = if i % 3 == 0 {
                "R"
            } else if i % 3 == 1 {
                "C"
            } else {
                "L"
            };
            manager.generate_next_reference(prefix).unwrap();
        }

        let duration = start.elapsed();
        println!("Generated 10,000 references in {:?}", duration);

        // Should be much faster than Python (target: sub-millisecond per reference)
        assert!(duration.as_millis() < 100); // Should be under 100ms total
    }

    #[test]
    fn test_hierarchy_validation() {
        let mut parent = RustReferenceManager::new();
        let mut child = RustReferenceManager::new();

        // Register reference in parent
        parent.register_reference("R1").unwrap();

        // Set up hierarchy (currently just stores the parent ID)
        let parent_id = parent.get_id();
        child.set_parent(Some(parent_id)).unwrap();

        // Note: Full hierarchy validation requires a global registry
        // For now, each manager validates independently
        assert!(!parent.validate_reference("R1")); // Parent has R1
        assert!(child.validate_reference("R1")); // Child doesn't have R1 yet

        // Child should be able to use different reference
        assert!(child.validate_reference("R2"));
    }
}
