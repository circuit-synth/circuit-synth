//! Cache implementation for symbol library data
//! 
//! This module handles the core caching logic including:
//! - File-based cache persistence
//! - TTL validation
//! - Hash-based cache invalidation
//! - Concurrent cache operations

use crate::{LibraryData, LibraryMetadata, Result, SymbolCacheError, SymbolData};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};
use tracing::{debug, info, warn};

impl crate::SymbolLibCache {
    /// Load library data from cache or parse fresh
    pub(crate) fn load_library(&self, lib_name: &str) -> Result<Arc<LibraryData>> {
        
        // Check in-memory cache first
        if let Some(cached) = self.inner.library_cache.get(lib_name) {
            if self.is_cache_valid(&cached.metadata)? {
                debug!("Using valid in-memory cache for {}", lib_name);
                return Ok(cached.clone());
            } else {
                debug!("In-memory cache invalid for {}", lib_name);
                self.inner.library_cache.remove(lib_name);
            }
        }
        
        // Find library file
        let lib_path = self.find_library_file(lib_name)?;
        
        // Check disk cache
        if self.inner.config.enabled && !self.inner.config.force_rebuild {
            info!("Checking disk cache for library: {}", lib_name);
            match self.load_from_disk_cache(&lib_path) {
                Ok(cached_data) => {
                    if self.is_cache_valid(&cached_data.metadata)? {
                        info!("✓ Loaded library from valid disk cache: {} ({} symbols)",
                              lib_name, cached_data.symbols.len());
                        let arc_data = Arc::new(cached_data);
                        self.inner.library_cache.insert(lib_name.to_string(), arc_data.clone());
                        return Ok(arc_data);
                    } else {
                        info!("✗ Disk cache invalid for {}, will rebuild", lib_name);
                    }
                }
                Err(e) => {
                    debug!("Failed to load disk cache for {}: {}", lib_name, e);
                }
            }
        }
        
        // Parse fresh
        self.parse_library_fresh(&lib_path, lib_name)
    }
    
    /// Parse library fresh and cache the result
    fn parse_library_fresh(&self, lib_path: &Path, lib_name: &str) -> Result<Arc<LibraryData>> {
        use std::sync::Arc;
        
        info!("Parsing .kicad_sym file: {}", lib_path.display());
        
        // Compute file hash
        let file_hash = self.compute_file_hash(lib_path)?;
        let cache_time = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        // Parse symbols
        let symbols = if self.inner.config.parallel_parsing {
            self.parse_symbols_parallel(lib_path)?
        } else {
            self.parse_symbols_sequential(lib_path)?
        };
        
        // Create library data
        let metadata = LibraryMetadata {
            name: lib_name.to_string(),
            path: lib_path.to_path_buf(),
            file_hash,
            cache_time,
            symbol_count: symbols.len(),
            category: self.categorize_library(lib_name),
        };
        
        let library_data = LibraryData { metadata, symbols };
        let arc_data = Arc::new(library_data);
        
        // Store in memory cache
        self.inner.library_cache.insert(lib_name.to_string(), arc_data.clone());
        
        // Store to disk cache if enabled
        if self.inner.config.enabled {
            info!("Saving library to disk cache: {}", lib_name);
            match self.save_to_disk_cache(&arc_data) {
                Ok(()) => {
                    info!("✓ Successfully saved library cache: {} ({} symbols)",
                          lib_name, arc_data.symbols.len());
                }
                Err(e) => {
                    warn!("✗ Failed to save library cache to disk: {}", e);
                }
            }
        }
        
        info!("✓ Parsed {} symbols from {}", arc_data.symbols.len(), lib_name);
        Ok(arc_data)
    }
    
    /// Parse symbols using parallel processing
    fn parse_symbols_parallel(&self, lib_path: &Path) -> Result<HashMap<String, SymbolData>> {
        use rayon::prelude::*;
        
        // Read file content
        let content = fs::read_to_string(lib_path)?;
        
        // Extract symbol definitions
        let symbol_texts = self.extract_symbol_texts(&content)?;
        
        // Create map of all symbols for inheritance resolution
        let all_symbols: HashMap<String, String> = symbol_texts.iter()
            .map(|(name, text)| (name.clone(), text.clone()))
            .collect();
        
        // Parse symbols in parallel with inheritance support
        let symbols: Result<Vec<(String, SymbolData)>> = symbol_texts
            .par_iter()
            .map(|(name, text)| {
                let symbol_data = self.parse_symbol_with_inheritance(text, &all_symbols)?;
                Ok((name.clone(), symbol_data))
            })
            .collect();
        
        Ok(symbols?.into_iter().collect())
    }
    
