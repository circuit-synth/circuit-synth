//! Hierarchical net processing engine
//!
//! This module implements high-performance hierarchical net processing with parallel
//! execution capabilities. It targets 30x performance improvement over the Python
//! implementation through optimized data structures and algorithms.

use crate::data_transform::{Circuit, Component, Net, NetNode};
use crate::errors::{NetlistError, Result};
use rayon::prelude::*;
use std::collections::{HashMap, HashSet};
use std::time::Instant;

/// High-performance net processor with parallel execution
pub struct NetProcessor {
    /// Net ownership mapping (net name -> owner circuit path)
    net_ownership: HashMap<String, String>,
    /// Set of hierarchical nets
    hierarchical_nets: HashSet<String>,
    /// Set of global nets (power, ground, etc.)
    global_nets: HashSet<String>,
    /// Set of local nets
    local_nets: HashSet<String>,
    /// Unconnected pins tracking
    unconnected_pins: HashSet<String>,
    /// Counter for auto-generated net names
    unnamed_net_counter: u32,
    /// Performance tracking
    last_processing_time: Option<std::time::Duration>,
    /// Memory usage estimation
    estimated_memory_usage: usize,
}

impl NetProcessor {
    /// Create a new net processor
    pub fn new() -> Self {
        Self {
            net_ownership: HashMap::new(),
            hierarchical_nets: HashSet::new(),
            global_nets: HashSet::new(),
            local_nets: HashSet::new(),
            unconnected_pins: HashSet::new(),
            unnamed_net_counter: 1,
            last_processing_time: None,
            estimated_memory_usage: 0,
        }
    }

    /// Get last processing time in milliseconds
    pub fn last_processing_time_ms(&self) -> f64 {
        self.last_processing_time
            .map(|d| d.as_secs_f64() * 1000.0)
            .unwrap_or(0.0)
    }

    /// Get estimated memory usage
    pub fn memory_usage(&self) -> usize {
        self.estimated_memory_usage
    }

    /// Generate the nets section for KiCad netlist
    pub fn generate_nets_section(&mut self, circuit: &Circuit) -> Result<String> {
        let start_time = Instant::now();

        // Clear previous state
        self.reset();

        // Process all nets and build the final net list
        let processed_nets = self.process_all_nets(circuit)?;

        // Generate the formatted nets section
        let nets_content = self.format_nets_section(&processed_nets)?;

        self.last_processing_time = Some(start_time.elapsed());
        self.update_memory_usage();

        Ok(nets_content)
    }

    /// Reset processor state
    fn reset(&mut self) {
        self.net_ownership.clear();
        self.hierarchical_nets.clear();
        self.global_nets.clear();
        self.local_nets.clear();
        self.unconnected_pins.clear();
        self.unnamed_net_counter = 1;
    }

    /// Process all nets in the circuit hierarchy
    fn process_all_nets(&mut self, circuit: &Circuit) -> Result<Vec<ProcessedNet>> {
        // First pass: determine net ownership and types
        self.analyze_net_hierarchy(circuit, "/")?;

        // Second pass: collect and merge all net nodes
        let all_nets = self.collect_all_nets(circuit, "/")?;

        // Third pass: process nets in parallel for performance
        let processed_nets: Result<Vec<_>> = all_nets
            .par_iter()
            .map(|(net_name, nodes)| self.process_single_net(net_name, nodes))
            .collect();

        processed_nets
    }

    /// Analyze net hierarchy to determine ownership and types
    fn analyze_net_hierarchy(&mut self, circuit: &Circuit, path: &str) -> Result<()> {
        // Process nets at this level
        for (net_name, net) in &circuit.nets {
            // Determine net type and ownership
            if self.is_global_net(net_name) {
                self.global_nets.insert(net_name.clone());
            } else if net.is_hierarchical {
                self.hierarchical_nets.insert(net_name.clone());
            } else {
                self.local_nets.insert(net_name.clone());
            }

            // Record ownership (first circuit to define the net owns it)
            if !self.net_ownership.contains_key(net_name) {
                self.net_ownership
                    .insert(net_name.clone(), path.to_string());
            }
        }

        // Process subcircuits recursively
        for subcircuit in &circuit.subcircuits {
            let sub_path = if path == "/" {
                format!("/{}", subcircuit.name)
            } else {
                format!("{}/{}", path, subcircuit.name)
            };
            self.analyze_net_hierarchy(subcircuit, &sub_path)?;
        }

        Ok(())
    }

