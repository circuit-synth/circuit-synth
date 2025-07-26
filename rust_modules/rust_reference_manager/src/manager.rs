//! Core reference manager implementation
//! 
//! This module provides the main ReferenceManager struct that handles
//! reference generation, validation, and hierarchy management with
//! high performance and thread safety.

use crate::errors::{ReferenceError, ValidationError};
use crate::hierarchy::{HierarchyNode, ReferenceHierarchy};
use crate::validation::ReferenceValidator;

use ahash::{AHashSet, AHashMap};
use parking_lot::RwLock;
use std::sync::atomic::{AtomicU32, AtomicU64, Ordering};
use std::sync::Arc;
use std::time::Instant;
use std::collections::HashMap;

/// Thread-safe, high-performance reference manager
#[derive(Debug)]
pub struct ReferenceManager {
    /// Unique identifier for this manager instance
    id: u64,
    
    /// Set of used references in this manager
    used_references: Arc<RwLock<AHashSet<String>>>,
    
    /// Counters for each prefix
    prefix_counters: Arc<RwLock<AHashMap<String, AtomicU32>>>,
    
    /// Counter for unnamed nets
    unnamed_net_counter: AtomicU32,
    
    /// Hierarchy management
    hierarchy: Arc<RwLock<HierarchyNode>>,
    
    /// Reference validator
    validator: ReferenceValidator,
    
    /// Performance tracking
    stats: Arc<RwLock<ManagerStats>>,
}

/// Performance statistics for the reference manager
#[derive(Debug, Clone)]
pub struct ManagerStats {
    pub references_generated: u64,
    pub validations_performed: u64,
    pub hierarchy_lookups: u64,
    pub total_generation_time_ns: u64,
    pub total_validation_time_ns: u64,
    pub avg_generation_time_ns: f64,
    pub avg_validation_time_ns: f64,
    pub created_at: Instant,
}

impl Default for ManagerStats {
    fn default() -> Self {
        Self {
            references_generated: 0,
            validations_performed: 0,
            hierarchy_lookups: 0,
            total_generation_time_ns: 0,
            total_validation_time_ns: 0,
            avg_generation_time_ns: 0.0,
            avg_validation_time_ns: 0.0,
            created_at: Instant::now(),
        }
    }
}

impl ManagerStats {
    fn update_generation_time(&mut self, duration_ns: u64) {
        self.references_generated += 1;
        self.total_generation_time_ns += duration_ns;
        self.avg_generation_time_ns = self.total_generation_time_ns as f64 / self.references_generated as f64;
    }
    
    fn update_validation_time(&mut self, duration_ns: u64) {
        self.validations_performed += 1;
        self.total_validation_time_ns += duration_ns;
        self.avg_validation_time_ns = self.total_validation_time_ns as f64 / self.validations_performed as f64;
    }
}

static MANAGER_ID_COUNTER: AtomicU64 = AtomicU64::new(1);

impl ReferenceManager {
    /// Create a new reference manager
    pub fn new() -> Self {
        let id = MANAGER_ID_COUNTER.fetch_add(1, Ordering::SeqCst);
        
        Self {
            id,
            used_references: Arc::new(RwLock::new(AHashSet::new())),
            prefix_counters: Arc::new(RwLock::new(AHashMap::new())),
            unnamed_net_counter: AtomicU32::new(1),
            hierarchy: Arc::new(RwLock::new(HierarchyNode::new(id))),
            validator: ReferenceValidator::new(),
            stats: Arc::new(RwLock::new(ManagerStats::default())),
        }
    }

    /// Create a new reference manager with initial counters
    pub fn with_initial_counters(counters: HashMap<String, u32>) -> Self {
        let mut manager = Self::new();
        manager.set_initial_counters(counters);
        manager
    }

    /// Get the unique ID of this manager
    pub fn get_id(&self) -> u64 {
        self.id
    }

    /// Set the parent reference manager
    pub fn set_parent(&mut self, parent_id: Option<u64>) -> Result<(), ReferenceError> {
        let mut hierarchy = self.hierarchy.write();
        hierarchy.set_parent(parent_id)?;
        Ok(())
    }

