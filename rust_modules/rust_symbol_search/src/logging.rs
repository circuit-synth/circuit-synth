/*!
Rust Logging Bridge for Circuit Synth Unified Logging
====================================================

This module provides logging integration between Rust components and the
Python unified logging system using pyo3-log. All Rust log messages are
forwarded to the Python logging system where they are processed with
full user context and performance tracking.

Usage:
    use log::{info, warn, error, debug};
    
    info!("Starting symbol search for query: {}", query);
    debug!("Processing {} symbols", symbol_count);
    error!("Failed to load symbol file: {}", error);
*/

use log::{info, warn, error, debug, trace};
use std::time::Instant;

/// Initialize the Rust logging system to forward to Python
/// 
/// This function should be called once when the Rust module is loaded
/// to set up the logging bridge with the Python unified logging system.
#[cfg(feature = "python-bindings")]
pub fn init_logging() {
    // Initialize pyo3-log to forward Rust logs to Python
    pyo3_log::init();
    
    info!("Rust logging bridge initialized for Circuit Synth");
}

/// Log a performance timing measurement
/// 
/// This function logs timing information that will be captured by the
/// Python performance monitoring system.
pub fn log_performance_timing(operation: &str, duration_ms: f64, metadata: Option<&str>) {
    let metadata_str = metadata.unwrap_or("{}");
    info!(
        "PERF_TIMING: operation={} duration_ms={:.2} metadata={}",
        operation, duration_ms, metadata_str
    );
}

/// Log an error with context information
/// 
/// Provides structured error logging that integrates with the Python
/// error tracking and alerting system.
pub fn log_error_with_context(
    operation: &str,
    error_msg: &str,
    error_type: &str,
    context: Option<&str>
) {
    let context_str = context.unwrap_or("{}");
    error!(
        "ERROR_CONTEXT: operation={} error_type={} error_msg={} context={}",
        operation, error_type, error_msg, context_str
    );
}

/// Log a warning with additional metadata
pub fn log_warning_with_metadata(message: &str, metadata: Option<&str>) {
    let metadata_str = metadata.unwrap_or("{}");
    warn!("WARNING_META: message={} metadata={}", message, metadata_str);
}

/// Log debug information with structured data
pub fn log_debug_structured(component: &str, message: &str, data: Option<&str>) {
    let data_str = data.unwrap_or("{}");
    debug!("DEBUG_STRUCT: component={} message={} data={}", component, message, data_str);
}

/// Timer utility for measuring operation performance
/// 
/// This struct provides a convenient way to measure and log the duration
/// of operations in Rust code.
pub struct PerformanceTimer {
    operation: String,
    start_time: Instant,
    metadata: Option<String>,
}

impl PerformanceTimer {
    /// Create a new performance timer for the given operation
    pub fn new(operation: &str) -> Self {
        debug!("Starting timer for operation: {}", operation);
        Self {
            operation: operation.to_string(),
            start_time: Instant::now(),
            metadata: None,
        }
    }
    
    /// Create a new performance timer with metadata
    pub fn with_metadata(operation: &str, metadata: &str) -> Self {
        debug!("Starting timer for operation: {} with metadata: {}", operation, metadata);
        Self {
            operation: operation.to_string(),
            start_time: Instant::now(),
            metadata: Some(metadata.to_string()),
        }
    }
    
    /// Add metadata to the timer
    pub fn add_metadata(&mut self, metadata: &str) {
        self.metadata = Some(metadata.to_string());
    }
    
    /// Get the current elapsed time in milliseconds
    pub fn elapsed_ms(&self) -> f64 {
        self.start_time.elapsed().as_secs_f64() * 1000.0
    }
    
    /// Finish the timer and log the performance data
    pub fn finish(self) {
        let duration_ms = self.elapsed_ms();
        log_performance_timing(
            &self.operation,
            duration_ms,
            self.metadata.as_deref()
        );
        
        info!(
            "Operation '{}' completed in {:.2}ms",
            self.operation, duration_ms
        );
    }
    
    /// Finish the timer with a custom message
    pub fn finish_with_message(self, message: &str) {
        let duration_ms = self.elapsed_ms();
        log_performance_timing(
            &self.operation,
            duration_ms,
            self.metadata.as_deref()
        );
        
        info!(
            "Operation '{}' completed in {:.2}ms: {}",
            self.operation, duration_ms, message
        );
    }
}

impl Drop for PerformanceTimer {
    /// Automatically log performance data when timer is dropped
    fn drop(&mut self) {
        let duration_ms = self.elapsed_ms();
        log_performance_timing(
            &self.operation,
            duration_ms,
            self.metadata.as_deref()
        );
        
        debug!(
            "Auto-finished timer for '{}': {:.2}ms",
            self.operation, duration_ms
        );
    }
}

