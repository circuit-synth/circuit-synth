# Quick Release Guide - Circuit Synth

**The exact process that worked on 2025-07-28**

## Prerequisites (One-time Setup)

### 1. PyPI Accounts
- **TestPyPI**: https://test.pypi.org/account/register/
- **Production PyPI**: https://pypi.org/account/register/
- **Enable 2FA** on both accounts

### 2. API Tokens
- **TestPyPI**: Account Settings → API Tokens → Create token
- **Production PyPI**: Account Settings → API Tokens → Create token
- **Save tokens securely** - you'll need them every time

## Release Process (Every Time)

### Step 1: Clean Repository
```bash
# Remove any generated/temporary files
rm -rf dist/ build/ src/*.egg-info/ logs/ example_kicad_project/

# Make sure you're on main branch
git checkout main
git pull origin main
```

### Step 2: Update Version
Edit these files:
- `pyproject.toml` → `version = "0.1.1"`
- `src/circuit_synth/__init__.py` → `__version__ = "0.1.1"`

### Step 3: Run Regression Tests
**ALL must pass before releasing:**
```bash
# 1. Core circuit test
uv run python examples/example_kicad_project.py

# 2. Unit tests
uv run pytest tests/unit/test_core_circuit.py -v

# 3. Build test
uv run python -m build
uv run python -m twine check dist/*
```

### Step 4: Build Package
```bash
# Clean previous builds
rm -rf dist/ build/ src/*.egg-info/

# Build package
uv run python -m build

# Verify build contents
tar -tzf dist/circuit_synth-*.tar.gz | grep -E "\.(py|md)$" | head -20
uv run python -m twine check dist/*
```

**Expected output**: Should see all your Python modules listed, and "PASSED" for twine check.

### Step 5: Test Upload to TestPyPI
```bash
# Upload to TestPyPI first (safer)
uv run python -m twine upload --repository testpypi dist/*

# When prompted:
# Username: __token__
# Password: [paste your TestPyPI token]
```

**Expected output**: 
```
View at: https://test.pypi.org/project/circuit-synth/X.X.X/
```

### Step 6: Test Installation
```bash
# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --no-deps circuit-synth

# Test import
python -c "import circuit_synth; print(f'✅ Version: {circuit_synth.__version__}')"

# Clean up test install
pip uninstall circuit-synth
```

### Step 7: Upload to Production PyPI
```bash
# Upload to production PyPI
uv run python -m twine upload dist/*

# When prompted:
# Username: __token__
# Password: [paste your production PyPI token]
```

**Expected output**: 
```
View at: https://pypi.org/project/circuit-synth/X.X.X/
```

### Step 8: Tag and Commit
```bash
# Commit version changes
git add pyproject.toml src/circuit_synth/__init__.py
git commit -m "Release v0.1.1

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Tag the release  
git tag v0.1.1
git push origin main
git push origin v0.1.1
```

### Step 9: Verify Public Installation
```bash
# Test public installation
pip install circuit-synth

# Test functionality
python -c "import circuit_synth; print('✅ Public release working!')"
```

## Troubleshooting

### Authentication Issues (403 Forbidden)
If you get "Invalid authentication information":

1. **Double-check token**: Make sure you're using the right token (TestPyPI vs PyPI)
2. **Token format**: Should start with `pypi-`
3. **Username**: Always use `__token__` (with underscores)
4. **Copy exactly**: No extra spaces when copying token

### Package Build Issues
If the package is missing files:
1. **Check `pyproject.toml`**: Make sure `[tool.setuptools.packages.find]` section exists
2. **Verify structure**: Run `tar -tzf dist/*.tar.gz | head -30` to see what's included
3. **Clean rebuild**: Always `rm -rf dist/ build/ src/*.egg-info/` before building

### Missing Dependencies in TestPyPI
TestPyPI doesn't have all dependencies. Use `--no-deps` flag:
```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps circuit-synth
```

## Files That Must Be Updated Each Release

1. `pyproject.toml` - version number
2. `src/circuit_synth/__init__.py` - `__version__` 
3. `CHANGELOG.md` - add new version entry (if exists)

## Quick Checklist

- [ ] Clean repository of temporary files
- [ ] Update version in both files
- [ ] All regression tests pass
- [ ] Package builds without errors
- [ ] twine check passes
- [ ] TestPyPI upload successful
- [ ] Test installation from TestPyPI works
- [ ] Production PyPI upload successful
- [ ] Git tag and push completed
- [ ] Public installation verified

## Emergency Rollback

**If you upload a broken version:**
1. **You cannot delete from PyPI** - only hide
2. **Increment patch version** (e.g., 0.1.1 → 0.1.2)
3. **Fix the issue and release immediately**
4. **Document in release notes**

## Success Criteria

A release is successful when:
- ✅ Package installs with: `pip install circuit-synth`
- ✅ Basic import works: `import circuit_synth`
- ✅ Core functionality: `from circuit_synth import Circuit, Component, Net`
- ✅ Version correct: `circuit_synth.__version__`

---

**Last Tested**: 2025-07-28  
**Status**: ✅ Working process
**Next Release**: Update version numbers and follow this guide exactly