    /// Register a new reference if it's unique in the hierarchy
    pub fn register_reference(&mut self, reference: &str) -> Result<(), ReferenceError> {
        let start = Instant::now();
        
        // Validate the reference format
        self.validator.validate_format(reference)?;
        
        // Check if reference is available in hierarchy
        if !self.validate_reference(reference) {
            return Err(ReferenceError::Validation(ValidationError::AlreadyInUse {
                reference: reference.to_string(),
            }));
        }
        
        // Register the reference
        {
            let mut used_refs = self.used_references.write();
            used_refs.insert(reference.to_string());
        }
        
        // Update statistics
        let duration = start.elapsed();
        {
            let mut stats = self.stats.write();
            stats.update_validation_time(duration.as_nanos() as u64);
        }
        
        #[cfg(feature = "logging")]
        log::debug!("Registered reference: {}", reference);
        Ok(())
    }

    /// Validate if a reference is available across the entire hierarchy
    pub fn validate_reference(&self, reference: &str) -> bool {
        let start = Instant::now();
        
        // Check local references
        {
            let used_refs = self.used_references.read();
            if used_refs.contains(reference) {
                return false;
            }
        }
        
        // Check hierarchy
        let hierarchy = self.hierarchy.read();
        let is_available = hierarchy.is_reference_available(reference);
        
        // Update statistics
        let duration = start.elapsed();
        {
            let mut stats = self.stats.write();
            stats.update_validation_time(duration.as_nanos() as u64);
            stats.hierarchy_lookups += 1;
        }
        
        is_available
    }

    /// Generate the next available reference for a prefix
    pub fn generate_next_reference(&mut self, prefix: &str) -> Result<String, ReferenceError> {
        let start = Instant::now();
        
        // Validate prefix format
        self.validator.validate_prefix(prefix)?;
        
        // Get or create counter for this prefix
        let counter = {
            let counters = self.prefix_counters.read();
            if let Some(counter) = counters.get(prefix) {
                counter.load(Ordering::SeqCst)
            } else {
                // Need to create new counter
                drop(counters);
                let mut counters = self.prefix_counters.write();
                counters.entry(prefix.to_string())
                    .or_insert_with(|| AtomicU32::new(1))
                    .load(Ordering::SeqCst)
            }
        };
        
        // Find next available reference
        let mut current_counter = counter;
        loop {
            let candidate = format!("{}{}", prefix, current_counter);
            
            if self.validate_reference(&candidate) {
                // Register the reference
                self.register_reference(&candidate)?;
                
                // Update the counter
                {
                    let counters = self.prefix_counters.read();
                    if let Some(atomic_counter) = counters.get(prefix) {
                        atomic_counter.store(current_counter + 1, Ordering::SeqCst);
                    }
                }
                
                // Update statistics
                let duration = start.elapsed();
                {
                    let mut stats = self.stats.write();
                    stats.update_generation_time(duration.as_nanos() as u64);
                }
                
                #[cfg(feature = "logging")]
                log::debug!("Generated reference: {}", candidate);
                return Ok(candidate);
            }
            
            current_counter += 1;
            
            // Prevent infinite loops (safety check)
            if current_counter > 1_000_000 {
                return Err(ReferenceError::Validation(ValidationError::CounterOverflow {
                    prefix: prefix.to_string(),
                    max_value: 1_000_000,
                }));
            }
        }
    }

    /// Generate the next unnamed net name (e.g., N$1, N$2, ...)
    pub fn generate_next_unnamed_net_name(&mut self) -> String {
        let counter = self.unnamed_net_counter.fetch_add(1, Ordering::SeqCst);
        let name = format!("N${}", counter);
        #[cfg(feature = "logging")]
        log::debug!("Generated unnamed net: {}", name);
        name
    }

    /// Set initial counters for reference generation
    pub fn set_initial_counters(&mut self, counters: HashMap<String, u32>) {
        let mut prefix_counters = self.prefix_counters.write();
        
        for (prefix, start_num) in counters {
            let current_value = prefix_counters
                .get(&prefix)
                .map(|c| c.load(Ordering::SeqCst))
                .unwrap_or(1);
            
            if start_num > current_value {
                prefix_counters.insert(prefix.clone(), AtomicU32::new(start_num));
                #[cfg(feature = "logging")]
                log::debug!("Set initial counter for prefix {}: {}", prefix, start_num);
            }
        }
    }

    /// Get all used references in this manager and its hierarchy
    pub fn get_all_used_references(&self) -> Vec<String> {
        let mut all_refs = Vec::new();
        
        // Get local references
        {
            let used_refs = self.used_references.read();
            all_refs.extend(used_refs.iter().cloned());
        }
        
        // Get hierarchy references
        let hierarchy = self.hierarchy.read();
        all_refs.extend(hierarchy.get_all_used_references());
        
        all_refs.sort();
        all_refs.dedup();
        all_refs
    }

