# Development Tools Reference Guide

✅ **COMPLETED**: All development tools have been moved to the organized `tools/` directory.

## 🏗️ **New Organization Structure**

All development tools are now organized in the `tools/` directory:

```
tools/
├── testing/           # Test automation
│   ├── run_full_regression_tests.py
│   ├── run_regression_tests.py
│   └── test_release.py
├── build/             # Build and formatting
│   ├── format_all.sh
│   └── setup_formatting.sh
├── release/           # Release automation
│   └── release_to_pypi.sh
├── maintenance/       # Utilities
│   └── clear_all_caches.sh
└── analysis/          # Code analysis
    ├── dead-code-analysis.py
    └── dead-code-analysis.sh
```

## 📖 **Quick Reference Commands**

```bash
# Most commonly used tools:
./tools/testing/run_full_regression_tests.py  # Comprehensive pre-release tests
./tools/build/format_all.sh                   # Format all code
./tools/maintenance/clear_all_caches.sh       # Clear caches
./tools/release/release_to_pypi.sh             # Release to PyPI
```

## 🔍 **Finding Tools**

```bash
# List all tools by category
ls tools/*/

# Find specific tool
find tools/ -name "*regression*"

# Search tool content  
grep -r "function_name" tools/
```

## ✅ **Migration Complete**

The old `scripts/` directory has been removed. Use these new paths:

**Updated paths:**
- ~~`./scripts/run_all_tests.sh`~~ → `./tools/testing/run_full_regression_tests.py`
- ~~`./scripts/clear_all_caches.sh`~~ → `./tools/maintenance/clear_all_caches.sh`
- ~~`./scripts/format_all.sh`~~ → `./tools/build/format_all.sh`
- ~~`./scripts/release_to_pypi.sh`~~ → `./tools/release/release_to_pypi.sh`

## 📚 **Related Documentation**

- **Testing**: `docs/TESTING.md` - Comprehensive testing guide
- **Contributing**: `docs/CONTRIBUTING.md` - Development guidelines  
- **Claude instructions**: `CLAUDE.md` - Claude Code guidance

---

**💡 Tip**: Use the organized `tools/` structure for clearer development workflows!