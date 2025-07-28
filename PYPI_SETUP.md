# PyPI Package Registration and Publishing Guide

## Overview

This guide covers the complete process for registering and publishing the `circuit-synth` package to PyPI (Python Package Index), following the official [Python Packaging Authority](https://packaging.python.org/) guidelines and best practices.

## Prerequisites

### 1. Account Setup

**Create PyPI accounts**:
- **Production PyPI**: https://pypi.org/account/register/
- **TestPyPI** (for testing): https://test.pypi.org/account/register/

**Enable 2FA** (highly recommended):
- Both accounts should have two-factor authentication enabled
- Required for API token generation

### 2. Package Name Verification

**Check availability**:
```bash
# Visit to check if name is available
https://pypi.org/project/circuit-synth/

# Should return "404 Not Found" if available
```

**Current package name**: `circuit_synth`
- **Import name**: `circuit_synth` (Python import)
- **Package name**: `circuit_synth` (pip install name)
- **Display name**: "circuit-synth" (can use hyphens in display)

## Publishing Setup

### 1. Install Publishing Tools

**Modern Python Packaging (recommended)**:
```bash
# Install build tools (official Python.org recommendation)
python -m pip install --upgrade build twine

# Using uv (alternative)
uv add --group dev twine build

# Verify installation
python -m build --help
python -m twine --help
```

**Reference**: [Python Packaging Tutorial](https://packaging.python.org/en/latest/tutorials/packaging-projects/)

### 2. Configure Authentication

**Option A: API Tokens (Recommended)**

1. **Generate tokens**:
   - PyPI: Account Settings → API Tokens → "Add API Token"
   - TestPyPI: Same process for testing

2. **Configure twine**:
```bash
# Create ~/.pypirc file
cat > ~/.pypirc << EOF
[distutils]
index-servers = 
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-testpypi-token-here
EOF

# Secure the file
chmod 600 ~/.pypirc
```

**Option B: Environment Variables**
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-api-token-here
```

### 3. Package Configuration Updates

**Update `pyproject.toml`** for better PyPI integration:

```toml
[project]
name = "circuit_synth"
version = "0.1.0"
description = "Pythonic circuit design for production-ready KiCad projects"
readme = {file = "README.md", content-type = "text/markdown"}
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "Circuit Synth Contributors", email = "contact@circuitsynth.com"},
]
keywords = ["circuit", "design", "kicad", "electronics", "pcb", "schematic", "eda"]
classifiers = [
    "Development Status :: 4 - Beta",  # Updated from Alpha
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    "Operating System :: OS Independent",
]