/// Macro for creating a scoped performance timer
/// 
/// This macro creates a performance timer that automatically logs
/// when it goes out of scope.
#[macro_export]
macro_rules! perf_timer {
    ($operation:expr) => {
        let _timer = $crate::logging::PerformanceTimer::new($operation);
    };
    ($operation:expr, $metadata:expr) => {
        let _timer = $crate::logging::PerformanceTimer::with_metadata($operation, $metadata);
    };
}

/// Macro for logging function entry and exit
/// 
/// This macro logs when a function is entered and exited, along with
/// timing information.
#[macro_export]
macro_rules! log_function {
    ($func_name:expr) => {
        debug!("Entering function: {}", $func_name);
        let _func_timer = $crate::logging::PerformanceTimer::new(&format!("function_{}", $func_name));
    };
    ($func_name:expr, $($arg:expr),*) => {
        debug!("Entering function: {} with args: {:?}", $func_name, ($($arg,)*));
        let _func_timer = $crate::logging::PerformanceTimer::new(&format!("function_{}", $func_name));
    };
}

/// Log memory usage information
/// 
/// This function logs current memory usage statistics that can be
/// correlated with performance data in the Python system.
pub fn log_memory_usage(operation: &str, bytes_used: usize) {
    let mb_used = bytes_used as f64 / (1024.0 * 1024.0);
    info!(
        "MEMORY_USAGE: operation={} bytes={} mb={:.2}",
        operation, bytes_used, mb_used
    );
}

/// Log cache statistics
/// 
/// Logs cache hit/miss statistics for performance analysis.
pub fn log_cache_stats(cache_name: &str, hits: u64, misses: u64, hit_rate: f64) {
    info!(
        "CACHE_STATS: cache={} hits={} misses={} hit_rate={:.3}",
        cache_name, hits, misses, hit_rate
    );
}

/// Log file operation statistics
/// 
/// Logs file I/O operations for performance monitoring.
pub fn log_file_operation(
    operation: &str,
    file_path: &str,
    bytes_processed: usize,
    duration_ms: f64
) {
    let mb_processed = bytes_processed as f64 / (1024.0 * 1024.0);
    let throughput_mbps = if duration_ms > 0.0 {
        mb_processed / (duration_ms / 1000.0)
    } else {
        0.0
    };
    
    info!(
        "FILE_OP: operation={} file={} bytes={} mb={:.2} duration_ms={:.2} throughput_mbps={:.2}",
        operation, file_path, bytes_processed, mb_processed, duration_ms, throughput_mbps
    );
}

/// Log search operation results
/// 
/// Logs search operation statistics for performance analysis.
pub fn log_search_results(
    query: &str,
    total_items: usize,
    results_found: usize,
    duration_ms: f64
) {
    let hit_rate = if total_items > 0 {
        results_found as f64 / total_items as f64
    } else {
        0.0
    };
    
    info!(
        "SEARCH_RESULTS: query={} total_items={} results_found={} hit_rate={:.3} duration_ms={:.2}",
        query, total_items, results_found, hit_rate, duration_ms
    );
}

/// Log component initialization
/// 
/// Logs when Rust components are initialized.
pub fn log_component_init(component_name: &str, version: &str) {
    info!(
        "COMPONENT_INIT: component={} version={} timestamp={}",
        component_name,
        version,
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs()
    );
}

/// Log component shutdown
/// 
/// Logs when Rust components are shut down.
pub fn log_component_shutdown(component_name: &str, uptime_ms: f64) {
    info!(
        "COMPONENT_SHUTDOWN: component={} uptime_ms={:.2}",
        component_name, uptime_ms
    );
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;
    use std::time::Duration;

    #[test]
    fn test_performance_timer() {
        let timer = PerformanceTimer::new("test_operation");
        thread::sleep(Duration::from_millis(10));
        let elapsed = timer.elapsed_ms();
        assert!(elapsed >= 10.0);
        timer.finish();
    }

    #[test]
    fn test_performance_timer_with_metadata() {
        let timer = PerformanceTimer::with_metadata("test_operation", "test_metadata");
        thread::sleep(Duration::from_millis(5));
        timer.finish_with_message("Test completed successfully");
    }

    #[test]
    fn test_logging_functions() {
        log_memory_usage("test", 1024 * 1024);
        log_cache_stats("test_cache", 100, 10, 0.9);
        log_file_operation("read", "/tmp/test.txt", 1024, 5.0);
        log_search_results("test_query", 1000, 50, 25.0);
        log_component_init("test_component", "1.0.0");
        log_component_shutdown("test_component", 60000.0);
    }
}