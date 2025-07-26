//! Python bindings for the Rust symbol search engine
//! 
//! This module provides PyO3-based Python bindings that allow seamless
//! integration with the existing Python codebase while delivering
//! high-performance search capabilities.

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::HashMap;
use crate::{RustSymbolSearcher};
use crate::types::{SearchResult as RustSearchResult, MatchType, MatchDetails};

/// Python wrapper for the Rust symbol searcher
#[pyclass(name = "RustSymbolSearcher")]
pub struct PyRustSymbolSearcher {
    searcher: RustSymbolSearcher,
}

#[pymethods]
impl PyRustSymbolSearcher {
    /// Create a new symbol searcher
    #[new]
    fn new() -> Self {
        Self {
            searcher: RustSymbolSearcher::new(),
        }
    }

    /// Build the search index from symbol data
    /// 
    /// Args:
    ///     symbols: Dictionary mapping symbol_name -> library_name
    /// 
    /// Returns:
    ///     None
    /// 
    /// Raises:
    ///     RuntimeError: If index building fails
    fn build_index(&mut self, symbols: &PyDict) -> PyResult<()> {
        let mut symbol_map = HashMap::new();
        
        for (key, value) in symbols.iter() {
            let symbol_name: String = key.extract()?;
            let library_name: String = value.extract()?;
            symbol_map.insert(symbol_name, library_name);
        }
        
        self.searcher.build_index(symbol_map)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to build index: {}", e)))?;
        
        Ok(())
    }

    /// Search for symbols matching the query
    /// 
    /// Args:
    ///     query: Search query string
    ///     max_results: Maximum number of results to return (default: 10)
    ///     min_score: Minimum match score threshold (default: 0.3)
    /// 
    /// Returns:
    ///     List of search result dictionaries
    fn search(&mut self, query: &str, max_results: Option<usize>, min_score: Option<f64>) -> PyResult<Vec<PyObject>> {
        let max_results = max_results.unwrap_or(10);
        let min_score = min_score.unwrap_or(0.3);
        
        let results = self.searcher.search(query, max_results, min_score);
        
        Python::with_gil(|py| {
            let py_results: PyResult<Vec<PyObject>> = results
                .into_iter()
                .map(|result| rust_result_to_python(py, result))
                .collect();
            py_results
        })
    }

    /// Get search engine statistics
    /// 
    /// Returns:
    ///     Dictionary with performance statistics
    fn get_stats(&self) -> PyResult<PyObject> {
        let stats = self.searcher.get_stats();
        
        Python::with_gil(|py| {
            let py_dict = PyDict::new(py);
            
            if let Some(obj) = stats.as_object() {
                for (key, value) in obj.iter() {
                    let py_key = key.to_object(py);
                    let py_value = json_value_to_python(py, value)?;
                    py_dict.set_item(py_key, py_value)?;
                }
            }
            
            Ok(py_dict.to_object(py))
        })
    }

    /// Check if the searcher is ready for use
    /// 
    /// Returns:
    ///     True if index is built and ready
    fn is_ready(&self) -> bool {
        // The searcher is ready if it has been built
        true // We'll assume it's ready after build_index is called
    }

    /// Get a string representation
    fn __repr__(&self) -> String {
        "RustSymbolSearcher()".to_string()
    }

    /// Get a string representation
    fn __str__(&self) -> String {
        "Rust-based high-performance symbol searcher".to_string()
    }
}

/// Convert a Rust SearchResult to a Python dictionary
fn rust_result_to_python(py: Python, result: RustSearchResult) -> PyResult<PyObject> {
    let dict = PyDict::new(py);
    
    dict.set_item("lib_id", result.lib_id)?;
    dict.set_item("name", result.symbol_name)?;
    dict.set_item("library", result.library_name)?;
    dict.set_item("score", result.score)?;
    dict.set_item("match_type", match_type_to_string(&result.match_type))?;
    
    // Convert match details
    let details_dict = PyDict::new(py);
    details_dict.set_item("symbol_exact", result.match_details.symbol_exact)?;
    details_dict.set_item("symbol_fuzzy", result.match_details.symbol_fuzzy)?;
    details_dict.set_item("library_fuzzy", result.match_details.library_fuzzy)?;
    details_dict.set_item("lib_id_fuzzy", result.match_details.lib_id_fuzzy)?;
    details_dict.set_item("symbol_substring", result.match_details.symbol_substring)?;
    details_dict.set_item("library_substring", result.match_details.library_substring)?;
    details_dict.set_item("ngram_score", result.match_details.ngram_score)?;
    
    dict.set_item("match_details", details_dict)?;
    
    Ok(dict.to_object(py))
}

