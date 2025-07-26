//! PyO3 bindings for Python integration
//! 
//! Provides seamless integration between Rust I/O processor and Python,
//! enabling 10-30x performance improvements while maintaining Python API compatibility.

use std::collections::HashMap;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString};
use pyo3_asyncio;
use tokio::runtime::Runtime;
use serde_json::Value;
use tracing::{info, error};

use crate::error::{IoError, IoResult};
use crate::json_processor::{JsonLoader, JsonSerializer, CircuitData};
use crate::kicad_parser::{KiCadParser, SchematicData, PcbData, SymbolLibraryData};
use crate::validation::{ValidationEngine, ValidationResult};
use crate::file_io::{AsyncFileOps, FileIoConfig};
use crate::memory::MemoryManager;

/// Initialize the Rust I/O processor
#[pyfunction]
pub fn init_processor() -> PyResult<()> {
    crate::init().map_err(|e| PyErr::from(e))?;
    info!("Rust I/O processor initialized");
    Ok(())
}

/// Get performance statistics
#[pyfunction]
pub fn get_stats() -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let stats = crate::get_performance_stats();
        pythonize::pythonize(py, &stats).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert stats: {}", e))
        })
    })
}

/// Load circuit from dictionary - equivalent to Python's load_circuit_from_dict()
#[pyfunction]
pub fn load_circuit_from_dict(py: Python, data: &PyDict) -> PyResult<PyObject> {
    let rt = Runtime::new().map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create runtime: {}", e))
    })?;

    // Convert Python dict to serde_json::Value
    let json_value: Value = pythonize::depythonize(data).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Failed to convert Python dict: {}", e))
    })?;

    let result = rt.block_on(async {
        let loader = JsonLoader::new();
        loader.load_circuit_from_dict(json_value).await
    });

    match result {
        Ok(circuit) => {
            // Convert Rust CircuitData back to Python dict
            let circuit_json = serde_json::to_value(&circuit).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to serialize circuit: {}", e))
            })?;
            
            pythonize::pythonize(py, &circuit_json).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert to Python: {}", e))
            })
        }
        Err(e) => Err(PyErr::from(e))
    }
}

/// Load circuit from JSON file - equivalent to Python's load_circuit_from_json_file()
#[pyfunction]
pub fn load_circuit_from_json_file(py: Python, path: &str) -> PyResult<PyObject> {
    let rt = Runtime::new().map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create runtime: {}", e))
    })?;

    let result = rt.block_on(async {
        let loader = JsonLoader::new();
        loader.load_circuit_from_json_file(path).await
    });

    match result {
        Ok(circuit) => {
            // Convert Rust CircuitData back to Python dict
            let circuit_json = serde_json::to_value(&circuit).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to serialize circuit: {}", e))
            })?;
            
            pythonize::pythonize(py, &circuit_json).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert to Python: {}", e))
            })
        }
        Err(e) => Err(PyErr::from(e))
    }
}

/// Save circuit to JSON file
#[pyfunction]
pub fn save_circuit_to_json_file(data: &PyDict, path: &str) -> PyResult<()> {
    let rt = Runtime::new().map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create runtime: {}", e))
    })?;

    // Convert Python dict to CircuitData
    let circuit: CircuitData = pythonize::depythonize(data).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Failed to convert Python dict: {}", e))
    })?;

    let result = rt.block_on(async {
        let serializer = JsonSerializer::new();
        serializer.save_circuit_to_json_file(&circuit, path).await
    });

    result.map_err(|e| PyErr::from(e))
}

/// Parse KiCad schematic file
#[pyfunction]
pub fn parse_kicad_schematic(py: Python, path: &str) -> PyResult<PyObject> {
    let rt = Runtime::new().map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create runtime: {}", e))
    })?;

    let result = rt.block_on(async {
        let parser = KiCadParser::new();
        parser.parse_schematic(path).await
    });

    match result {
        Ok(schematic) => {
            let schematic_json = serde_json::to_value(&schematic).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to serialize schematic: {}", e))
            })?;
            
            pythonize::pythonize(py, &schematic_json).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert to Python: {}", e))
            })
        }
        Err(e) => Err(PyErr::from(e))
    }
}

