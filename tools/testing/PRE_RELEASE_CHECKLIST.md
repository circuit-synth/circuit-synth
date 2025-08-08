
# PyPI Release Pre-Flight Checklist

## Before Building Package

- [ ] All Rust modules built successfully
  ```bash
  ./tools/build/build_rust_modules.sh
  ```

- [ ] Rust modules are functional
  ```bash  
  python -c "import rust_kicad_integration; print('✅ rust_kicad_integration works')"
  python -c "import rust_core_circuit_engine; print('✅ rust_core_circuit_engine works')"
  python -c "import rust_force_directed_placement; print('✅ rust_force_directed_placement works')"
  python -c "import rust_netlist_processor; print('✅ rust_netlist_processor works')"
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
- [ ] Rust modules included in wheel
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
