//! Python bindings for the Rust reference manager
//!
//! This module provides PyO3-based Python bindings that allow seamless
//! integration with the existing Python codebase while delivering
//! high-performance reference management capabilities.

use crate::errors::ReferenceError;
use crate::RustReferenceManager;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::HashMap;

/// Python wrapper for the Rust reference manager
#[pyclass(name = "RustReferenceManager")]
pub struct PyRustReferenceManager {
    manager: RustReferenceManager,
}

#[pymethods]
impl PyRustReferenceManager {
    /// Create a new reference manager
    #[new]
    fn new(initial_counters: Option<&PyDict>) -> PyResult<Self> {
        let manager = match initial_counters {
            Some(counters) => {
                let mut counter_map = HashMap::new();
                for (key, value) in counters.iter() {
                    let prefix: String = key.extract()?;
                    let count: u32 = value.extract()?;
                    counter_map.insert(prefix, count);
                }
                RustReferenceManager::with_initial_counters(counter_map)
            }
            None => RustReferenceManager::new(),
        };

        Ok(Self { manager })
    }

    /// Set the parent reference manager
    ///
    /// Args:
    ///     parent_id: Optional parent manager ID
    ///
    /// Returns:
    ///     None
    ///
    /// Raises:
    ///     RuntimeError: If setting parent fails
    fn set_parent(&mut self, parent_id: Option<u64>) -> PyResult<()> {
        self.manager.set_parent(parent_id).map_err(|e| {
            let (exc_type, message) = e.to_python_exception();
            match exc_type {
                "ValueError" => PyErr::new::<pyo3::exceptions::PyValueError, _>(message),
                _ => PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(message),
            }
        })?;
        Ok(())
    }

    /// Register a new reference
    ///
    /// Args:
    ///     reference: Reference string to register (e.g., "R1", "C23")
    ///
    /// Returns:
    ///     None
    ///
    /// Raises:
    ///     ValueError: If reference format is invalid
    ///     RuntimeError: If reference is already in use
    fn register_reference(&mut self, reference: &str) -> PyResult<()> {
        self.manager.register_reference(reference).map_err(|e| {
            let (exc_type, message) = e.to_python_exception();
            match exc_type {
                "ValueError" => PyErr::new::<pyo3::exceptions::PyValueError, _>(message),
                _ => PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(message),
            }
        })?;
        Ok(())
    }

    /// Validate if a reference is available
    ///
    /// Args:
    ///     reference: Reference string to validate
    ///
    /// Returns:
    ///     True if reference is available, False otherwise
    fn validate_reference(&self, reference: &str) -> bool {
        self.manager.validate_reference(reference)
    }

    /// Generate the next available reference for a prefix
    ///
    /// Args:
    ///     prefix: Prefix string (e.g., "R", "C", "U")
    ///
    /// Returns:
    ///     Next available reference string
    ///
    /// Raises:
    ///     ValueError: If prefix format is invalid
    ///     RuntimeError: If generation fails
    fn generate_next_reference(&mut self, prefix: &str) -> PyResult<String> {
        self.manager.generate_next_reference(prefix).map_err(|e| {
            let (exc_type, message) = e.to_python_exception();
            match exc_type {
                "ValueError" => PyErr::new::<pyo3::exceptions::PyValueError, _>(message),
                _ => PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(message),
            }
        })
    }

    /// Generate the next unnamed net name
    ///
    /// Returns:
    ///     Next unnamed net name (e.g., "N$1", "N$2")
    fn generate_next_unnamed_net_name(&mut self) -> String {
        self.manager.generate_next_unnamed_net_name()
    }

    /// Set initial counters for reference generation
    ///
    /// Args:
    ///     counters: Dictionary mapping prefix -> start_number
    ///
    /// Returns:
    ///     None
    fn set_initial_counters(&mut self, counters: &PyDict) -> PyResult<()> {
        let mut counter_map = HashMap::new();
        for (key, value) in counters.iter() {
            let prefix: String = key.extract()?;
            let count: u32 = value.extract()?;
            counter_map.insert(prefix, count);
        }
        self.manager.set_initial_counters(counter_map);
        Ok(())
    }

    /// Get all used references in the hierarchy
    ///
    /// Returns:
    ///     List of all used reference strings
    fn get_all_used_references(&self) -> Vec<String> {
        self.manager.get_all_used_references()
    }

    /// Clear all references and reset state
    ///
    /// Returns:
    ///     None
    fn clear(&mut self) {
        self.manager.clear();
    }