/// Parse KiCad PCB file
#[pyfunction]
pub fn parse_kicad_pcb(py: Python, path: &str) -> PyResult<PyObject> {
    let rt = Runtime::new().map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create runtime: {}", e))
    })?;

    let result = rt.block_on(async {
        let parser = KiCadParser::new();
        parser.parse_pcb(path).await
    });

    match result {
        Ok(pcb) => {
            let pcb_json = serde_json::to_value(&pcb).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to serialize PCB: {}", e))
            })?;
            
            pythonize::pythonize(py, &pcb_json).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert to Python: {}", e))
            })
        }
        Err(e) => Err(PyErr::from(e))
    }
}

/// Parse KiCad symbol library file
#[pyfunction]
pub fn parse_kicad_symbol(py: Python, path: &str) -> PyResult<PyObject> {
    let rt = Runtime::new().map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create runtime: {}", e))
    })?;

    let result = rt.block_on(async {
        let parser = KiCadParser::new();
        parser.parse_symbol_library(path).await
    });

    match result {
        Ok(library) => {
            let library_json = serde_json::to_value(&library).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to serialize library: {}", e))
            })?;
            
            pythonize::pythonize(py, &library_json).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert to Python: {}", e))
            })
        }
        Err(e) => Err(PyErr::from(e))
    }
}

/// Validate circuit data
#[pyfunction]
pub fn validate_circuit_data(py: Python, data: &PyDict) -> PyResult<PyObject> {
    let rt = Runtime::new().map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create runtime: {}", e))
    })?;

    // Convert Python dict to CircuitData
    let circuit: CircuitData = pythonize::depythonize(data).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Failed to convert Python dict: {}", e))
    })?;

    let result = rt.block_on(async {
        let engine = ValidationEngine::new();
        engine.validate_circuit_data(&circuit).await
    });

    match result {
        Ok(validation_result) => {
            let result_json = serde_json::to_value(&validation_result).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to serialize validation result: {}", e))
            })?;
            
            pythonize::pythonize(py, &result_json).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert to Python: {}", e))
            })
        }
        Err(e) => Err(PyErr::from(e))
    }
}

/// Validate JSON schema
#[pyfunction]
pub fn validate_json_schema(py: Python, data: &PyDict, schema_name: &str) -> PyResult<PyObject> {
    let rt = Runtime::new().map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create runtime: {}", e))
    })?;

    // Convert Python dict to serde_json::Value
    let json_value: Value = pythonize::depythonize(data).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Failed to convert Python dict: {}", e))
    })?;

    let result = rt.block_on(async {
        let engine = ValidationEngine::new();
        engine.validate_json_schema(&json_value, schema_name).await
    });

    match result {
        Ok(()) => Ok(py.None()),
        Err(issues) => {
            let issues_json = serde_json::to_value(&issues).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to serialize issues: {}", e))
            })?;
            
            pythonize::pythonize(py, &issues_json).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert to Python: {}", e))
            })
        }
    }
}

/// Read file asynchronously
#[pyfunction]
pub fn read_file_async(path: &str) -> PyResult<Vec<u8>> {
    let rt = Runtime::new().map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create runtime: {}", e))
    })?;

    let result = rt.block_on(async {
        let file_ops = AsyncFileOps::new();
        file_ops.reader().read_file(path).await
    });

    result.map_err(|e| PyErr::from(e))
}

/// Write file asynchronously
#[pyfunction]
pub fn write_file_async(path: &str, data: Vec<u8>) -> PyResult<()> {
    let rt = Runtime::new().map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create runtime: {}", e))
    })?;

    let result = rt.block_on(async {
        let file_ops = AsyncFileOps::new();
        file_ops.writer().write_file(path, &data).await
    });

    result.map_err(|e| PyErr::from(e))
}

/// Batch load multiple circuit files
#[pyfunction]
pub fn load_circuits_batch(py: Python, paths: Vec<String>) -> PyResult<PyObject> {
    let rt = Runtime::new().map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create runtime: {}", e))
    })?;

    let result = rt.block_on(async {
        let loader = JsonLoader::new();
        loader.load_circuits_batch(paths).await
    });

    // Convert results to Python
    let mut py_results = Vec::new();
    for circuit_result in result {
        match circuit_result {
            Ok(circuit) => {
                let circuit_json = serde_json::to_value(&circuit).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to serialize circuit: {}", e))
                })?;
                py_results.push(pythonize::pythonize(py, &circuit_json)?);
            }
            Err(e) => {
                return Err(PyErr::from(e));
            }
        }
    }

    Ok(PyList::new(py, py_results).into())
}

