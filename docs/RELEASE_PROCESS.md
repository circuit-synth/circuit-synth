# Circuit-Synth Release Process

This document describes the comprehensive release process for circuit-synth to ensure packages work correctly before releasing to PyPI.

## 🚀 Release Checklist

### Pre-Release Testing

1. **Run Local Tests**
   ```bash
   # Run comprehensive test suite
   ./tools/testing/test_release.py 0.8.4
   
   # Or use make command
   make test-release VERSION=0.8.4
   ```

2. **Test on TestPyPI First**
   ```bash
   # Build distribution
   uv build
   
   # Upload to TestPyPI
   uv run twine upload --repository testpypi dist/*
   
   # Test installation from TestPyPI
   pip install --index-url https://test.pypi.org/simple/ \
               --extra-index-url https://pypi.org/simple/ \
               circuit-synth==0.8.4
   ```

3. **Run GitHub Actions Tests**
   - Trigger the "Test Release Package" workflow manually
   - Wait for all matrix tests to pass (Linux, macOS, Windows × Python 3.10, 3.11, 3.12)
   - Verify Docker container tests pass
   - Check TestPyPI upload and installation works

### Release Steps

1. **Update Version**
   ```bash
   # Update version in pyproject.toml
   # Update version in src/circuit_synth/__init__.py
   ```

2. **Create PR from develop to main**
   ```bash
   gh pr create --base main --head develop \
     --title "Release v0.8.4" \
     --body "Release notes..."
   ```

3. **After PR Merge, Tag Release**
   ```bash
   git checkout main
   git pull origin main
   git tag -a v0.8.4 -m "Release v0.8.4: Description"
   git push origin v0.8.4
   ```

4. **Build Final Distribution**
   ```bash
   # Clean old builds
   rm -rf dist/
   
   uv build
   ```

5. **Final Test Before PyPI**
   ```bash
   # Test the exact wheel that will be uploaded
   python -m venv final_test
   source final_test/bin/activate
   pip install dist/circuit_synth-0.8.4-py3-none-any.whl
   deactivate
   ```

6. **Upload to PyPI**
   ```bash
   uv run twine upload dist/*
   ```

7. **Create GitHub Release**
   ```bash
   gh release create v0.8.4 \
     --title "v0.8.4: Release Title" \
     --notes "Release notes..." \
     dist/*
   ```

## 🧪 Testing Infrastructure

### Local Testing Tools

- **`test_release.py`**: Comprehensive release testing script
  - Tests in isolated virtual environments
  - Tests multiple Python versions
  - Tests Docker containers
  - Tests actual circuit functionality

- **`test_pypi_package.py`**: Quick PyPI package test
  - Tests installation in clean environment
  - Validates imports work

### GitHub Actions Workflows

- **`test-release.yml`**: Automated release testing
  - Matrix testing (OS × Python version)
  - Docker container testing
  - TestPyPI upload and installation test
  - Comprehensive test suite execution

### TestPyPI Configuration

1. **Create TestPyPI Account**
   - Register at https://test.pypi.org/account/register/
   - Verify email address

2. **Configure `.pypirc`**
   ```ini
   [distutils]
   index-servers =
       pypi
       testpypi

   [pypi]
   username = __token__
   password = pypi-...your-token...

   [testpypi]
   repository = https://test.pypi.org/legacy/
   username = __token__
   password = pypi-...your-test-token...
   ```

3. **Set GitHub Secrets**
   - `TEST_PYPI_API_TOKEN`: Your TestPyPI API token
   - `PYPI_API_TOKEN`: Your PyPI API token



   ```bash
   ```

2. **Verify compiled binaries are in place**
   ```bash
   ```

   ```bash
   python -c "
   "
   ```


1. **Import path mismatches**: Ensure import logic handles both development and PyPI environments
2. **Binary naming**: Compiled binaries must match Python's expected module names
3. **Missing binaries**: Ensure all `.so`/`.dylib`/`.pyd` files are included in the wheel

## 🐳 Docker Testing

### Local Docker Test
```bash
cat > Dockerfile.test <<EOF
FROM python:3.12-slim
WORKDIR /test
COPY dist/*.whl /test/
RUN pip install /test/*.whl
RUN python -c "import circuit_synth; print('✅ Docker test passed!')"
EOF

docker build -f Dockerfile.test -t circuit-synth-test .
docker run --rm circuit-synth-test
```

### Multi-Version Docker Test
```bash
for version in 3.10 3.11 3.12; do
  docker run --rm -v $(pwd)/dist:/dist python:$version-slim \
    sh -c "pip install /dist/*.whl && python -c 'import circuit_synth'"
done
```

## 📊 Test Matrix

Ensure all combinations pass before release:

| Platform | Python 3.10 | Python 3.11 | Python 3.12 |
|----------|-------------|-------------|-------------|
| Linux    | ✅          | ✅          | ✅          |
| macOS    | ✅          | ✅          | ✅          |
| Windows  | ✅          | ✅          | ✅          |
| Docker   | ✅          | ✅          | ✅          |

## 🔍 Debugging Failed Releases

### If users report import errors after release:

1. **Test exact user scenario**
   ```bash
   # Create clean environment
   python -m venv debug_env
   source debug_env/bin/activate
   
   # Install exact version from PyPI
   pip install circuit-synth==0.8.4
   
   # Test imports with verbose output
   python -v -c "import circuit_synth"
   ```

2. **Check wheel contents**
   ```bash
   # Download wheel from PyPI
   pip download circuit-synth==0.8.4 --no-deps
   
   # Inspect contents
   unzip -l circuit_synth-0.8.4-py3-none-any.whl | grep -E "\.(so|dylib|pyd)$"
   ```

3. **Test on different platforms**
   - Use GitHub Codespaces for Linux testing
   - Use macOS/Windows VMs or CI for platform-specific issues

## 🚨 Emergency Rollback

If a bad release is published:

1. **Yank the release on PyPI** (doesn't delete but prevents new installs)
   ```bash
   pip install --upgrade twine
   twine yank circuit-synth --version 0.8.4
   ```

2. **Fix the issue**
3. **Release a patch version** (e.g., 0.8.5)
4. **Communicate to users** via GitHub issues/discussions

## 📝 Post-Release

1. **Verify on PyPI**
   ```bash
   pip install circuit-synth==$(cat pyproject.toml | grep version | cut -d'"' -f2)
   ```

2. **Update documentation**
   - Update README with new version
   - Update CHANGELOG
   - Create GitHub discussion for release announcement

3. **Monitor for issues**
   - Watch GitHub issues for installation problems
   - Check PyPI download stats
   - Monitor CI/CD for any post-release failures