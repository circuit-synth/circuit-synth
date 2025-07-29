//! Debug utilities for enhanced logging in PyO3 context
//!
//! This module provides additional debugging tools that work reliably
//! when Rust code is called from Python via PyO3 bindings.

use std::io::{self, Write};

/// Enhanced debug macro that ensures output visibility
#[macro_export]
macro_rules! debug_print {
    ($($arg:tt)*) => {
        println!($($arg)*);
        let _ = std::io::stdout().flush();
    };
}

/// Enhanced error macro using stderr
#[macro_export]
macro_rules! debug_error {
    ($($arg:tt)*) => {
        eprintln!("❌ ERROR: {}", format!($($arg)*));
        let _ = std::io::stderr().flush();
    };
}

/// Enhanced info macro
#[macro_export]
macro_rules! debug_info {
    ($($arg:tt)*) => {
        println!("ℹ️  INFO: {}", format!($($arg)*));
        let _ = std::io::stdout().flush();
    };
}

/// Enhanced warning macro
#[macro_export]
macro_rules! debug_warn {
    ($($arg:tt)*) => {
        eprintln!("⚠️  WARN: {}", format!($($arg)*));
        let _ = std::io::stderr().flush();
    };
}

/// Enhanced success macro
#[macro_export]
macro_rules! debug_success {
    ($($arg:tt)*) => {
        println!("✅ SUCCESS: {}", format!($($arg)*));
        let _ = std::io::stdout().flush();
    };
}

/// Debug section separator
#[macro_export]
macro_rules! debug_section {
    ($title:expr) => {
        println!("🔧 [{}] {}", $title, "=".repeat(40));
        let _ = std::io::stdout().flush();
    };
}

/// Debug subsection
#[macro_export]
macro_rules! debug_step {
    ($step:expr, $msg:expr) => {
        println!("🔧 [{}] {}", $step, $msg);
        let _ = std::io::stdout().flush();
    };
}

/// Conditional debug print (only in debug builds)
#[macro_export]
macro_rules! debug_only {
    ($($arg:tt)*) => {
        #[cfg(debug_assertions)]
        {
            println!($($arg)*);
            let _ = std::io::stdout().flush();
        }
    };
}

/// Performance timing debug utility
pub struct DebugTimer {
    name: String,
    start: std::time::Instant,
}

impl DebugTimer {
    pub fn new(name: &str) -> Self {
        println!("⏱️  TIMER START: {}", name);
        let _ = io::stdout().flush();
        Self {
            name: name.to_string(),
            start: std::time::Instant::now(),
        }
    }

    pub fn checkpoint(&self, checkpoint_name: &str) {
        let elapsed = self.start.elapsed();
        println!(
            "⏱️  TIMER {}: {} - {:?}",
            self.name, checkpoint_name, elapsed
        );
        let _ = io::stdout().flush();
    }
}

impl Drop for DebugTimer {
    fn drop(&mut self) {
        let elapsed = self.start.elapsed();
        println!("⏱️  TIMER END: {} - Total: {:?}", self.name, elapsed);
        let _ = io::stdout().flush();
    }
}

/// Initialize logging for Python context
pub fn init_python_logging() {
    // Set up environment logger if available
    if std::env::var("RUST_LOG").is_err() {
        std::env::set_var("RUST_LOG", "debug");
    }

    // Try to initialize env_logger (will fail silently if already initialized)
    let _ = env_logger::try_init();

    debug_info!("Rust debug logging initialized for Python context");
}

/// Test all debug macros
pub fn test_debug_output() {
    debug_section!("DEBUG_TEST");
    debug_info!("Testing debug output visibility");
    debug_success!("println! statements work in PyO3");
    debug_warn!("This is a warning message");
    debug_error!("This is an error message (non-fatal)");
    debug_step!("STEP_1", "Testing step logging");
    debug_only!("This only shows in debug builds");

    let _timer = DebugTimer::new("test_operation");
    std::thread::sleep(std::time::Duration::from_millis(10));

    println!("🔧 [DEBUG_TEST] All debug utilities tested successfully");
    let _ = io::stdout().flush();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_debug_macros() {
        debug_print!("Test debug print");
        debug_info!("Test info");
        debug_success!("Test success");
        debug_warn!("Test warning");
        debug_error!("Test error");
    }

    #[test]
    fn test_debug_timer() {
        let timer = DebugTimer::new("test");
        timer.checkpoint("middle");
        std::thread::sleep(std::time::Duration::from_millis(1));
        // Timer will print on drop
    }
}
