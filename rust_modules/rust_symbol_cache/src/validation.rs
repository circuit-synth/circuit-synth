//! Validation utilities for symbol cache operations
//!
//! This module provides validation functions for:
//! - Symbol data integrity
//! - Library file validation
//! - Cache consistency checks

use crate::{Result, SymbolCacheError, SymbolData};
use std::path::Path;
use tracing::{debug, warn};

impl crate::SymbolLibCache {
    /// Validate symbol data integrity
    pub fn validate_symbol_data(&self, symbol: &SymbolData) -> Result<()> {
        // Check required fields
        if symbol.name.is_empty() {
            return Err(SymbolCacheError::Validation {
                message: "Symbol name cannot be empty".to_string(),
            });
        }

        // Validate symbol name format
        if !self.is_valid_symbol_name(&symbol.name) {
            return Err(SymbolCacheError::Validation {
                message: format!("Invalid symbol name: {}", symbol.name),
            });
        }

        // Validate pins
        for (idx, pin) in symbol.pins.iter().enumerate() {
            if pin.number.is_empty() {
                return Err(SymbolCacheError::Validation {
                    message: format!("Pin {} has empty number", idx),
                });
            }

            // Check for duplicate pin numbers
            let pin_count = symbol
                .pins
                .iter()
                .filter(|p| p.number == pin.number)
                .count();

            if pin_count > 1 {
                return Err(SymbolCacheError::Validation {
                    message: format!("Duplicate pin number: {}", pin.number),
                });
            }
        }

        debug!("Symbol validation passed: {}", symbol.name);
        Ok(())
    }

    /// Validate library file format and accessibility
    pub fn validate_library_file(&self, lib_path: &Path) -> Result<()> {
        // Check file exists
        if !lib_path.exists() {
            return Err(SymbolCacheError::Validation {
                message: format!("Library file does not exist: {}", lib_path.display()),
            });
        }

        // Check file extension
        if lib_path.extension().and_then(|s| s.to_str()) != Some("kicad_sym") {
            return Err(SymbolCacheError::Validation {
                message: format!("Invalid file extension: {}", lib_path.display()),
            });
        }

        // Check file is readable
        if let Err(e) = std::fs::File::open(lib_path) {
            return Err(SymbolCacheError::Validation {
                message: format!("Cannot read library file {}: {}", lib_path.display(), e),
            });
        }

        // Basic content validation
        let content = std::fs::read_to_string(lib_path)?;
        if !content.contains("(kicad_symbol_lib") {
            return Err(SymbolCacheError::Validation {
                message: format!(
                    "Invalid KiCad symbol library format: {}",
                    lib_path.display()
                ),
            });
        }

        debug!("Library file validation passed: {}", lib_path.display());
        Ok(())
    }

    /// Validate cache consistency
    pub fn validate_cache_consistency(&self) -> Result<Vec<String>> {
        let mut issues = Vec::new();

        // Check library index consistency
        for entry in self.inner.library_index.iter() {
            let (lib_name, lib_path) = entry.pair();

            // Check if library file still exists
            if !lib_path.exists() {
                issues.push(format!(
                    "Library file missing: {} -> {}",
                    lib_name,
                    lib_path.display()
                ));
                continue;
            }

            // Validate file
            if let Err(e) = self.validate_library_file(lib_path) {
                issues.push(format!("Library validation failed: {} -> {}", lib_name, e));
            }
        }

        // Check symbol index consistency
        let mut orphaned_symbols = 0;
        for entry in self.inner.symbol_index.iter() {
            let (symbol_name, index_entry) = entry.pair();

            // Check if library exists in library index
            if !self
                .inner
                .library_index
                .contains_key(&index_entry.library_name)
            {
                orphaned_symbols += 1;
                if orphaned_symbols <= 10 {
                    // Limit reporting to avoid spam
                    issues.push(format!(
                        "Orphaned symbol: {} -> library {} not found",
                        symbol_name, index_entry.library_name
                    ));
                }
            }
        }

        if orphaned_symbols > 10 {
            issues.push(format!(
                "... and {} more orphaned symbols",
                orphaned_symbols - 10
            ));
        }

        // Check category consistency
        for entry in self.inner.library_categories.iter() {
            let (lib_name, _category) = entry.pair();

            if !self.inner.library_index.contains_key(lib_name) {
                issues.push(format!("Category entry for missing library: {}", lib_name));
            }
        }

        if issues.is_empty() {
            debug!("Cache consistency validation passed");
        } else {
            warn!("Cache consistency issues found: {}", issues.len());
        }

        Ok(issues)
    }