    /// Collect all net nodes from the circuit hierarchy
    fn collect_all_nets(
        &mut self,
        circuit: &Circuit,
        path: &str,
    ) -> Result<HashMap<String, Vec<NetNode>>> {
        let mut all_nets: HashMap<String, Vec<NetNode>> = HashMap::new();

        // Collect nets from this circuit
        for (net_name, net) in &circuit.nets {
            // Handle unnamed nets by generating unique names
            let final_net_name = if self.is_unnamed_net(net_name) {
                let generated_name = self.generate_unnamed_net_name();
                generated_name
            } else {
                self.resolve_net_name(net_name, path)
            };

            // Clone nodes and update their paths if needed
            let mut processed_nodes = Vec::new();
            for node in &net.nodes {
                let mut processed_node = node.clone();

                // Normalize component reference
                processed_node.component =
                    self.normalize_component_reference(&node.component, path);

                // Handle unconnected pins
                if node.pin.is_unconnected() {
                    let unconnected_name = format!(
                        "unconnected-{}-{}",
                        processed_node.normalized_component_ref(),
                        node.pin.number
                    );
                    self.unconnected_pins.insert(unconnected_name.clone());

                    // Create separate net for unconnected pin
                    all_nets
                        .entry(unconnected_name)
                        .or_insert_with(Vec::new)
                        .push(processed_node);
                    continue;
                }

                processed_nodes.push(processed_node);
            }

            // Add processed nodes to the final net
            if !processed_nodes.is_empty() {
                all_nets
                    .entry(final_net_name)
                    .or_insert_with(Vec::new)
                    .extend(processed_nodes);
            }
        }

        // Process subcircuits recursively
        for subcircuit in &circuit.subcircuits {
            let sub_path = if path == "/" {
                format!("/{}", subcircuit.name)
            } else {
                format!("{}/{}", path, subcircuit.name)
            };

            let sub_nets = self.collect_all_nets(subcircuit, &sub_path)?;

            // Merge subcircuit nets
            for (net_name, nodes) in sub_nets {
                all_nets
                    .entry(net_name)
                    .or_insert_with(Vec::new)
                    .extend(nodes);
            }
        }

        Ok(all_nets)
    }

    /// Process a single net into the final format
    fn process_single_net(&self, net_name: &str, nodes: &[NetNode]) -> Result<ProcessedNet> {
        // Skip empty nets
        if nodes.is_empty() {
            return Err(NetlistError::net_processing_error(format!(
                "Net '{}' has no connections",
                net_name
            )));
        }

        // Deduplicate nodes (same component + pin)
        let mut unique_nodes = HashMap::new();
        for node in nodes {
            let key = format!("{}:{}", node.component, node.pin.number);
            unique_nodes.insert(key, node.clone());
        }

        let final_nodes: Vec<NetNode> = unique_nodes.into_values().collect();

        Ok(ProcessedNet {
            name: net_name.to_string(),
            nodes: final_nodes,
            is_hierarchical: self.hierarchical_nets.contains(net_name),
            is_global: self.global_nets.contains(net_name),
            is_unconnected: net_name.starts_with("unconnected-"),
        })
    }

    /// Resolve the final net name based on hierarchy
    fn resolve_net_name(&self, net_name: &str, current_path: &str) -> String {
        // Unnamed nets should not reach this method (handled in collect_all_nets)
        if self.is_unnamed_net(net_name) {
            return net_name.to_string();
        }

        // Global nets keep their original names
        if self.is_global_net(net_name) {
            return net_name.to_string();
        }

        // Unconnected nets keep their generated names
        if net_name.starts_with("unconnected-") {
            return net_name.to_string();
        }

        // Hierarchical nets get path prefixes
        if self.hierarchical_nets.contains(net_name) {
            // Check if net already has a hierarchical path
            if net_name.starts_with('/') {
                return net_name.to_string();
            }

            // Add hierarchical path
            if current_path == "/" {
                format!("/{}", net_name)
            } else {
                format!("{}/{}", current_path, net_name)
            }
        } else {
            // Local nets keep original names
            net_name.to_string()
        }
    }

    /// Check if a net is a global net (power, ground, etc.)
    fn is_global_net(&self, net_name: &str) -> bool {
        let upper_name = net_name.to_uppercase();
        matches!(
            upper_name.as_str(),
            "VCC"
                | "VDD"
                | "VSS"
                | "GND"
                | "GNDA"
                | "GNDD"
                | "+3V3"
                | "+5V"
                | "+12V"
                | "-12V"
                | "+15V"
                | "-15V"
        ) || net_name.starts_with('+')
            || net_name.starts_with('-')
    }

    /// Generate a unique name for an unnamed net
    fn generate_unnamed_net_name(&mut self) -> String {
        let name = format!("N${}", self.unnamed_net_counter);
        self.unnamed_net_counter += 1;
        name
    }

    /// Check if a net name indicates an unnamed net
    fn is_unnamed_net(&self, net_name: &str) -> bool {
        net_name == "__UNNAMED_NET__" || net_name.trim().is_empty()
    }

