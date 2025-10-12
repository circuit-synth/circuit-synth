# Changelog

All notable changes to circuit-synth will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.38] - 2025-01-11

### Fixed
- **PCB Generation**: Fixed silent failure when `generate_pcb=True` was set but no `.kicad_pcb` file was created
  - Root cause: Incorrect parser API usage (`SExpressionParser().parse_file()` returns dict instead of Schematic object)
  - Solution: Changed to `ksa.Schematic.load()` which returns proper Schematic objects
  - Impact: PCB file generation now works correctly with all components properly placed

### Changed
- Updated kicad-sch-api dependency to `>=0.2.3` to include pin electrical type quoting fix

### Internal
- Removed extensive debug logging added during troubleshooting
- Cleaned up unused imports in PCB generation modules

## [0.8.37] - 2025-01-11

### Fixed
- Fixed kicad-sch-api pin electrical type quoting bug
  - Added missing pin types (`no_connect`, `open_collector`, `open_emitter`, `free`) to formatter validation
  - Prevents KiCAD schematic opening errors for components with these pin types

### Changed
- Updated kicad-sch-api to v0.2.3 with pin electrical type fix

## Previous Versions

(Changelog entries for versions prior to 0.8.37 are being compiled)
