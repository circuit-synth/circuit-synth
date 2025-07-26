//! Symbol indexer for building complete library and symbol indices
//! 
//! This module provides:
//! - Parallel library scanning
//! - Symbol index building
//! - Library categorization
//! - Index persistence and loading

use crate::{Result, SymbolCacheError, SymbolIndexEntry};
use rayon::prelude::*;
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use tracing::{debug, info, warn};

impl crate::SymbolLibCache {
    /// Ensure the symbol index is built
    pub(crate) fn ensure_index_built(&self) -> Result<()> {
        let mut index_built = self.inner.index_built.lock();
        if *index_built {
            info!("🔍 [ENSURE_INDEX] Index already built - {} libraries, {} symbols",
                  self.inner.library_index.len(), self.inner.symbol_index.len());
            return Ok(());
        }
        
        info!("🔍 [ENSURE_INDEX] Building symbol index...");
        
        // Try to load from cache first
        if self.inner.config.enabled && !self.inner.config.force_rebuild {
            info!("🔍 [ENSURE_INDEX] Attempting to load from cache...");
            if self.load_index_from_cache()? {
                info!("✅ [ENSURE_INDEX] Loaded symbol index from cache: {} libraries, {} symbols",
                      self.inner.library_index.len(), self.inner.symbol_index.len());
                self.build_library_categorization();
                *index_built = true;
                return Ok(());
            } else {
                info!("❌ [ENSURE_INDEX] Failed to load from cache, building fresh...");
            }
        } else {
            info!("🔍 [ENSURE_INDEX] Cache disabled or force rebuild set, building fresh...");
        }
        
        // Build fresh index
        self.build_complete_index_fresh()?;
        *index_built = true;
        
        info!("✅ [ENSURE_INDEX] Index build complete - {} libraries, {} symbols",
              self.inner.library_index.len(), self.inner.symbol_index.len());
        
        Ok(())
    }
    
    /// Build complete index from scratch
    fn build_complete_index_fresh(&self) -> Result<()> {
        info!("Building complete symbol library index...");
        
        let symbol_dirs = self.get_symbol_directories();
        if symbol_dirs.is_empty() {
            warn!("No valid KiCad symbol directories found");
            return Ok(());
        }
        
        info!("Scanning symbol libraries in {} directories:", symbol_dirs.len());
        for dir in &symbol_dirs {
            info!("  - {}", dir.display());
        }
        
        // Clear existing indices
        self.inner.library_index.clear();
        self.inner.symbol_index.clear();
        
        // Scan directories in parallel
        let all_libraries: Vec<PathBuf> = symbol_dirs
            .par_iter()
            .map(|dir| self.scan_directory_for_libraries(dir))
            .reduce(Vec::new, |mut acc, mut libs| {
                acc.append(&mut libs);
                acc
            });
        
        info!("Found {} symbol library files", all_libraries.len());
        
        // Process libraries in parallel
        let library_data: Vec<(String, PathBuf, Vec<String>)> = all_libraries
            .par_iter()
            .filter_map(|lib_path| {
                let lib_name = lib_path.file_stem()?.to_string_lossy().to_string();
                
                // Handle duplicate library names
                let unique_name = self.get_unique_library_name(&lib_name);
                
                match self.extract_symbols_from_library(lib_path) {
                    Ok(symbols) => {
                        debug!("Indexed {} symbols from {}", symbols.len(), unique_name);
                        Some((unique_name, lib_path.clone(), symbols))
                    }
                    Err(e) => {
                        warn!("Failed to index symbols from {}: {}", lib_path.display(), e);
                        None
                    }
                }
            })
            .collect();
        
        // Build indices
        for (lib_name, lib_path, symbols) in library_data {
            // Add to library index
            self.inner.library_index.insert(lib_name.clone(), lib_path.clone());
            
            // Add symbols to symbol index
            for symbol_name in symbols {
                // Only add if not already present (first library wins)
                if !self.inner.symbol_index.contains_key(&symbol_name) {
                    let entry = SymbolIndexEntry {
                        symbol_name: symbol_name.clone(),
                        library_name: lib_name.clone(),
                        library_path: lib_path.clone(),
                        category: self.categorize_library(&lib_name),
                    };
                    self.inner.symbol_index.insert(symbol_name, entry);
                }
            }
        }
        
        info!("Symbol index built: {} libraries, {} symbols",
              self.inner.library_index.len(), self.inner.symbol_index.len());
        
        // Save to cache
        if self.inner.config.enabled {
            if let Err(e) = self.save_index_to_cache() {
                warn!("Failed to save index to cache: {}", e);
            }
        }
        
        // Build categorization
        self.build_library_categorization();
        
        Ok(())
    }
    
