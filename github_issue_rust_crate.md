# GitHub Issue: Extract Rust KiCad Module into Standalone Repository

## Title
Extract Rust KiCad integration as standalone crate for crates.io

## Description

### Overview
The Rust KiCad schematic manipulation module currently in `rust_modules/rust_kicad_integration/` has grown into a robust, general-purpose library that would benefit the wider community. It should be extracted into its own repository and published to crates.io.

### Current Features
- ✅ Create and manipulate KiCad schematic files (.kicad_sch)
- ✅ Add/remove/update components programmatically  
- ✅ Handle extended symbols (inheritance)
- ✅ Support multi-unit components (op-amps, MCUs)
- ✅ Parse and generate S-expressions
- ✅ Python bindings via PyO3/maturin
- ✅ Hierarchical label support
- ✅ Component removal

### Benefits of Extraction
1. **Wider adoption** - Other projects can use it without circuit-synth dependency
2. **Focused development** - Can evolve independently with its own versioning
3. **Community contributions** - Easier for others to contribute KiCad features
4. **Cleaner architecture** - Clear separation between generic KiCad tools and circuit-synth

### Tasks

#### Phase 1: Repository Setup
- [ ] Create new repository: `circuit-synth/kicad-rust`
- [ ] Move code from `rust_modules/rust_kicad_integration/`
- [ ] Set up CI/CD (GitHub Actions)
- [ ] Add comprehensive README with examples
- [ ] Add LICENSE file (MIT/Apache-2.0 dual license)
- [ ] Create CONTRIBUTING.md

#### Phase 2: Crate Preparation
- [ ] Choose crate name (suggest: `kicad` or `kicad-schematic`)
- [ ] Update Cargo.toml with proper metadata:
  - Description
  - Homepage
  - Repository URL
  - Keywords: ["kicad", "eda", "schematic", "pcb", "electronics"]
  - Categories: ["hardware-support", "parsing", "science"]
- [ ] Add crate-level documentation
- [ ] Create examples/ directory with usage examples
- [ ] Add integration tests

#### Phase 3: Publishing
- [ ] Register crate name on crates.io
- [ ] Publish initial version (0.1.0)
- [ ] Set up automated releases via GitHub Actions
- [ ] Create GitHub releases with changelogs
- [ ] Add crates.io and docs.rs badges to README

#### Phase 4: Python Package
- [ ] Publish Python wheels to PyPI
- [ ] Set up manylinux builds for compatibility
- [ ] Document Python installation and usage
- [ ] Add to circuit-synth as optional dependency

#### Phase 5: Circuit-Synth Integration
- [ ] Update circuit-synth to use published crate
- [ ] Modify `src/circuit_synth/kicad/rust_integration.py` to use PyPI package
- [ ] Update installation docs
- [ ] Add migration guide for existing users

### Proposed Crate Structure
```
kicad-rust/
├── Cargo.toml
├── README.md
├── LICENSE-MIT
├── LICENSE-APACHE
├── CONTRIBUTING.md
├── src/
│   ├── lib.rs                    # Main library entry
│   ├── schematic_editor.rs       # Schematic manipulation
│   ├── s_expression.rs           # S-expression parser
│   ├── kicad_library.rs         # Library symbol loading
│   ├── types.rs                  # Common types
│   └── python_bindings.rs       # PyO3 bindings
├── examples/
│   ├── create_schematic.rs      # Rust example
│   └── python_example.py        # Python example
├── tests/
│   └── integration_tests.rs     # Integration tests
└── .github/
    └── workflows/
        ├── ci.yml               # Test & lint
        └── release.yml          # Publish to crates.io

```

### API Stability Commitment
Before 1.0 release:
- May have breaking changes between minor versions
- Will follow semantic versioning after 1.0
- Python API will remain stable where possible

### Success Metrics
- [ ] Published on crates.io
- [ ] Published on PyPI  
- [ ] Used by at least one external project
- [ ] Circuit-synth successfully using published version
- [ ] Documentation on docs.rs

### References
- Current code: `rust_modules/rust_kicad_integration/`
- Integration layer: `src/circuit_synth/kicad/rust_integration.py`
- Test results show it handles complex KiCad symbols correctly

### Labels
`enhancement`, `refactoring`, `rust`, `packaging`

### Assignees
@shanemattner

### Milestone
v0.6.0