    /// Get performance statistics
    ///
    /// Returns:
    ///     Dictionary with performance statistics
    fn get_stats(&self) -> PyResult<PyObject> {
        let stats = self.manager.get_stats();

        Python::with_gil(|py| json_value_to_python(py, &stats))
    }

    /// Get the manager ID
    ///
    /// Returns:
    ///     Unique manager ID
    fn get_id(&self) -> u64 {
        self.manager.get_id()
    }

    /// Check if the manager is ready for use
    ///
    /// Returns:
    ///     True if manager is ready
    fn is_ready(&self) -> bool {
        true // Rust manager is always ready after creation
    }

    /// Get a string representation
    fn __repr__(&self) -> String {
        format!("RustReferenceManager(id={})", self.manager.get_id())
    }

    /// Get a string representation
    fn __str__(&self) -> String {
        "Rust-based high-performance reference manager".to_string()
    }
}

/// Convert serde_json::Value to Python object
fn json_value_to_python(py: Python, value: &serde_json::Value) -> PyResult<PyObject> {
    match value {
        serde_json::Value::Null => Ok(py.None()),
        serde_json::Value::Bool(b) => Ok(b.to_object(py)),
        serde_json::Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Ok(i.to_object(py))
            } else if let Some(u) = n.as_u64() {
                Ok(u.to_object(py))
            } else if let Some(f) = n.as_f64() {
                Ok(f.to_object(py))
            } else {
                Ok(py.None())
            }
        }
        serde_json::Value::String(s) => Ok(s.to_object(py)),
        serde_json::Value::Array(arr) => {
            let py_list = PyList::empty(py);
            for item in arr {
                let py_item = json_value_to_python(py, item)?;
                py_list.append(py_item)?;
            }
            Ok(py_list.to_object(py))
        }
        serde_json::Value::Object(obj) => {
            let py_dict = PyDict::new(py);
            for (key, val) in obj {
                let py_val = json_value_to_python(py, val)?;
                py_dict.set_item(key, py_val)?;
            }
            Ok(py_dict.to_object(py))
        }
    }
}

/// Benchmark function for performance testing
#[pyfunction]
pub fn benchmark_reference_generation(
    prefixes: &PyList,
    iterations: Option<usize>,
) -> PyResult<PyObject> {
    let iterations = iterations.unwrap_or(1000);

    // Convert prefixes
    let prefix_list: Result<Vec<String>, _> = prefixes.iter().map(|p| p.extract()).collect();
    let prefix_list = prefix_list?;

    if prefix_list.is_empty() {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "At least one prefix must be provided",
        ));
    }

    // Create manager and run benchmark
    let mut manager = RustReferenceManager::new();
    let build_start = std::time::Instant::now();

    // Pre-warm the manager
    for prefix in &prefix_list {
        let _ = manager.generate_next_reference(prefix);
    }
    manager.clear();

    let build_time = build_start.elapsed();

    // Run generation benchmark
    let generation_start = std::time::Instant::now();
    let mut total_generated = 0;

    for _ in 0..iterations {
        for prefix in &prefix_list {
            match manager.generate_next_reference(prefix) {
                Ok(_) => total_generated += 1,
                Err(_) => break, // Stop on error
            }
        }
    }

    let generation_time = generation_start.elapsed();

    Python::with_gil(|py| {
        let result_dict = PyDict::new(py);
        result_dict.set_item("setup_time_ms", build_time.as_millis())?;
        result_dict.set_item("total_generation_time_ms", generation_time.as_millis())?;
        result_dict.set_item(
            "avg_generation_time_ns",
            generation_time.as_nanos() as f64 / total_generated as f64,
        )?;
        result_dict.set_item("total_generated", total_generated)?;
        result_dict.set_item(
            "generations_per_second",
            total_generated as f64 / generation_time.as_secs_f64(),
        )?;
        result_dict.set_item("prefixes_tested", prefix_list.len())?;
        result_dict.set_item("iterations", iterations)?;

        Ok(result_dict.to_object(py))
    })
}

/// Compare Rust vs Python performance
#[pyfunction]
fn compare_performance(prefixes: &PyList, iterations: Option<usize>) -> PyResult<PyObject> {
    // This function would ideally compare against the Python implementation
    // For now, we'll just return Rust performance metrics
    benchmark_reference_generation(prefixes, iterations)
}