    /// Scan a directory for .kicad_sym files
    fn scan_directory_for_libraries(&self, dir: &Path) -> Vec<PathBuf> {
        let mut libraries = Vec::new();
        
        if let Ok(entries) = std::fs::read_dir(dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.extension().and_then(|s| s.to_str()) == Some("kicad_sym") {
                    libraries.push(path);
                }
            }
        }
        
        // Also scan subdirectories
        if let Ok(entries) = std::fs::read_dir(dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_dir() {
                    libraries.extend(self.scan_directory_for_libraries(&path));
                }
            }
        }
        
        libraries
    }
    
    /// Extract symbol names from a library file
    fn extract_symbols_from_library(&self, lib_path: &Path) -> Result<Vec<String>> {
        let content = std::fs::read_to_string(lib_path)?;
        Ok(self.extract_symbol_names_fast(&content))
    }
    
    /// Get unique library name to handle duplicates
    fn get_unique_library_name(&self, base_name: &str) -> String {
        let mut name = base_name.to_string();
        let mut counter = 1;
        
        while self.inner.library_index.contains_key(&name) {
            name = format!("{}_{}", base_name, counter);
            counter += 1;
        }
        
        name
    }
    
    /// Build library categorization for tier-based search
    pub(crate) fn build_library_categorization(&self) {
        info!("Building library categorization for tier-based routing...");
        
        self.inner.library_categories.clear();
        self.inner.category_libraries.clear();
        
        // Define category patterns
        let category_patterns = self.get_category_patterns();
        
        // Categorize each library
        for entry in self.inner.library_index.iter() {
            let (lib_name, _) = entry.pair();
            let category = self.categorize_library_with_patterns(lib_name, &category_patterns);
            
            self.inner.library_categories.insert(lib_name.clone(), category.clone());
            
            // Add to category->libraries mapping
            self.inner.category_libraries
                .entry(category.clone())
                .or_insert_with(Vec::new)
                .push(lib_name.clone());
        }
        
        // Log categorization results
        let total_libs = self.inner.library_index.len();
        let categorized_libs: usize = self.inner.category_libraries
            .iter()
            .map(|entry| entry.value().len())
            .sum();
        
        info!("Library categorization complete:");
        for entry in self.inner.category_libraries.iter() {
            let (category, libs) = entry.pair();
            info!("  {}: {} libraries", category, libs.len());
        }
        
        info!("Total: {}/{} libraries categorized", categorized_libs, total_libs);
    }
    
    /// Get category patterns for library classification
    fn get_category_patterns(&self) -> HashMap<String, Vec<String>> {
        let mut patterns = HashMap::new();
        
        patterns.insert("connectors".to_string(), vec![
            "Connector".to_string(), "connector".to_string(), "USB".to_string(), "usb".to_string(),
            "Jack".to_string(), "jack".to_string(), "Header".to_string(), "header".to_string(),
            "Socket".to_string(), "socket".to_string(), "Plug".to_string(), "plug".to_string(),
            "Terminal".to_string(), "terminal".to_string(),
        ]);
        
        patterns.insert("microcontrollers".to_string(), vec![
            "MCU".to_string(), "mcu".to_string(), "Microcontroller".to_string(), "microcontroller".to_string(),
            "ESP".to_string(), "esp".to_string(), "STM".to_string(), "stm".to_string(),
            "Arduino".to_string(), "arduino".to_string(), "Processor".to_string(), "processor".to_string(),
            "CPU".to_string(), "cpu".to_string(),
        ]);
        
        patterns.insert("sensors".to_string(), vec![
            "Sensor".to_string(), "sensor".to_string(), "Motion".to_string(), "motion".to_string(),
            "Temperature".to_string(), "temperature".to_string(), "Humidity".to_string(), "humidity".to_string(),
            "Pressure".to_string(), "pressure".to_string(), "Accelerometer".to_string(), "accelerometer".to_string(),
            "Gyroscope".to_string(), "gyroscope".to_string(), "IMU".to_string(), "imu".to_string(),
        ]);
        
        patterns.insert("power".to_string(), vec![
            "Regulator".to_string(), "regulator".to_string(), "Power".to_string(), "power".to_string(),
            "Converter".to_string(), "converter".to_string(), "Battery".to_string(), "battery".to_string(),
            "Charger".to_string(), "charger".to_string(), "Supply".to_string(), "supply".to_string(),
            "LDO".to_string(), "ldo".to_string(), "Buck".to_string(), "buck".to_string(),
            "Boost".to_string(), "boost".to_string(),
        ]);
        
        patterns.insert("leds".to_string(), vec![
            "LED".to_string(), "led".to_string(), "Light".to_string(), "light".to_string(),
            "Display".to_string(), "display".to_string(), "Addressable".to_string(), "addressable".to_string(),
            "RGB".to_string(), "rgb".to_string(), "WS28".to_string(), "ws28".to_string(),
            "SK68".to_string(), "sk68".to_string(), "Neopixel".to_string(), "neopixel".to_string(),
        ]);
        
        patterns.insert("rf".to_string(), vec![
            "RF".to_string(), "rf".to_string(), "Antenna".to_string(), "antenna".to_string(),
            "Wireless".to_string(), "wireless".to_string(), "Bluetooth".to_string(), "bluetooth".to_string(),
            "WiFi".to_string(), "wifi".to_string(), "Radio".to_string(), "radio".to_string(),
            "Transceiver".to_string(), "transceiver".to_string(),
        ]);
        
        patterns.insert("analog".to_string(), vec![
            "Amplifier".to_string(), "amplifier".to_string(), "OpAmp".to_string(), "opamp".to_string(),
            "Comparator".to_string(), "comparator".to_string(), "Filter".to_string(), "filter".to_string(),
            "Analog".to_string(), "analog".to_string(), "ADC".to_string(), "adc".to_string(),
            "DAC".to_string(), "dac".to_string(),
        ]);
        
        patterns.insert("digital".to_string(), vec![
            "Logic".to_string(), "logic".to_string(), "Digital".to_string(), "digital".to_string(),
            "Gate".to_string(), "gate".to_string(), "Counter".to_string(), "counter".to_string(),
            "Decoder".to_string(), "decoder".to_string(), "Encoder".to_string(), "encoder".to_string(),
            "Multiplexer".to_string(), "multiplexer".to_string(),
        ]);
        
        patterns.insert("passive".to_string(), vec![
            "Device".to_string(), "device".to_string(), "Resistor".to_string(), "resistor".to_string(),
            "Capacitor".to_string(), "capacitor".to_string(), "Inductor".to_string(), "inductor".to_string(),
            "Crystal".to_string(), "crystal".to_string(), "Oscillator".to_string(), "oscillator".to_string(),
        ]);
        
        patterns.insert("memory".to_string(), vec![
            "Memory".to_string(), "memory".to_string(), "EEPROM".to_string(), "eeprom".to_string(),
            "Flash".to_string(), "flash".to_string(), "RAM".to_string(), "ram".to_string(),
            "Storage".to_string(), "storage".to_string(), "FRAM".to_string(), "fram".to_string(),
        ]);
        
        patterns
    }
    
    /// Categorize a library based on its name and patterns
    pub(crate) fn categorize_library(&self, lib_name: &str) -> String {
        let patterns = self.get_category_patterns();
        self.categorize_library_with_patterns(lib_name, &patterns)
    }
    
    /// Categorize library with provided patterns
    fn categorize_library_with_patterns(
        &self,
        lib_name: &str,
        patterns: &HashMap<String, Vec<String>>,
    ) -> String {
        let lib_lower = lib_name.to_lowercase();
        
        // Check each category's patterns
        for (category, pattern_list) in patterns {
            for pattern in pattern_list {
                if lib_lower.contains(&pattern.to_lowercase()) {
                    return category.clone();
                }
            }
        }
        
        // Default category
        "general".to_string()
    }
    
    /// Load index from disk cache
    fn load_index_from_cache(&self) -> Result<bool> {
        let cache_file = self.inner.config.cache_path.join("symbol_index.json");
        
        info!("Loading symbol index from cache: {}", cache_file.display());
        
        if !cache_file.exists() {
            info!("No symbol index cache file found at: {}", cache_file.display());
            return Ok(false);
        }
        
        let content = std::fs::read_to_string(&cache_file)?;
        let cache_data: serde_json::Value = serde_json::from_str(&content)?;
        
        // Check cache expiration
        let cache_time = cache_data["cache_time"].as_u64().unwrap_or(0);
        let current_time = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        let ttl_seconds = self.inner.config.ttl_hours * 3600;
        if current_time - cache_time > ttl_seconds {
            debug!("Symbol index cache expired");
            return Ok(false);
        }
        
        // Load library index
        if let Some(lib_index) = cache_data["library_index"].as_object() {
            for (name, path_value) in lib_index {
                if let Some(path_str) = path_value.as_str() {
                    self.inner.library_index.insert(name.clone(), PathBuf::from(path_str));
                }
            }
        }
        
        // Load symbol index
        if let Some(sym_index) = cache_data["symbol_index"].as_object() {
            for (symbol_name, entry_value) in sym_index {
                if let Ok(entry) = serde_json::from_value::<SymbolIndexEntry>(entry_value.clone()) {
                    self.inner.symbol_index.insert(symbol_name.clone(), entry);
                }
            }
        }
        
        debug!("Successfully loaded symbol index from cache");
        Ok(true)
    }
    
    /// Save index to disk cache
    fn save_index_to_cache(&self) -> Result<()> {
        if !self.inner.config.enabled {
            return Ok(());
        }
        
        let cache_file = self.inner.config.cache_path.join("symbol_index.json");
        
        info!("Saving symbol index to cache: {}", cache_file.display());
        
        // Ensure cache directory exists
        if let Some(parent) = cache_file.parent() {
            std::fs::create_dir_all(parent)?;
            debug!("Created cache directory: {}", parent.display());
        }
        
        let current_time = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        // Build cache data
        let mut cache_data = serde_json::Map::new();
        cache_data.insert("cache_time".to_string(), serde_json::Value::Number(current_time.into()));
        cache_data.insert("version".to_string(), serde_json::Value::String("1.0.0".to_string()));
        cache_data.insert("library_count".to_string(), serde_json::Value::Number(self.inner.library_index.len().into()));
        cache_data.insert("symbol_count".to_string(), serde_json::Value::Number(self.inner.symbol_index.len().into()));
        
        // Library index
        let mut lib_index = serde_json::Map::new();
        for entry in self.inner.library_index.iter() {
            let (name, path) = entry.pair();
            lib_index.insert(name.clone(), serde_json::Value::String(path.to_string_lossy().to_string()));
        }
        cache_data.insert("library_index".to_string(), serde_json::Value::Object(lib_index));
        
        // Symbol index
        let mut sym_index = serde_json::Map::new();
        for entry in self.inner.symbol_index.iter() {
            let (name, index_entry) = entry.pair();
            if let Ok(value) = serde_json::to_value(index_entry.clone()) {
                sym_index.insert(name.clone(), value);
            }
        }
        cache_data.insert("symbol_index".to_string(), serde_json::Value::Object(sym_index));
        
        let content = serde_json::to_string_pretty(&cache_data)?;
        
        // Write to temporary file first, then rename for atomic operation
        let temp_file = cache_file.with_extension("tmp");
        std::fs::write(&temp_file, &content)?;
        std::fs::rename(&temp_file, &cache_file)?;
        
        info!("✓ Saved symbol index to cache: {} libraries, {} symbols",
              self.inner.library_index.len(), self.inner.symbol_index.len());
        
        // Update cache metadata
        if let Err(e) = self.update_cache_metadata() {
            warn!("Failed to update cache metadata: {}", e);
        }
        
        Ok(())
    }
}