    /// Parse symbols sequentially
    fn parse_symbols_sequential(&self, lib_path: &Path) -> Result<HashMap<String, SymbolData>> {
        let content = fs::read_to_string(lib_path)?;
        let symbol_texts = self.extract_symbol_texts(&content)?;
        
        // Create map of all symbols for inheritance resolution
        let all_symbols: HashMap<String, String> = symbol_texts.iter()
            .map(|(name, text)| (name.clone(), text.clone()))
            .collect();
        
        let mut symbols = HashMap::new();
        for (name, text) in symbol_texts {
            let symbol_data = self.parse_symbol_with_inheritance(&text, &all_symbols)?;
            symbols.insert(name, symbol_data);
        }
        
        Ok(symbols)
    }
    
    /// Check if cache is valid based on TTL and file hash
    fn is_cache_valid(&self, metadata: &LibraryMetadata) -> Result<bool> {
        // Check TTL
        let current_time = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        let ttl_seconds = self.inner.config.ttl_hours * 3600;
        if current_time - metadata.cache_time > ttl_seconds {
            debug!("Cache expired for {}", metadata.name);
            return Ok(false);
        }
        
        // Check file hash
        if metadata.path.exists() {
            let current_hash = self.compute_file_hash(&metadata.path)?;
            if current_hash != metadata.file_hash {
                debug!("File hash mismatch for {}", metadata.name);
                return Ok(false);
            }
        } else {
            debug!("Library file no longer exists: {}", metadata.path.display());
            return Ok(false);
        }
        
        Ok(true)
    }
    
    /// Compute SHA-256 hash of a file
    pub(crate) fn compute_file_hash(&self, file_path: &Path) -> Result<String> {
        let content = fs::read(file_path)?;
        let mut hasher = Sha256::new();
        hasher.update(&content);
        Ok(format!("{:x}", hasher.finalize()))
    }
    
    /// Load library data from disk cache
    fn load_from_disk_cache(&self, lib_path: &Path) -> Result<LibraryData> {
        let cache_file = self.get_cache_file_path(lib_path);
        let content = fs::read_to_string(cache_file)?;
        let library_data: LibraryData = serde_json::from_str(&content)?;
        Ok(library_data)
    }
    
    /// Save library data to disk cache
    fn save_to_disk_cache(&self, library_data: &LibraryData) -> Result<()> {
        let cache_file = self.get_cache_file_path(&library_data.metadata.path);
        
        debug!("Saving library cache to: {}", cache_file.display());
        
        // Ensure cache directory exists
        if let Some(parent) = cache_file.parent() {
            fs::create_dir_all(parent)?;
            debug!("Created cache directory: {}", parent.display());
        }
        
        // Serialize library data
        let content = serde_json::to_string_pretty(library_data)?;
        
        // Write to temporary file first, then rename for atomic operation
        let temp_file = cache_file.with_extension("tmp");
        fs::write(&temp_file, &content)?;
        fs::rename(&temp_file, &cache_file)?;
        
        debug!("✓ Saved library cache: {} -> {}",
               library_data.metadata.name, cache_file.display());
        
        // Update cache metadata
        if let Err(e) = self.update_cache_metadata() {
            warn!("Failed to update cache metadata: {}", e);
        }
        
        Ok(())
    }
    
    /// Get cache file path for a library
    fn get_cache_file_path(&self, lib_path: &Path) -> PathBuf {
        let mut hasher = Sha256::new();
        hasher.update(lib_path.to_string_lossy().as_bytes());
        let path_hash = format!("{:x}", hasher.finalize())[..8].to_string();
        
        let stem = lib_path.file_stem()
            .unwrap_or_default()
            .to_string_lossy()
            .replace('.', "_");
        
        let cache_filename = format!("{}_{}.json", stem, path_hash);
        self.inner.config.cache_path.join("libraries").join(cache_filename)
    }
    
    /// Find library file by name
    pub(crate) fn find_library_file(&self, lib_name: &str) -> Result<PathBuf> {
        // Check library index first
        if let Some(path) = self.inner.library_index.get(lib_name) {
            return Ok(path.clone());
        }
        
        // Search in KICAD_SYMBOL_DIR
        let symbol_dirs = self.get_symbol_directories();
        for dir in symbol_dirs {
            let lib_file = dir.join(format!("{}.kicad_sym", lib_name));
            if lib_file.exists() {
                return Ok(lib_file);
            }
        }
        
        Err(SymbolCacheError::LibraryNotFound {
            library_name: lib_name.to_string(),
        })
    }
    