[project.urls]
Homepage = "https://github.com/shanemattner/circuit-synth"
Documentation = "https://circuit-synth.readthedocs.io"
Repository = "https://github.com/shanemattner/circuit-synth"
Issues = "https://github.com/shanemattner/circuit-synth/issues"
Changelog = "https://github.com/shanemattner/circuit-synth/blob/main/CHANGELOG.md"
```

## Publishing Process

### 1. Pre-Publishing Checklist

**Code Quality**:
- [ ] All regression tests pass
- [ ] Code formatted with black/isort
- [ ] No lint errors (flake8)
- [ ] Type checking passes (mypy)
- [ ] Version number updated in `pyproject.toml`

**Documentation**:
- [ ] README.md is current and comprehensive
- [ ] CHANGELOG.md includes release notes
- [ ] Examples work and are tested
- [ ] License file exists and is correct

**Package Structure**:
- [ ] No debug/temporary files included
- [ ] `.gitignore` excludes build artifacts
- [ ] `src/circuit_synth/__init__.py` has correct version

### 2. Build Package

**Official Python packaging process**:
```bash
# Clean previous builds
rm -rf dist/ build/ src/*.egg-info/

# Build package (official method)
python -m build

# Alternative using uv
uv build

# Verify build contents
tar -tzf dist/circuit_synth-*.tar.gz | head -20
unzip -l dist/circuit_synth-*.whl | head -20

# Check package metadata
python -m twine check dist/*
```

**Build outputs**:
- `dist/circuit_synth-*.tar.gz` - Source distribution (sdist)
- `dist/circuit_synth-*.whl` - Built distribution (wheel)

**Reference**: [Building and Uploading](https://packaging.python.org/en/latest/tutorials/packaging-projects/#generating-distribution-archives)

### 3. Test Upload (TestPyPI)

**Official testing process**:
```bash
# Upload to TestPyPI first (recommended)
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps circuit-synth

# Test basic functionality
python -c "import circuit_synth; print(circuit_synth.__version__)"

# Clean up test installation
python -m pip uninstall circuit-synth
```

### 4. Production Upload

**Final publishing process**:
```bash
# Upload to production PyPI
python -m twine upload dist/*

# Verify upload success
# Visit: https://pypi.org/project/circuit-synth/

# Test installation from PyPI
python -m pip install circuit-synth

# Verify functionality
python -c "import circuit_synth; print('Install successful!')"
```

**References**: 
- [Uploading to TestPyPI](https://packaging.python.org/en/latest/tutorials/packaging-projects/#uploading-the-distribution-archives)
- [Publishing Package Distribution Releases](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)

## Version Management

### Semantic Versioning

**Format**: `MAJOR.MINOR.PATCH`

**Current Version**: `0.1.0`
- **0.x.x**: Pre-1.0 development releases
- **1.0.0**: First stable release
- **1.1.0**: New features, backward compatible
- **1.0.1**: Bug fixes, backward compatible
- **2.0.0**: Breaking changes

### Release Schedule

**Planned Releases**:
- `0.1.0`: Initial PyPI release with current functionality
- `0.2.0`: Enhanced placement algorithms
- `0.3.0`: Improved KiCad integration
- `1.0.0`: First stable release

### Version Update Process

```bash
# Update version in multiple places
# 1. pyproject.toml
version = "0.1.1"

# 2. src/circuit_synth/__init__.py
__version__ = "0.1.1"

# 3. CHANGELOG.md
## [0.1.1] - 2025-07-28
### Fixed
- Bug fix description

# 4. Git tag
git tag v0.1.1
git push origin v0.1.1
```

## Automated Publishing (Future)

### GitHub Actions Integration

**Setup for future automation**:

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

### Security Considerations

**API Token Security**:
- Store tokens as GitHub Secrets
- Use scoped tokens (package-specific)
- Rotate tokens regularly
- Never commit tokens to repository

**Package Security**:
- Enable PyPI 2FA
- Use trusted publishing when available
- Monitor package for unauthorized uploads
- Keep dependencies updated

## Maintenance

### Post-Publication Tasks

**After each release**:
- [ ] Verify package installs correctly
- [ ] Test import and basic functionality
- [ ] Update documentation sites
- [ ] Announce release (if applicable)
- [ ] Monitor for issues or bug reports

### Package Statistics

**Monitor package health**:
- Download statistics: https://pypistats.org/packages/circuit-synth
- PyPI project page: https://pypi.org/project/circuit-synth/
- Security advisories: Check GitHub security tab

### Support and Issues

**User Support**:
- GitHub Issues for bug reports
- Discussions for questions and help
- Documentation for common use cases
- Examples and tutorials

## Troubleshooting

### Common Publishing Issues

**Upload failures**:
```bash
# Check package format (official method)
python -m twine check dist/*

# Verbose upload for debugging
python -m twine upload --verbose dist/*

# Alternative repository specification
python -m twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
```

**Authentication issues (403 Forbidden)**:
**COMMON ISSUE**: "Invalid or non-existent authentication information"

**Solution that works**:
1. **Double-check your token**: Make sure it's the TestPyPI token (not production)
2. **Username**: Always use `__token__` (with two underscores)
3. **Token format**: Should start with `pypi-`
4. **Copy exactly**: No extra spaces when pasting

**If still failing**, try verbose mode:
```bash
uv run python -m twine upload --repository testpypi --verbose dist/*
```

**Authentication workflow that worked**:
```bash
# Interactive prompt (what we used successfully)
uv run python -m twine upload --repository testpypi dist/*
# Username: __token__
# Password: [paste TestPyPI token]
```

**Package conflicts**:
- Ensure version is unique
- Check for naming conflicts
- Verify package contents

### Recovery Procedures

**If bad release uploaded**:
1. **Cannot delete PyPI releases** - only hide them
2. **Upload fixed version** with incremented version number
3. **Document issues** in CHANGELOG.md
4. **Communicate** to users via GitHub releases

**Version conflicts**:
- Increment patch version for fixes
- Use post-release versions if needed (e.g., `1.0.0.post1`)

## Additional Resources

### Official Python Packaging Documentation
- [Python Packaging User Guide](https://packaging.python.org/)
- [Packaging Projects Tutorial](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [Building and Publishing](https://packaging.python.org/en/latest/guides/section-build-and-publish/)
- [Using TestPyPI](https://packaging.python.org/en/latest/guides/using-testpypi/)
- [Publishing with GitHub Actions](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)

### Tools Documentation
- [Build Documentation](https://build.pypa.io/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [PyPI Help](https://pypi.org/help/)

---

**Document Version**: 1.1  
**Last Updated**: 2025-07-28  
**Status**: Updated with official Python.org guidelines  
**Reference**: [Python Packaging Authority](https://packaging.python.org/)