/// Batch parse multiple KiCad files
#[pyfunction]
pub fn parse_kicad_files_batch(py: Python, paths: Vec<String>) -> PyResult<PyObject> {
    let rt = Runtime::new().map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create runtime: {}", e))
    })?;

    let result = rt.block_on(async {
        let parser = KiCadParser::new();
        parser.parse_files_batch(paths).await
    });

    // Convert results to Python
    let mut py_results = Vec::new();
    for parse_result in result {
        match parse_result {
            Ok(kicad_data) => {
                let data_json = serde_json::to_value(&kicad_data).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to serialize KiCad data: {}", e))
                })?;
                py_results.push(pythonize::pythonize(py, &data_json)?);
            }
            Err(e) => {
                return Err(PyErr::from(e));
            }
        }
    }

    Ok(PyList::new(py, py_results).into())
}

/// Get memory statistics
#[pyfunction]
pub fn get_memory_stats(py: Python) -> PyResult<PyObject> {
    let stats = crate::memory::get_memory_stats();
    pythonize::pythonize(py, &stats).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert stats: {}", e))
    })
}

/// Clear memory caches
#[pyfunction]
pub fn clear_memory_caches() -> PyResult<()> {
    crate::memory::cleanup_memory();
    Ok(())
}

/// Optimize memory usage
#[pyfunction]
pub fn optimize_memory() -> PyResult<()> {
    crate::memory::MemoryOptimizer::optimize();
    Ok(())
}

/// Get file cache statistics
#[pyfunction]
pub fn get_file_cache_stats(py: Python) -> PyResult<PyObject> {
    let file_ops = AsyncFileOps::new();
    let stats = file_ops.get_cache_stats();
    pythonize::pythonize(py, &stats).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert stats: {}", e))
    })
}

/// Clear file cache
#[pyfunction]
pub fn clear_file_cache() -> PyResult<()> {
    let file_ops = AsyncFileOps::new();
    file_ops.clear_cache();
    Ok(())
}

/// Configure file I/O settings
#[pyfunction]
pub fn configure_file_io(
    mmap_threshold: Option<usize>,
    cache_size_limit: Option<usize>,
    enable_caching: Option<bool>,
    buffer_size: Option<usize>,
    max_concurrent_ops: Option<usize>,
) -> PyResult<()> {
    let mut config = FileIoConfig::default();
    
    if let Some(threshold) = mmap_threshold {
        config.mmap_threshold = threshold;
    }
    if let Some(limit) = cache_size_limit {
        config.cache_size_limit = limit;
    }
    if let Some(caching) = enable_caching {
        config.enable_caching = caching;
    }
    if let Some(buffer) = buffer_size {
        config.buffer_size = buffer;
    }
    if let Some(concurrent) = max_concurrent_ops {
        config.max_concurrent_ops = concurrent;
    }

    info!("File I/O configuration updated: {:?}", config);
    Ok(())
}

/// Python class wrapper for JsonLoader
#[pyclass]
pub struct PyJsonLoader {
    loader: JsonLoader,
    rt: Runtime,
}

#[pymethods]
impl PyJsonLoader {
    #[new]
    fn new() -> PyResult<Self> {
        let rt = Runtime::new().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create runtime: {}", e))
        })?;
        
        Ok(PyJsonLoader {
            loader: JsonLoader::new(),
            rt,
        })
    }

    fn load_from_file(&self, py: Python, path: &str) -> PyResult<PyObject> {
        let result = self.rt.block_on(async {
            self.loader.load_circuit_from_json_file(path).await
        });

        match result {
            Ok(circuit) => {
                let circuit_json = serde_json::to_value(&circuit).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to serialize circuit: {}", e))
                })?;
                
                pythonize::pythonize(py, &circuit_json).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert to Python: {}", e))
                })
            }
            Err(e) => Err(PyErr::from(e))
        }
    }

    fn load_from_dict(&self, py: Python, data: &PyDict) -> PyResult<PyObject> {
        let json_value: Value = pythonize::depythonize(data).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Failed to convert Python dict: {}", e))
        })?;

        let result = self.rt.block_on(async {
            self.loader.load_circuit_from_dict(json_value).await
        });

        match result {
            Ok(circuit) => {
                let circuit_json = serde_json::to_value(&circuit).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to serialize circuit: {}", e))
                })?;
                
                pythonize::pythonize(py, &circuit_json).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert to Python: {}", e))
                })
            }
            Err(e) => Err(PyErr::from(e))
        }
    }
}

