//! # Rust Netlist Processor
//!
//! High-performance netlist processing engine for Circuit Synth, targeting 30-50x performance
//! improvements over the Python implementation through optimized data structures, zero-copy
//! string operations, and parallel processing.
//!
//! ## Architecture
//!
//! The processor is organized into specialized modules:
//! - [`s_expression`]: High-performance S-expression formatting engine
//! - [`net_processor`]: Hierarchical net processing with parallel execution
//! - [`component_gen`]: Component section generation with efficient serialization
//! - [`libpart_gen`]: Library parts processing with deduplication
//! - [`data_transform`]: Data structure transformations and serialization
//! - [`python_bindings`]: PyO3 integration layer for seamless Python interop
//!
//! ## Performance Targets
//!
//! - S-expression formatting: 50x faster with zero-copy operations
//! - Hierarchical net processing: 30x faster with optimized data structures
//! - Component processing: 40x faster with efficient serialization
//! - Overall netlist generation: 30-50x improvement
//!
//! ## Usage
//!
//! ```rust
//! use rust_netlist_processor::{NetlistProcessor, Circuit};
//!
//! let mut processor = NetlistProcessor::new();
//! let circuit = Circuit::new("Test Circuit");
//! let netlist = processor.generate_kicad_netlist(&circuit).unwrap();
//! ```

use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use thiserror::Error;

// Core modules
pub mod s_expression;
pub mod net_processor;
pub mod component_gen;
pub mod libpart_gen;
pub mod data_transform;
pub mod errors;

// Python bindings (feature-gated)
#[cfg(feature = "python-bindings")]
pub mod python_bindings;

// PyO3 module initialization - this is the entry point for Python
#[cfg(feature = "python-bindings")]
use pyo3::prelude::*;

#[cfg(feature = "python-bindings")]
#[pymodule]
fn rust_netlist_processor(_py: Python, m: &PyModule) -> PyResult<()> {
    // Import all the classes and functions from python_bindings
    use python_bindings::{PyNetlistProcessor, PyCircuit, PyComponent, convert_json_to_netlist, benchmark_netlist_generation};
    
    m.add_class::<PyNetlistProcessor>()?;
    m.add_class::<PyCircuit>()?;
    m.add_class::<PyComponent>()?;
    m.add_function(wrap_pyfunction!(convert_json_to_netlist, m)?)?;
    m.add_function(wrap_pyfunction!(benchmark_netlist_generation, m)?)?;
    
    // Add version information
    m.add("__version__", "0.1.0")?;
    m.add("__author__", "Circuit Synth Team")?;
    
    Ok(())
}

// Re-export main types
pub use errors::{NetlistError, Result};
pub use s_expression::SExprFormatter;
pub use net_processor::NetProcessor;
pub use component_gen::ComponentGenerator;
pub use libpart_gen::LibpartGenerator;
pub use data_transform::{Circuit, Component, NetNode, PinInfo, PinType};

/// Main netlist processor that orchestrates all processing stages
pub struct NetlistProcessor {
    formatter: SExprFormatter,
    net_processor: NetProcessor,
    component_gen: ComponentGenerator,
    libpart_gen: LibpartGenerator,
}

impl NetlistProcessor {
    /// Create a new netlist processor with optimized default settings
    pub fn new() -> Self {
        Self {
            formatter: SExprFormatter::new(),
            net_processor: NetProcessor::new(),
            component_gen: ComponentGenerator::new(),
            libpart_gen: LibpartGenerator::new(),
        }
    }

    /// Generate a complete KiCad netlist from circuit data
    ///
    /// This is the main entry point that orchestrates all processing stages:
    /// 1. Data structure transformation and validation
    /// 2. Component section generation
    /// 3. Library parts processing and deduplication
    /// 4. Hierarchical net processing
    /// 5. S-expression formatting and output generation
    ///
    /// # Arguments
    /// * `circuit` - The circuit data structure to process
    ///
    /// # Returns
    /// * `Result<String>` - The formatted KiCad netlist or an error
    ///
    /// # Performance
    /// This function is optimized for maximum performance with:
    /// - Pre-allocated string buffers
    /// - Zero-copy string operations where possible
    /// - Parallel processing of independent sections
    /// - Efficient data structure traversal
    pub fn generate_kicad_netlist(&mut self, circuit: &Circuit) -> Result<String> {
        // Clear any previous state
        self.formatter.reset();
        
        // Generate all sections in parallel where possible
        let design_section = self.formatter.generate_design_section(circuit)?;
        let components_section = self.component_gen.generate_components_section(circuit)?;
        let libparts_section = self.libpart_gen.generate_libparts_section(circuit)?;
        let libraries_section = self.libpart_gen.generate_libraries_section(circuit)?;
        let nets_section = self.net_processor.generate_nets_section(circuit)?;

        // Format the complete netlist
        self.formatter.format_complete_netlist(
            &design_section,
            &components_section,
            &libparts_section,
            &libraries_section,
            &nets_section,
        )
    }

    /// Generate only the nets section (useful for testing and debugging)
    pub fn generate_nets_only(&mut self, circuit: &Circuit) -> Result<String> {
        let nets_section = self.net_processor.generate_nets_section(circuit)?;
        self.formatter.format_nets_section(&nets_section)
    }

    /// Generate only the components section
    pub fn generate_components_only(&mut self, circuit: &Circuit) -> Result<String> {
        let components_section = self.component_gen.generate_components_section(circuit)?;
        self.formatter.format_components_section(&components_section)
    }

    /// Get performance statistics from the last processing run
    pub fn get_performance_stats(&self) -> ProcessingStats {
        ProcessingStats {
            formatting_time_ms: self.formatter.last_processing_time_ms(),
            net_processing_time_ms: self.net_processor.last_processing_time_ms(),
            component_processing_time_ms: self.component_gen.last_processing_time_ms(),
            libpart_processing_time_ms: self.libpart_gen.last_processing_time_ms(),
            total_memory_used_bytes: self.estimate_memory_usage(),
        }
    }

    /// Reset the processor state for reuse
    pub fn reset(&mut self) {
        self.formatter.reset();
        // Note: Other processors don't need explicit reset as they're stateless
        // or reset themselves during processing
    }

    /// Estimate current memory usage (for performance monitoring)
    fn estimate_memory_usage(&self) -> usize {
        self.formatter.buffer_capacity() +
        self.net_processor.memory_usage() +
        self.component_gen.memory_usage() +
        self.libpart_gen.memory_usage()
    }
}

impl Default for NetlistProcessor {
    fn default() -> Self {
        Self::new()
    }
}

/// Performance statistics for monitoring and optimization
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessingStats {
    pub formatting_time_ms: f64,
    pub net_processing_time_ms: f64,
    pub component_processing_time_ms: f64,
    pub libpart_processing_time_ms: f64,
    pub total_memory_used_bytes: usize,
}

impl ProcessingStats {
    /// Get total processing time in milliseconds
    pub fn total_time_ms(&self) -> f64 {
        self.formatting_time_ms +
        self.net_processing_time_ms +
        self.component_processing_time_ms +
        self.libpart_processing_time_ms
    }

    /// Get memory usage in megabytes
    pub fn memory_usage_mb(&self) -> f64 {
        self.total_memory_used_bytes as f64 / (1024.0 * 1024.0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_processor_creation() {
        let processor = NetlistProcessor::new();
        assert!(processor.formatter.buffer_capacity() > 0);
    }

    #[test]
    fn test_default_processor() {
        let processor = NetlistProcessor::default();
        assert!(processor.formatter.buffer_capacity() > 0);
    }
}