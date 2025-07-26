//! Hierarchical reference management
//! 
//! This module provides the hierarchy management functionality that allows
//! reference managers to be organized in parent-child relationships,
//! ensuring reference uniqueness across the entire hierarchy.

use crate::errors::ReferenceError;
use ahash::{AHashSet, AHashMap};
use parking_lot::RwLock;
use std::sync::{Arc, Weak};
use std::collections::HashMap;

/// A node in the reference hierarchy
#[derive(Debug)]
pub struct HierarchyNode {
    /// Unique identifier for this node
    id: u64,
    
    /// Parent node (weak reference to avoid cycles)
    parent: Option<Weak<RwLock<HierarchyNode>>>,
    
    /// Child nodes
    children: AHashMap<u64, Arc<RwLock<HierarchyNode>>>,
    
    /// References used by this node
    local_references: AHashSet<String>,
}

impl HierarchyNode {
    /// Create a new hierarchy node
    pub fn new(id: u64) -> Self {
        Self {
            id,
            parent: None,
            children: AHashMap::new(),
            local_references: AHashSet::new(),
        }
    }

    /// Set the parent of this node
    pub fn set_parent(&mut self, parent_id: Option<u64>) -> Result<(), ReferenceError> {
        match parent_id {
            Some(id) => {
                // In a real implementation, we would need a global registry
                // For now, we'll just store the ID
                #[cfg(feature = "logging")]
                #[cfg(feature = "logging")]
        log::debug!("Setting parent {} for node {}", id, self.id);
                // TODO: Implement proper parent linking with global registry
            }
            None => {
                self.parent = None;
                #[cfg(feature = "logging")]
        log::debug!("Removed parent for node {}", self.id);
            }
        }
        Ok(())
    }

    /// Add a child node
    pub fn add_child(&mut self, child: Arc<RwLock<HierarchyNode>>) {
        let child_id = child.read().id;
        self.children.insert(child_id, child);
        #[cfg(feature = "logging")]
        log::debug!("Added child {} to node {}", child_id, self.id);
    }

    /// Remove a child node
    pub fn remove_child(&mut self, child_id: u64) {
        self.children.remove(&child_id);
        #[cfg(feature = "logging")]
        log::debug!("Removed child {} from node {}", child_id, self.id);
    }

    /// Check if a reference is available in this hierarchy
    pub fn is_reference_available(&self, reference: &str) -> bool {
        // Check local references
        if self.local_references.contains(reference) {
            return false;
        }

        // Check parent hierarchy
        if let Some(parent_weak) = &self.parent {
            if let Some(parent) = parent_weak.upgrade() {
                let parent_node = parent.read();
                if !parent_node.is_reference_available(reference) {
                    return false;
                }
            }
        }

        // Check children
        for child in self.children.values() {
            let child_node = child.read();
            if !child_node.is_reference_available(reference) {
                return false;
            }
        }

        true
    }

    /// Add a reference to this node
    pub fn add_reference(&mut self, reference: String) {
        self.local_references.insert(reference);
    }

    /// Remove a reference from this node
    pub fn remove_reference(&mut self, reference: &str) {
        self.local_references.remove(reference);
    }

    /// Get all references used in this subtree
    pub fn get_all_used_references(&self) -> Vec<String> {
        let mut all_refs = Vec::new();
        
        // Add local references
        all_refs.extend(self.local_references.iter().cloned());
        
        // Add children references
        for child in self.children.values() {
            let child_node = child.read();
            all_refs.extend(child_node.get_all_used_references());
        }
        
        all_refs
    }

    /// Clear all references and children
    pub fn clear(&mut self) {
        self.local_references.clear();
        self.children.clear();
        self.parent = None;
        #[cfg(feature = "logging")]
        log::debug!("Cleared hierarchy node {}", self.id);
    }

    /// Get statistics for this hierarchy node
    pub fn get_stats(&self) -> serde_json::Value {
        serde_json::json!({
            "node_id": self.id,
            "local_references_count": self.local_references.len(),
            "children_count": self.children.len(),
            "has_parent": self.parent.is_some(),
            "total_references_in_subtree": self.get_all_used_references().len()
        })
    }