/// Validate multiple references at once
#[pyfunction]
fn batch_validate_references(
    manager: &PyRustReferenceManager,
    references: &PyList,
) -> PyResult<PyObject> {
    let reference_list: Result<Vec<String>, _> = references.iter().map(|r| r.extract()).collect();
    let reference_list = reference_list?;

    let mut results = Vec::new();
    let start_time = std::time::Instant::now();

    for reference in reference_list {
        let is_valid = manager.validate_reference(&reference);
        results.push((reference, is_valid));
    }

    let validation_time = start_time.elapsed();

    Python::with_gil(|py| {
        let result_dict = PyDict::new(py);

        // Convert results to Python format
        let py_results = PyList::empty(py);
        for (reference, is_valid) in results {
            let result_tuple = (reference, is_valid).to_object(py);
            py_results.append(result_tuple)?;
        }

        result_dict.set_item("results", py_results)?;
        result_dict.set_item("validation_time_ms", validation_time.as_millis())?;
        result_dict.set_item(
            "avg_validation_time_ns",
            validation_time.as_nanos() as f64 / py_results.len() as f64,
        )?;

        Ok(result_dict.to_object(py))
    })
}

/// Python module definition
#[pymodule]
fn _rust_reference_manager(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyRustReferenceManager>()?;
    m.add_function(wrap_pyfunction!(benchmark_reference_generation, m)?)?;
    m.add_function(wrap_pyfunction!(compare_performance, m)?)?;
    m.add_function(wrap_pyfunction!(batch_validate_references, m)?)?;

    // Add version info
    m.add("__version__", "0.1.0")?;
    m.add("__author__", "Circuit Synth Team")?;
    m.add(
        "__description__",
        "High-performance Rust-based reference manager",
    )?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::types::IntoPyDict;

    #[test]
    fn test_python_bindings() {
        Python::with_gil(|py| {
            let mut manager = PyRustReferenceManager::new(None).unwrap();

            // Test reference generation
            let ref1 = manager.generate_next_reference("R").unwrap();
            assert_eq!(ref1, "R1");

            let ref2 = manager.generate_next_reference("R").unwrap();
            assert_eq!(ref2, "R2");

            // Test validation
            assert!(!manager.validate_reference("R1")); // Should be in use
            assert!(manager.validate_reference("R99")); // Should be available

            // Test registration
            assert!(manager.register_reference("C1").is_ok());
            assert!(manager.register_reference("C1").is_err()); // Duplicate

            // Test stats
            let stats = manager.get_stats().unwrap();
            assert!(!stats.is_none(py));
        });
    }

    #[test]
    fn test_initial_counters() {
        Python::with_gil(|py| {
            let counters = [("R", 10u32), ("C", 5u32)].into_py_dict(py);

            let mut manager = PyRustReferenceManager::new(Some(counters)).unwrap();

            let ref1 = manager.generate_next_reference("R").unwrap();
            assert_eq!(ref1, "R10");

            let ref2 = manager.generate_next_reference("C").unwrap();
            assert_eq!(ref2, "C5");
        });
    }

    #[test]
    fn test_unnamed_net_generation() {
        Python::with_gil(|py| {
            let mut manager = PyRustReferenceManager::new(None).unwrap();

            let net1 = manager.generate_next_unnamed_net_name();
            assert_eq!(net1, "N$1");

            let net2 = manager.generate_next_unnamed_net_name();
            assert_eq!(net2, "N$2");
        });
    }

    #[test]
    fn test_benchmark_function() {
        Python::with_gil(|py| {
            let prefixes = PyList::new(py, &["R", "C", "L"]);

            let result = benchmark_reference_generation(prefixes, Some(10)).unwrap();
            assert!(!result.is_none(py));

            // Extract and verify results
            let result_dict = result.downcast::<PyDict>(py).unwrap();
            let total_generated = result_dict
                .get_item("total_generated")
                .unwrap()
                .extract::<usize>()
                .unwrap();
            assert!(total_generated > 0);
        });
    }

    #[test]
    fn test_batch_validation() {
        Python::with_gil(|py| {
            let mut manager = PyRustReferenceManager::new(None).unwrap();

            // Register some references
            manager.register_reference("R1").unwrap();
            manager.register_reference("C1").unwrap();

            let references = PyList::new(py, &["R1", "R2", "C1", "C2"]);
            let result = batch_validate_references(&manager, references).unwrap();

            let result_dict = result.downcast::<PyDict>(py).unwrap();
            let results = result_dict
                .get_item("results")
                .unwrap()
                .downcast::<PyList>()
                .unwrap();

            assert_eq!(results.len(), 4);
        });
    }

    #[test]
    fn test_error_handling() {
        Python::with_gil(|py| {
            let mut manager = PyRustReferenceManager::new(None).unwrap();

            // Test invalid prefix
            let result = manager.generate_next_reference("123");
            assert!(result.is_err());

            // Test invalid reference
            let result = manager.register_reference("");
            assert!(result.is_err());
        });
    }
}