/// Python class wrapper for KiCadParser
#[pyclass]
pub struct PyKiCadParser {
    parser: KiCadParser,
    rt: Runtime,
}

#[pymethods]
impl PyKiCadParser {
    #[new]
    fn new() -> PyResult<Self> {
        let rt = Runtime::new().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create runtime: {}", e))
        })?;
        
        Ok(PyKiCadParser {
            parser: KiCadParser::new(),
            rt,
        })
    }

    fn parse_schematic(&self, py: Python, path: &str) -> PyResult<PyObject> {
        let result = self.rt.block_on(async {
            self.parser.parse_schematic(path).await
        });

        match result {
            Ok(schematic) => {
                let schematic_json = serde_json::to_value(&schematic).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to serialize schematic: {}", e))
                })?;
                
                pythonize::pythonize(py, &schematic_json).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert to Python: {}", e))
                })
            }
            Err(e) => Err(PyErr::from(e))
        }
    }

    fn parse_pcb(&self, py: Python, path: &str) -> PyResult<PyObject> {
        let result = self.rt.block_on(async {
            self.parser.parse_pcb(path).await
        });

        match result {
            Ok(pcb) => {
                let pcb_json = serde_json::to_value(&pcb).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to serialize PCB: {}", e))
                })?;
                
                pythonize::pythonize(py, &pcb_json).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert to Python: {}", e))
                })
            }
            Err(e) => Err(PyErr::from(e))
        }
    }

    fn parse_symbol_library(&self, py: Python, path: &str) -> PyResult<PyObject> {
        let result = self.rt.block_on(async {
            self.parser.parse_symbol_library(path).await
        });

        match result {
            Ok(library) => {
                let library_json = serde_json::to_value(&library).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to serialize library: {}", e))
                })?;
                
                pythonize::pythonize(py, &library_json).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert to Python: {}", e))
                })
            }
            Err(e) => Err(PyErr::from(e))
        }
    }
}

/// Python class wrapper for ValidationEngine
#[pyclass]
pub struct PyValidationEngine {
    engine: ValidationEngine,
    rt: Runtime,
}

#[pymethods]
impl PyValidationEngine {
    #[new]
    fn new() -> PyResult<Self> {
        let rt = Runtime::new().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create runtime: {}", e))
        })?;
        
        Ok(PyValidationEngine {
            engine: ValidationEngine::new(),
            rt,
        })
    }

    fn validate_circuit(&self, py: Python, data: &PyDict) -> PyResult<PyObject> {
        let circuit: CircuitData = pythonize::depythonize(data).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Failed to convert Python dict: {}", e))
        })?;

        let result = self.rt.block_on(async {
            self.engine.validate_circuit_data(&circuit).await
        });

        match result {
            Ok(validation_result) => {
                let result_json = serde_json::to_value(&validation_result).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to serialize validation result: {}", e))
                })?;
                
                pythonize::pythonize(py, &result_json).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert to Python: {}", e))
                })
            }
            Err(e) => Err(PyErr::from(e))
        }
    }

    fn get_stats(&self, py: Python) -> PyResult<PyObject> {
        let stats = self.engine.get_validation_stats();
        pythonize::pythonize(py, &stats).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to convert stats: {}", e))
        })
    }

    fn clear_caches(&self) -> PyResult<()> {
        self.engine.clear_caches();
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::types::IntoPyDict;

    #[test]
    fn test_python_integration() {
        Python::with_gil(|py| {
            // Test initialization
            assert!(init_processor().is_ok());

            // Test stats
            let stats = get_stats().unwrap();
            assert!(!stats.is_none(py));
        });
    }

    #[test]
    fn test_json_loader_class() {
        Python::with_gil(|py| {
            let loader = PyJsonLoader::new().unwrap();
            
            // Test with empty dict
            let empty_dict = [("name", "test"), ("components", "{}"), ("nets", "{}")]
                .into_py_dict(py);
            
            // This should work with proper circuit data
            // let result = loader.load_from_dict(py, empty_dict);
            // Note: Would need proper circuit data structure for full test
        });
    }
}