    /// Repair cache inconsistencies
    pub fn repair_cache_inconsistencies(&self) -> Result<usize> {
        let mut repairs = 0;

        // Remove orphaned symbols from symbol index
        let mut to_remove = Vec::new();
        for entry in self.inner.symbol_index.iter() {
            let (symbol_name, index_entry) = entry.pair();

            if !self
                .inner
                .library_index
                .contains_key(&index_entry.library_name)
            {
                to_remove.push(symbol_name.clone());
            }
        }

        for symbol_name in to_remove {
            self.inner.symbol_index.remove(&symbol_name);
            repairs += 1;
        }

        // Remove orphaned library categories
        let mut to_remove_cats = Vec::new();
        for entry in self.inner.library_categories.iter() {
            let (lib_name, _) = entry.pair();

            if !self.inner.library_index.contains_key(lib_name) {
                to_remove_cats.push(lib_name.clone());
            }
        }

        for lib_name in to_remove_cats {
            self.inner.library_categories.remove(&lib_name);
            repairs += 1;
        }

        // Rebuild category libraries mapping
        self.inner.category_libraries.clear();
        for entry in self.inner.library_categories.iter() {
            let (lib_name, category) = entry.pair();

            self.inner
                .category_libraries
                .entry(category.clone())
                .or_insert_with(Vec::new)
                .push(lib_name.clone());
        }

        if repairs > 0 {
            warn!("Repaired {} cache inconsistencies", repairs);
        } else {
            debug!("No cache repairs needed");
        }

        Ok(repairs)
    }

    /// Validate environment configuration
    pub fn validate_environment(&self) -> Result<Vec<String>> {
        let mut warnings = Vec::new();

        // Check KICAD_SYMBOL_DIR
        if let Ok(kicad_dir) = std::env::var("KICAD_SYMBOL_DIR") {
            let separator = if cfg!(windows) { ";" } else { ":" };
            let dirs: Vec<&str> = kicad_dir.split(separator).collect();

            for dir_str in dirs {
                let dir_path = Path::new(dir_str.trim());
                if !dir_path.exists() {
                    warnings.push(format!(
                        "KICAD_SYMBOL_DIR contains non-existent path: {}",
                        dir_str
                    ));
                } else if !dir_path.is_dir() {
                    warnings.push(format!(
                        "KICAD_SYMBOL_DIR contains non-directory path: {}",
                        dir_str
                    ));
                }
            }
        } else {
            warnings.push("KICAD_SYMBOL_DIR environment variable not set".to_string());
        }

        // Check cache directory
        if !self.inner.config.cache_path.exists() {
            if let Err(e) = std::fs::create_dir_all(&self.inner.config.cache_path) {
                warnings.push(format!(
                    "Cannot create cache directory {}: {}",
                    self.inner.config.cache_path.display(),
                    e
                ));
            }
        } else if !self.inner.config.cache_path.is_dir() {
            warnings.push(format!(
                "Cache path is not a directory: {}",
                self.inner.config.cache_path.display()
            ));
        }

        // Check cache permissions
        if self.inner.config.cache_path.exists() {
            let test_file = self.inner.config.cache_path.join("test_write_permissions");
            if let Err(e) = std::fs::write(&test_file, "test") {
                warnings.push(format!("No write permission to cache directory: {}", e));
            } else {
                let _ = std::fs::remove_file(test_file);
            }
        }

        if warnings.is_empty() {
            debug!("Environment validation passed");
        } else {
            warn!("Environment validation warnings: {}", warnings.len());
        }

        Ok(warnings)
    }

