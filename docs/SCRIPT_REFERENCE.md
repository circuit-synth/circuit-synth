# Script Reference Guide

This document lists all scripts in the `scripts/` directory and their purposes.

## 🧪 **Testing Scripts**

### Automated Testing
- **`scripts/run_all_tests.sh`** - Comprehensive test runner (Python + Rust + Integration)
- **`scripts/test_rust_modules.sh`** - Automated Rust module testing with JSON output

## 🔧 **Build & Setup Scripts**

### Rust Integration
- **`scripts/rebuild_all_rust.sh`** - Rebuilds all Rust modules from scratch
- **`scripts/enable_rust_acceleration.py`** - Enables Rust acceleration for performance

### Code Formatting
- **`scripts/format_all.sh`** - Formats all Python and Rust code
- **`scripts/setup_formatting.sh`** - Sets up pre-commit hooks for automatic formatting

## 🛠️ **Maintenance & Utilities**

- **`scripts/clear_all_caches.sh`** - Clears all circuit-synth caches for fresh testing

## 📖 **Quick Reference Commands**

```bash
# Most commonly used scripts:
./scripts/run_all_tests.sh                    # Run comprehensive tests
./scripts/test_rust_modules.sh               # Test only Rust modules
./scripts/rebuild_all_rust.sh                # Rebuild all Rust modules
./scripts/format_all.sh                      # Format all code
./scripts/clear_all_caches.sh                # Clear caches
./scripts/enable_rust_acceleration.py        # Enable Rust performance
```

## 🔍 **Finding Scripts**

All scripts are now located in the `scripts/` directory. Use these commands to explore:

```bash
# List all scripts
ls scripts/

# Find specific script
find scripts/ -name "*rust*"

# Search script content  
grep -r "function_name" scripts/
```

## 📚 **Related Documentation**

- **Main docs**: `docs/AUTOMATED_TESTING.md` - Comprehensive testing guide
- **Rust docs**: `docs/RUST_TESTING_GUIDE.md` - Rust-specific testing
- **Integration**: `docs/RUST_PYPI_INTEGRATION.md` - Python-Rust integration
- **Contributing**: `CONTRIBUTING.md` - Development guidelines
- **Claude instructions**: `CLAUDE.md` - Claude Code guidance

---

**💡 Tip**: Bookmark this file! All your utility scripts are now organized in `scripts/` with this reference guide.