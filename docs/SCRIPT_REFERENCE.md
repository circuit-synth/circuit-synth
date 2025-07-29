# Script Reference Guide

This document lists all scripts in the `scripts/` directory and their purposes.

## 🔧 **Build & Setup Scripts**

### Rust Integration
- **`scripts/rebuild_all_rust.sh`** - Rebuilds all Rust modules from scratch
- **`scripts/enable_rust_acceleration.py`** - Enables Rust acceleration for performance
- **`scripts/setup_integrated_rust.py`** - Sets up integrated Rust environment

### KiCad Symbol Management  
- **`scripts/download-kicad-symbols.sh`** - Downloads KiCad symbol libraries
- **`scripts/extract-test-symbols.sh`** - Extracts symbols for testing
- **`scripts/setup-ci-symbols.sh`** - Sets up symbols for CI environment

## 🧪 **Testing Scripts**

### Automated Testing
- **`scripts/run_all_tests.sh`** - Comprehensive test runner (Python + Rust + Integration)
- **`scripts/test_rust_modules.sh`** - Automated Rust module testing with JSON output

### Development Tools
- **`scripts/defensive_baseline.py`** - Baseline defensive programming checks
- **`scripts/investigate_nondeterminism.py`** - Debugging nondeterministic behavior

## 🐳 **Docker & Deployment**

- **`scripts/circuit-synth-docker`** - Docker container management
- **`scripts/deploy-production.sh`** - Production deployment script
- **`scripts/docker-kicad-modern.sh`** - Modern KiCad Docker setup
- **`scripts/docker-kicad-test.sh`** - KiCad testing environment
- **`scripts/run-with-kicad.sh`** - Run with KiCad integration

## 📖 **Quick Reference Commands**

```bash
# Most commonly used scripts:
./scripts/run_all_tests.sh                    # Run comprehensive tests
./scripts/test_rust_modules.sh               # Test only Rust modules
./scripts/rebuild_all_rust.sh                # Rebuild all Rust modules
./scripts/download-kicad-symbols.sh          # Download KiCad symbols
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