    /// Get the depth of this node in the hierarchy
    pub fn get_depth(&self) -> usize {
        match &self.parent {
            Some(parent_weak) => {
                if let Some(parent) = parent_weak.upgrade() {
                    let parent_node = parent.read();
                    parent_node.get_depth() + 1
                } else {
                    0
                }
            }
            None => 0,
        }
    }

    /// Get the root node of this hierarchy
    pub fn get_root(&self) -> Option<Arc<RwLock<HierarchyNode>>> {
        match &self.parent {
            Some(parent_weak) => {
                if let Some(parent) = parent_weak.upgrade() {
                    let parent_node = parent.read();
                    parent_node.get_root().or_else(|| Some(parent.clone()))
                } else {
                    None
                }
            }
            None => None,
        }
    }
}

/// Global hierarchy manager for coordinating multiple reference managers
#[derive(Debug)]
pub struct ReferenceHierarchy {
    /// Global registry of all hierarchy nodes
    nodes: Arc<RwLock<AHashMap<u64, Arc<RwLock<HierarchyNode>>>>>,
    
    /// Root nodes (nodes without parents)
    roots: Arc<RwLock<AHashSet<u64>>>,
}

impl ReferenceHierarchy {
    /// Create a new reference hierarchy
    pub fn new() -> Self {
        Self {
            nodes: Arc::new(RwLock::new(AHashMap::new())),
            roots: Arc::new(RwLock::new(AHashSet::new())),
        }
    }

    /// Register a new node in the hierarchy
    pub fn register_node(&self, node: Arc<RwLock<HierarchyNode>>) {
        let node_id = node.read().id;
        
        {
            let mut nodes = self.nodes.write();
            nodes.insert(node_id, node.clone());
        }
        
        {
            let mut roots = self.roots.write();
            roots.insert(node_id);
        }
        
        #[cfg(feature = "logging")]
        log::debug!("Registered hierarchy node {}", node_id);
    }

    /// Set parent-child relationship between nodes
    pub fn set_parent_child(&self, child_id: u64, parent_id: Option<u64>) -> Result<(), ReferenceError> {
        let nodes = self.nodes.read();
        
        let child_node = nodes.get(&child_id)
            .ok_or_else(|| ReferenceError::HierarchyError(format!("Child node {} not found", child_id)))?;

        match parent_id {
            Some(pid) => {
                let parent_node = nodes.get(&pid)
                    .ok_or_else(|| ReferenceError::HierarchyError(format!("Parent node {} not found", pid)))?;

                // Set up parent-child relationship
                {
                    let mut child = child_node.write();
                    child.parent = Some(Arc::downgrade(parent_node));
                }
                
                {
                    let mut parent = parent_node.write();
                    parent.add_child(child_node.clone());
                }

                // Remove child from roots if it was there
                {
                    let mut roots = self.roots.write();
                    roots.remove(&child_id);
                }

                #[cfg(feature = "logging")]
        log::debug!("Set parent {} for child {}", pid, child_id);
            }
            None => {
                // Remove parent relationship
                let old_parent_id = {
                    let mut child = child_node.write();
                    let old_parent = child.parent.take();
                    old_parent.and_then(|p| p.upgrade().map(|parent| parent.read().id))
                };

                // Remove from old parent's children
                if let Some(old_pid) = old_parent_id {
                    if let Some(old_parent_node) = nodes.get(&old_pid) {
                        let mut old_parent = old_parent_node.write();
                        old_parent.remove_child(child_id);
                    }
                }

                // Add to roots
                {
                    let mut roots = self.roots.write();
                    roots.insert(child_id);
                }

                #[cfg(feature = "logging")]
        log::debug!("Removed parent for child {}", child_id);
            }
        }

        Ok(())
    }

    /// Check if a reference is available across the entire hierarchy
    pub fn is_reference_available_globally(&self, reference: &str) -> bool {
        let roots = self.roots.read();
        let nodes = self.nodes.read();

        // Check all root nodes (which will recursively check their subtrees)
        for root_id in roots.iter() {
            if let Some(root_node) = nodes.get(root_id) {
                let root = root_node.read();
                if !root.is_reference_available(reference) {
                    return false;
                }
            }
        }

        true
    }