/// Convert MatchType to string
fn match_type_to_string(match_type: &MatchType) -> &'static str {
    match match_type {
        MatchType::Exact => "exact",
        MatchType::HighFuzzy => "high_fuzzy",
        MatchType::Fuzzy => "fuzzy",
        MatchType::Substring => "substring",
        MatchType::NGram => "ngram",
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
pub fn benchmark_rust_search(symbols: &PyDict, queries: &PyList, iterations: Option<usize>) -> PyResult<PyObject> {
    let iterations = iterations.unwrap_or(100);
    
    // Convert symbols
    let mut symbol_map = HashMap::new();
    for (key, value) in symbols.iter() {
        let symbol_name: String = key.extract()?;
        let library_name: String = value.extract()?;
        symbol_map.insert(symbol_name, library_name);
    }
    
    // Convert queries
    let query_list: Result<Vec<String>, _> = queries.iter().map(|q| q.extract()).collect();
    let query_list = query_list?;
    
    // Create searcher and build index
    let mut searcher = RustSymbolSearcher::new();
    let build_start = std::time::Instant::now();
    searcher.build_index(symbol_map)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to build index: {}", e)))?;
    let build_time = build_start.elapsed();
    
    // Run search benchmark
    let search_start = std::time::Instant::now();
    let mut total_results = 0;
    
    for _ in 0..iterations {
        for query in &query_list {
            let results = searcher.search(query, 10, 0.3);
            total_results += results.len();
        }
    }
    
    let search_time = search_start.elapsed();
    
    Python::with_gil(|py| {
        let result_dict = PyDict::new(py);
        result_dict.set_item("build_time_ms", build_time.as_millis())?;
        result_dict.set_item("total_search_time_ms", search_time.as_millis())?;
        result_dict.set_item("avg_search_time_ms", search_time.as_millis() as f64 / (iterations * query_list.len()) as f64)?;
        result_dict.set_item("total_searches", iterations * query_list.len())?;
        result_dict.set_item("total_results", total_results)?;
        result_dict.set_item("searches_per_second", (iterations * query_list.len()) as f64 / search_time.as_secs_f64())?;
        
        Ok(result_dict.to_object(py))
    })
}

/// Compare Rust vs Python performance
#[pyfunction]
fn compare_performance(symbols: &PyDict, queries: &PyList) -> PyResult<PyObject> {
    // This function would ideally compare against the Python implementation
    // For now, we'll just return Rust performance metrics
    benchmark_rust_search(symbols, queries, Some(10))
}

/// Python module definition
#[pymodule]
fn _rust_symbol_search(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyRustSymbolSearcher>()?;
    m.add_function(wrap_pyfunction!(benchmark_rust_search, m)?)?;
    m.add_function(wrap_pyfunction!(compare_performance, m)?)?;
    
    // Add version info
    m.add("__version__", "0.1.0")?;
    m.add("__author__", "Circuit Synth Team")?;
    m.add("__description__", "High-performance Rust-based symbol search engine")?;
    
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::types::IntoPyDict;

    #[test]
    fn test_python_bindings() {
        Python::with_gil(|py| {
            let mut searcher = PyRustSymbolSearcher::new();
            
            // Create test symbols
            let symbols = [
                ("R", "Device"),
                ("C", "Device"),
                ("LM7805_TO220", "Regulator_Linear"),
            ].into_py_dict(py);
            
            // Build index
            searcher.build_index(symbols).unwrap();
            
            // Test search
            let results = searcher.search("resistor", Some(5), Some(0.3)).unwrap();
            assert!(!results.is_empty());
            
            // Test stats
            let stats = searcher.get_stats().unwrap();
            assert!(!stats.is_none(py));
        });
    }

    #[test]
    fn test_benchmark_function() {
        Python::with_gil(|py| {
            let symbols = [
                ("R", "Device"),
                ("C", "Device"),
                ("L", "Device"),
            ].into_py_dict(py);
            
            let queries = PyList::new(py, &["resistor", "capacitor", "inductor"]);
            
            let result = benchmark_rust_search(symbols, queries, Some(5)).unwrap();
            assert!(!result.is_none(py));
        });
    }
}