    /// Clear all references and reset state
    pub fn clear(&mut self) {
        {
            let mut used_refs = self.used_references.write();
            used_refs.clear();
        }
        
        {
            let mut counters = self.prefix_counters.write();
            counters.clear();
        }
        
        self.unnamed_net_counter.store(1, Ordering::SeqCst);
        
        {
            let mut hierarchy = self.hierarchy.write();
            hierarchy.clear();
        }
        
        {
            let mut stats = self.stats.write();
            *stats = ManagerStats::default();
        }
        
        #[cfg(feature = "logging")]
        log::debug!("Cleared reference manager {}", self.id);
    }

    /// Get performance statistics
    pub fn get_stats(&self) -> serde_json::Value {
        let stats = self.stats.read();
        let hierarchy = self.hierarchy.read();
        let used_refs = self.used_references.read();
        let counters = self.prefix_counters.read();
        
        serde_json::json!({
            "manager_id": self.id,
            "references_count": used_refs.len(),
            "prefix_counters_count": counters.len(),
            "unnamed_net_counter": self.unnamed_net_counter.load(Ordering::SeqCst),
            "performance": {
                "references_generated": stats.references_generated,
                "validations_performed": stats.validations_performed,
                "hierarchy_lookups": stats.hierarchy_lookups,
                "avg_generation_time_ns": stats.avg_generation_time_ns,
                "avg_validation_time_ns": stats.avg_validation_time_ns,
                "uptime_ms": stats.created_at.elapsed().as_millis()
            },
            "hierarchy": hierarchy.get_stats()
        })
    }
}

impl Default for ReferenceManager {
    fn default() -> Self {
        Self::new()
    }
}

// Thread safety: ReferenceManager is Send + Sync due to Arc<RwLock<_>> usage
unsafe impl Send for ReferenceManager {}
unsafe impl Sync for ReferenceManager {}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_manager_creation() {
        let manager1 = ReferenceManager::new();
        let manager2 = ReferenceManager::new();
        
        // Each manager should have unique ID
        assert_ne!(manager1.get_id(), manager2.get_id());
    }

    #[test]
    fn test_reference_registration() {
        let mut manager = ReferenceManager::new();
        
        // Should be able to register new reference
        assert!(manager.register_reference("R1").is_ok());
        
        // Should not be able to register same reference again
        assert!(manager.register_reference("R1").is_err());
    }

    #[test]
    fn test_reference_generation() {
        let mut manager = ReferenceManager::new();
        
        let ref1 = manager.generate_next_reference("R").unwrap();
        assert_eq!(ref1, "R1");
        
        let ref2 = manager.generate_next_reference("R").unwrap();
        assert_eq!(ref2, "R2");
        
        // Different prefix should start from 1
        let ref3 = manager.generate_next_reference("C").unwrap();
        assert_eq!(ref3, "C1");
    }

    #[test]
    fn test_concurrent_access() {
        use std::sync::Arc;
        use std::thread;
        
        let manager = Arc::new(parking_lot::Mutex::new(ReferenceManager::new()));
        let mut handles = vec![];
        
        // Spawn multiple threads generating references
        for i in 0..10 {
            let manager_clone = Arc::clone(&manager);
            let handle = thread::spawn(move || {
                let mut mgr = manager_clone.lock();
                let prefix = format!("T{}", char::from(b'A' + i as u8));
                mgr.generate_next_reference(&prefix).unwrap()
            });
            handles.push(handle);
        }
        
        // Collect results
        let mut results = vec![];
        for handle in handles {
            results.push(handle.join().unwrap());
        }
        
        // All results should be unique
        results.sort();
        results.dedup();
        assert_eq!(results.len(), 10);
    }

    #[test]
    fn test_performance_stats() {
        let mut manager = ReferenceManager::new();
        
        // Generate some references
        for i in 1..=100 {
            let prefix = if i % 2 == 0 { "R" } else { "C" };
            manager.generate_next_reference(prefix).unwrap();
        }
        
        let stats = manager.get_stats();
        assert!(stats["performance"]["references_generated"].as_u64().unwrap() > 0);
        assert!(stats["performance"]["avg_generation_time_ns"].as_f64().unwrap() > 0.0);
    }
}