    /// Normalize component reference for hierarchical paths
    fn normalize_component_reference(&self, component_ref: &str, current_path: &str) -> String {
        // If component already has a path, use it as-is
        if component_ref.starts_with('/') {
            return component_ref.to_string();
        }

        // Add hierarchical path for components in subcircuits
        if current_path == "/" {
            component_ref.to_string()
        } else {
            format!("{}/{}", current_path, component_ref)
        }
    }

    /// Format the complete nets section
    fn format_nets_section(&self, processed_nets: &[ProcessedNet]) -> Result<String> {
        let mut section = String::with_capacity(processed_nets.len() * 512);

        // Sort nets for deterministic output
        let mut sorted_nets = processed_nets.to_vec();
        sorted_nets.sort_by(|a, b| a.name.cmp(&b.name));

        let mut net_code = 1u32;

        for net in &sorted_nets {
            let net_entry = self.format_single_net(net, net_code)?;
            section.push_str(&net_entry);
            section.push('\n');
            net_code += 1;
        }

        Ok(section)
    }

    /// Format a single net entry
    fn format_single_net(&self, net: &ProcessedNet, net_code: u32) -> Result<String> {
        let mut entry = String::with_capacity(256 + net.nodes.len() * 128);

        // Net header
        entry.push_str(&format!(
            "    (net (code \"{}\") (name \"{}\")",
            net_code, net.name
        ));

        // Sort nodes for deterministic output
        let mut sorted_nodes = net.nodes.clone();
        sorted_nodes.sort_by(|a, b| {
            a.normalized_component_ref()
                .cmp(b.normalized_component_ref())
                .then_with(|| a.pin.number.cmp(&b.pin.number))
        });

        // Add nodes
        for node in &sorted_nodes {
            entry.push_str(&format!(
                "\n      (node (ref \"{}\") (pin \"{}\") (pintype \"{}\"){})",
                node.normalized_component_ref(),
                node.pin.number,
                node.pin.pin_type.to_kicad_str(),
                if !node.pin.name.is_empty() && node.pin.name != "~" {
                    format!(" (pinfunction \"{}\")", node.pin.name)
                } else {
                    String::new()
                }
            ));
        }

        entry.push_str("\n    )"); // Close net

        Ok(entry)
    }

    /// Update memory usage estimation
    fn update_memory_usage(&mut self) {
        self.estimated_memory_usage = self.net_ownership.capacity()
            * (std::mem::size_of::<String>() * 2)
            + self.hierarchical_nets.capacity() * std::mem::size_of::<String>()
            + self.global_nets.capacity() * std::mem::size_of::<String>()
            + self.local_nets.capacity() * std::mem::size_of::<String>()
            + self.unconnected_pins.capacity() * std::mem::size_of::<String>();
    }
}

impl Default for NetProcessor {
    fn default() -> Self {
        Self::new()
    }
}

/// Processed net ready for formatting
#[derive(Debug, Clone)]
struct ProcessedNet {
    name: String,
    nodes: Vec<NetNode>,
    is_hierarchical: bool,
    is_global: bool,
    is_unconnected: bool,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::data_transform::{PinInfo, PinType};

    #[test]
    fn test_net_processor_creation() {
        let processor = NetProcessor::new();
        assert!(processor.net_ownership.is_empty());
        assert!(processor.hierarchical_nets.is_empty());
    }

    #[test]
    fn test_global_net_detection() {
        let processor = NetProcessor::new();
        assert!(processor.is_global_net("VCC"));
        assert!(processor.is_global_net("GND"));
        assert!(processor.is_global_net("+3V3"));
        assert!(!processor.is_global_net("DATA"));
    }

    #[test]
    fn test_component_reference_normalization() {
        let processor = NetProcessor::new();

        // Root level component
        assert_eq!(processor.normalize_component_reference("R1", "/"), "R1");

        // Subcircuit component
        assert_eq!(
            processor.normalize_component_reference("U1", "/MCU"),
            "/MCU/U1"
        );

        // Already has path
        assert_eq!(
            processor.normalize_component_reference("/MCU/U1", "/Power"),
            "/MCU/U1"
        );
    }

    #[test]
    fn test_net_name_resolution() {
        let mut processor = NetProcessor::new();
        processor.hierarchical_nets.insert("DATA".to_string());

        // Global net
        assert_eq!(processor.resolve_net_name("VCC", "/MCU"), "VCC");

        // Hierarchical net
        assert_eq!(processor.resolve_net_name("DATA", "/MCU"), "/MCU/DATA");

        // Already hierarchical
        assert_eq!(
            processor.resolve_net_name("/MCU/DATA", "/Power"),
            "/MCU/DATA"
        );
    }

    #[test]
    fn test_memory_usage_tracking() {
        let mut processor = NetProcessor::new();
        processor
            .net_ownership
            .insert("test".to_string(), "/".to_string());
        processor.update_memory_usage();
        assert!(processor.memory_usage() > 0);
    }
}
