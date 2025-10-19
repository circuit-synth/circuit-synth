# Template Build System

## Overview

Circuit-synth uses a **single-source template system** to avoid maintaining duplicate copies of the example project template.

### Architecture

```
circuit-synth/
├── example_project/                          # SOURCE OF TRUTH (edit here)
│   ├── .claude/
│   ├── circuit-synth/
│   └── ...
│
├── src/circuit_synth/data/templates/
│   └── example_project/                      # GENERATED (auto-copied during build)
│       └── [same structure as above]
```

**Important:**
- ✅ **Edit only**: `/example_project/` (root level)
- ❌ **Never edit**: `/src/circuit_synth/data/templates/example_project/` (generated)
- 🚫 **Ignored by git**: The packaged template is in `.gitignore`

## Development Workflow

### Making Template Changes

1. **Edit the source template**:
   ```bash
   # Edit files in /example_project/
   vim example_project/circuit-synth/main.py
   ```

2. **The packaged copy is auto-updated**:
   - The `new_project.py` tool uses the root `/example_project/` during development
   - No manual copying needed during development

3. **Commit only the source**:
   ```bash
   git add example_project/
   git commit -m "Update example project template"
   ```

## Building for Distribution

### Before Building Package

Run the build script to copy the template:

```bash
# Copy template from /example_project/ to package data
python build.py
```

This copies:
- Source: `/example_project/`
- Destination: `/src/circuit_synth/data/templates/example_project/`

### Build the Package

```bash
# Build the distribution
uv build
# or
python -m build
```

### Clean Generated Files

```bash
# Remove the packaged template copy
python build.py clean
```

## How It Works

### Development Mode

When running from source (development):
```python
# new_project.py logic:
template_dir = circuit_synth_dir / "data" / "templates" / "example_project"

# Fallback to root (for development):
if not template_dir.exists():
    template_dir = repo_root / "example_project"  # ✅ Uses this
```

### Installed Package Mode

When installed via pip:
```python
# The packaged template is included in the wheel/distribution
template_dir = circuit_synth_dir / "data" / "templates" / "example_project"  # ✅ Uses this
```

## CI/CD Integration

### GitHub Actions Build

Add to build workflow:

```yaml
- name: Copy example project template
  run: python build.py

- name: Build package
  run: uv build

- name: Clean build artifacts
  run: python build.py clean
```

### Pre-commit Hook (Optional)

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Ensure packaged template is in sync (for local testing)
if [ -f build.py ]; then
    python build.py
fi
```

## Advantages

1. **Single source of truth**: Edit only `/example_project/`
2. **No duplication**: One template to maintain
3. **Git cleanliness**: Packaged copy not tracked in git
4. **Fast development**: No manual sync during development
5. **Clean releases**: Template auto-copied during package build

## Troubleshooting

### Template not found during development

**Problem**: `cs-new-project` says template not found

**Solution**: The development fallback should handle this automatically. Check that `/example_project/` exists at repo root.

### Template not found in installed package

**Problem**: Installed package can't find template

**Solution**: Make sure `python build.py` was run before building the distribution package.

### Changes to template not appearing

**Development**: Edit `/example_project/` and restart - changes are immediate
**Distribution**: Re-run `python build.py` then rebuild the package

## Migration Notes

### From Dual-Source System

**Old system** (before this change):
- Edit in two places: `/example_project/` AND `/src/.../example_project/`
- Both tracked in git
- Easy to get out of sync

**New system** (after this change):
- Edit in one place: `/example_project/`
- Packaged copy generated during build
- Cannot get out of sync - single source

## Related Files

- `build.py`: Template copy script
- `.gitignore`: Ignores `src/circuit_synth/data/templates/example_project/`
- `pyproject.toml`: Package data configuration
- `src/circuit_synth/tools/project_management/new_project.py`: Template usage

---

*Last updated: 2025-10-19*