    /// Get all used references across the entire hierarchy
    pub fn get_all_used_references(&self) -> Vec<String> {
        let mut all_refs = Vec::new();
        let roots = self.roots.read();
        let nodes = self.nodes.read();

        for root_id in roots.iter() {
            if let Some(root_node) = nodes.get(root_id) {
                let root = root_node.read();
                all_refs.extend(root.get_all_used_references());
            }
        }

        all_refs.sort();
        all_refs.dedup();
        all_refs
    }

    /// Get statistics for the entire hierarchy
    pub fn get_hierarchy_stats(&self) -> serde_json::Value {
        let nodes = self.nodes.read();
        let roots = self.roots.read();

        let total_nodes = nodes.len();
        let root_count = roots.len();
        let total_references = self.get_all_used_references().len();

        serde_json::json!({
            "total_nodes": total_nodes,
            "root_nodes": root_count,
            "total_references": total_references,
            "max_depth": self.get_max_depth(),
            "node_details": nodes.values().map(|node| {
                let n = node.read();
                n.get_stats()
            }).collect::<Vec<_>>()
        })
    }

    /// Get the maximum depth of the hierarchy
    pub fn get_max_depth(&self) -> usize {
        let nodes = self.nodes.read();
        nodes.values()
            .map(|node| node.read().get_depth())
            .max()
            .unwrap_or(0)
    }

    /// Clear the entire hierarchy
    pub fn clear(&self) {
        {
            let mut nodes = self.nodes.write();
            for node in nodes.values() {
                let mut n = node.write();
                n.clear();
            }
            nodes.clear();
        }

        {
            let mut roots = self.roots.write();
            roots.clear();
        }

        #[cfg(feature = "logging")]
        log::debug!("Cleared entire reference hierarchy");
    }
}

impl Default for ReferenceHierarchy {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hierarchy_node_creation() {
        let node = HierarchyNode::new(1);
        assert_eq!(node.id, 1);
        assert!(node.parent.is_none());
        assert!(node.children.is_empty());
        assert!(node.local_references.is_empty());
    }

    #[test]
    fn test_reference_availability() {
        let mut node = HierarchyNode::new(1);
        
        // Initially available
        assert!(node.is_reference_available("R1"));
        
        // Add reference and check availability
        node.add_reference("R1".to_string());
        assert!(!node.is_reference_available("R1"));
        
        // Remove reference and check availability
        node.remove_reference("R1");
        assert!(node.is_reference_available("R1"));
    }

    #[test]
    fn test_hierarchy_management() {
        let hierarchy = ReferenceHierarchy::new();
        
        let node1 = Arc::new(RwLock::new(HierarchyNode::new(1)));
        let node2 = Arc::new(RwLock::new(HierarchyNode::new(2)));
        
        hierarchy.register_node(node1.clone());
        hierarchy.register_node(node2.clone());
        
        // Set parent-child relationship
        hierarchy.set_parent_child(2, Some(1)).unwrap();
        
        // Add reference to parent
        {
            let mut parent = node1.write();
            parent.add_reference("R1".to_string());
        }
        
        // Child should not be able to use parent's reference
        {
            let child = node2.read();
            assert!(!child.is_reference_available("R1"));
        }
    }

    #[test]
    fn test_global_reference_availability() {
        let hierarchy = ReferenceHierarchy::new();
        
        let node1 = Arc::new(RwLock::new(HierarchyNode::new(1)));
        let node2 = Arc::new(RwLock::new(HierarchyNode::new(2)));
        
        hierarchy.register_node(node1.clone());
        hierarchy.register_node(node2.clone());
        
        // Initially available globally
        assert!(hierarchy.is_reference_available_globally("R1"));
        
        // Add to one node
        {
            let mut n1 = node1.write();
            n1.add_reference("R1".to_string());
        }
        
        // Should not be available globally
        assert!(!hierarchy.is_reference_available_globally("R1"));
    }

    #[test]
    fn test_hierarchy_stats() {
        let hierarchy = ReferenceHierarchy::new();
        
        let node1 = Arc::new(RwLock::new(HierarchyNode::new(1)));
        let node2 = Arc::new(RwLock::new(HierarchyNode::new(2)));
        
        hierarchy.register_node(node1.clone());
        hierarchy.register_node(node2.clone());
        
        let stats = hierarchy.get_hierarchy_stats();
        assert_eq!(stats["total_nodes"].as_u64().unwrap(), 2);
        assert_eq!(stats["root_nodes"].as_u64().unwrap(), 2);
    }
}