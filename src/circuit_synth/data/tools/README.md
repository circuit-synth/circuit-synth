# Circuit-Synth Tools

This directory contains utility tools and scripts for circuit-synth development, testing, and deployment.

## 📁 Directory Structure

### `ci-setup/`
**Continuous Integration Setup Tools**
- `setup-ci-symbols.sh` - Cross-platform bash script for KiCad symbol setup
- `setup_ci_symbols.py` - Python alternative for environments without bash
- `download-kicad-symbols.sh` - Basic symbol download script
- `extract-test-symbols.sh` - Symbol extraction utilities
- `CI_SETUP.md` - Complete CI setup documentation

**Usage**:
```bash
# From repository root
./tools/ci-setup/setup-ci-symbols.sh
```

### `development/` *(Future)*
**Development and Debugging Tools**
- Symbol validation scripts
- Performance benchmarking tools
- Development environment setup

### `deployment/` *(Future)*
**Deployment and Distribution Tools**
- Package building scripts
- Release automation tools
- Distribution utilities

## 🚀 Quick Reference

### CI Setup
```bash
# Cross-platform KiCad symbol setup for CI
./tools/ci-setup/setup-ci-symbols.sh

# Python alternative
python3 tools/ci-setup/setup_ci_symbols.py
```

### Integration with Existing Scripts
The `scripts/` directory in the repository root contains runtime scripts that are part of the installed package:
- `scripts/circuit-synth-docker` - Docker integration
- `scripts/deploy-production.sh` - Production deployment
- `scripts/run-with-kicad.sh` - KiCad environment setup

The `tools/` directory contains **development and CI tools** that are not part of the installed package but help with development workflows.

## 📋 Tool Categories

| Category | Location | Purpose |
|----------|----------|---------|
| **CI Setup** | `tools/ci-setup/` | KiCad symbols, test environment setup |
| **Runtime Scripts** | `scripts/` | Part of installed package, runtime utilities |
| **Docker Tools** | `docker/` | Container management and deployment |
| **Examples** | `examples/` | Usage examples and demos |
| **Documentation** | `docs/` | API docs, guides, and references |

This organization keeps development tools separate from runtime components while maintaining clear, logical groupings.