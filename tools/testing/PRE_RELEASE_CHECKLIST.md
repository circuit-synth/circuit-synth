
# PyPI Release Pre-Flight Checklist

## Before Building Package

  ```bash
  ```

  ```bash  
  ```

## After Building Package

- [ ] Run PyPI package test
  ```bash
  python tools/testing/test_pypi_package.py
  ```

- [ ] Version numbers updated consistently
  - [ ] pyproject.toml version
  - [ ] src/circuit_synth/__init__.py version

- [ ] Package size reasonable (< 100MB)
  ```bash
  ls -lah dist/*.whl
  ```

## Final Checks

- [ ] All tests pass in clean environment
- [ ] No hardcoded development paths in imports
- [ ] Basic circuit generation works

## Release

- [ ] Upload to PyPI
  ```bash
  uv run python -m twine upload dist/*
  ```

- [ ] Test installation from PyPI
  ```bash
  pip install circuit-synth==NEW_VERSION
  python -c "import circuit_synth; circuit_synth.Circuit('test')"
  ```
