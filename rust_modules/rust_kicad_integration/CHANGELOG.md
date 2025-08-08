# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive integration tests for all major functionality
- Benchmark suite for performance testing
- Example programs demonstrating library usage
- GitHub Actions CI/CD pipeline
- Complete Cargo.toml metadata for crate publishing
- Optional Python feature flag for conditional compilation

### Changed
- Improved project structure with proper separation of concerns
- Enhanced documentation with rustdoc comments
- Made Python bindings optional via feature flag

### Fixed
- Fixed unit tests by adding missing `subcircuits` field
- Resolved S-expression formatting issues with lexpr

## [0.1.0] - 2025-01-06

### Added
- Initial release with basic KiCad schematic generation
- Simple API for creating empty schematics
- Support for multiple paper sizes (A4, A3, A2, A1, A0, Letter, Legal)
- Component placement and net connections
- Hierarchical label generation
- Python bindings via PyO3
- S-expression generation using lexpr crate
- Clean API without dotted pair notation

### Known Issues
- PySimpleComponent class not exporting to Python (debugging needed)
- Complex circuit data conversion incomplete

[Unreleased]: https://github.com/circuit-synth/circuit-synth/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/circuit-synth/circuit-synth/releases/tag/v0.1.0