    /// Comprehensive health check
    pub fn health_check(&self) -> Result<HealthReport> {
        let mut report = HealthReport::default();

        // Environment validation
        report.environment_warnings = self.validate_environment()?;

        // Cache consistency
        report.cache_issues = self.validate_cache_consistency()?;

        // Statistics
        report.library_count = self.inner.library_index.len();
        report.symbol_count = self.inner.symbol_index.len();
        report.category_count = self.inner.category_libraries.len();
        report.memory_cache_size = self.inner.symbol_lru.read().len();

        // Performance metrics
        let stats = self.get_cache_stats();
        report.cache_hit_ratio =
            stats
                .get("cache_hits")
                .zip(stats.get("cache_misses"))
                .map(|(hits, misses)| {
                    if hits + misses > 0 {
                        *hits as f32 / (hits + misses) as f32
                    } else {
                        0.0
                    }
                });

        // Overall health
        report.overall_health =
            if report.cache_issues.is_empty() && report.environment_warnings.len() <= 1 {
                HealthStatus::Healthy
            } else if report.cache_issues.len() <= 5 && report.environment_warnings.len() <= 3 {
                HealthStatus::Warning
            } else {
                HealthStatus::Critical
            };

        Ok(report)
    }
}

/// Health status enumeration
#[derive(Debug, Clone, PartialEq)]
pub enum HealthStatus {
    Healthy,
    Warning,
    Critical,
}

/// Comprehensive health report
#[derive(Debug, Clone)]
pub struct HealthReport {
    pub overall_health: HealthStatus,
    pub library_count: usize,
    pub symbol_count: usize,
    pub category_count: usize,
    pub memory_cache_size: usize,
    pub cache_hit_ratio: Option<f32>,
    pub environment_warnings: Vec<String>,
    pub cache_issues: Vec<String>,
}

impl Default for HealthReport {
    fn default() -> Self {
        Self {
            overall_health: HealthStatus::Healthy,
            library_count: 0,
            symbol_count: 0,
            category_count: 0,
            memory_cache_size: 0,
            cache_hit_ratio: None,
            environment_warnings: Vec::new(),
            cache_issues: Vec::new(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{PinData, SymbolData, SymbolLibCache};
    use std::collections::HashMap;

    #[test]
    fn test_symbol_validation() {
        let cache = SymbolLibCache::new();

        // Valid symbol
        let valid_symbol = SymbolData {
            name: "R".to_string(),
            description: Some("Resistor".to_string()),
            datasheet: None,
            keywords: None,
            fp_filters: None,
            pins: vec![
                PinData {
                    name: "~".to_string(),
                    number: "1".to_string(),
                    pin_type: "passive".to_string(),
                    unit: 1,
                    x: 0.0,
                    y: 0.0,
                    length: 2.54,
                    orientation: 0,
                },
                PinData {
                    name: "~".to_string(),
                    number: "2".to_string(),
                    pin_type: "passive".to_string(),
                    unit: 1,
                    x: 5.08,
                    y: 0.0,
                    length: 2.54,
                    orientation: 180,
                },
            ],
            properties: HashMap::new(),
        };

        assert!(cache.validate_symbol_data(&valid_symbol).is_ok());

        // Invalid symbol - empty name
        let invalid_symbol = SymbolData {
            name: "".to_string(),
            description: None,
            datasheet: None,
            keywords: None,
            fp_filters: None,
            pins: Vec::new(),
            properties: HashMap::new(),
        };

        assert!(cache.validate_symbol_data(&invalid_symbol).is_err());
    }
}