    /// Get symbol directories from environment
    pub(crate) fn get_symbol_directories(&self) -> Vec<PathBuf> {
        let mut dirs = Vec::new();
        
        info!("🔍 [GET_SYMBOL_DIRS] Searching for KiCad symbol directories...");
        
        // Check KICAD_SYMBOL_DIR environment variable
        if let Ok(kicad_dir) = std::env::var("KICAD_SYMBOL_DIR") {
            info!("🔍 [GET_SYMBOL_DIRS] Found KICAD_SYMBOL_DIR: {}", kicad_dir);
            let separator = if cfg!(windows) { ";" } else { ":" };
            for dir_str in kicad_dir.split(separator) {
                let dir_path = PathBuf::from(dir_str.trim());
                info!("🔍 [GET_SYMBOL_DIRS] Checking env dir: {}", dir_path.display());
                if dir_path.exists() && dir_path.is_dir() {
                    info!("✅ [GET_SYMBOL_DIRS] Found valid env dir: {}", dir_path.display());
                    dirs.push(dir_path);
                } else {
                    info!("❌ [GET_SYMBOL_DIRS] Env dir not found/invalid: {}", dir_path.display());
                }
            }
        } else {
            info!("🔍 [GET_SYMBOL_DIRS] KICAD_SYMBOL_DIR not set");
        }
        
        // Add default directories if none found
        if dirs.is_empty() {
            info!("🔍 [GET_SYMBOL_DIRS] No env dirs found, checking default directories...");
            let default_dirs = [
                "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/",
                "/usr/share/kicad/symbols/",
                "C:\\Program Files\\KiCad\\share\\kicad\\symbols\\",
            ];
            
            for dir_str in &default_dirs {
                let dir_path = PathBuf::from(dir_str);
                info!("🔍 [GET_SYMBOL_DIRS] Checking default dir: {}", dir_path.display());
                if dir_path.exists() && dir_path.is_dir() {
                    info!("✅ [GET_SYMBOL_DIRS] Found valid default dir: {}", dir_path.display());
                    dirs.push(dir_path);
                    break;
                } else {
                    info!("❌ [GET_SYMBOL_DIRS] Default dir not found/invalid: {}", dir_path.display());
                }
            }
        }
        
        // Also check for KiCad installation in common macOS locations
        if dirs.is_empty() {
            info!("🔍 [GET_SYMBOL_DIRS] No standard dirs found, checking additional macOS locations...");
            let additional_dirs = [
                "/opt/homebrew/share/kicad/symbols/",
                "/usr/local/share/kicad/symbols/",
                "/Applications/KiCad/KiCad.app/Contents/SharedSupport/template/",
                "/Applications/KiCad/KiCad.app/Contents/SharedSupport/",
                "/Applications/KiCad/KiCad.app/Contents/",
                "/Applications/KiCad/",
                "/opt/kicad/share/kicad/symbols/",
                "/opt/local/share/kicad/symbols/",
            ];
            
            for dir_str in &additional_dirs {
                let dir_path = PathBuf::from(dir_str);
                info!("🔍 [GET_SYMBOL_DIRS] Checking additional dir: {}", dir_path.display());
                if dir_path.exists() && dir_path.is_dir() {
                    info!("✅ [GET_SYMBOL_DIRS] Found valid additional dir: {}", dir_path.display());
                    dirs.push(dir_path);
                    break;
                } else {
                    info!("❌ [GET_SYMBOL_DIRS] Additional dir not found/invalid: {}", dir_path.display());
                }
            }
        }
        
        if dirs.is_empty() {
            warn!("⚠️  [GET_SYMBOL_DIRS] No valid KiCad symbol directories found!");
            warn!("⚠️  [GET_SYMBOL_DIRS] This means the cache cannot be populated with real symbols");
            warn!("⚠️  [GET_SYMBOL_DIRS] The system will rely on embedded fallback symbols");
        } else {
            info!("✅ [GET_SYMBOL_DIRS] Found {} symbol directories:", dirs.len());
            for dir in &dirs {
                info!("✅ [GET_SYMBOL_DIRS]   - {}", dir.display());
            }
        }
        
        dirs
    }
    
    /// Parse symbol ID into library and symbol names
    pub(crate) fn parse_symbol_id(&self, symbol_id: &str) -> Result<(String, String)> {
        let parts: Vec<&str> = symbol_id.split(':').collect();
        if parts.len() != 2 {
            return Err(SymbolCacheError::InvalidSymbolId {
                symbol_id: symbol_id.to_string(),
            });
        }
        
        Ok((parts[0].to_string(), parts[1].to_string()))
    }
}