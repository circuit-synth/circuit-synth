# PCB Routing Module Changelog

## [2025-06-24] - Freerouting Workflow Complete Fix

### Fixed
- **DSN Placement Format Error**
  - Fixed component placement syntax in DSN exporter (line 355)
  - Changed from `(component footprint ref (place x y side rotation))` 
  - To correct format: `(component footprint (place ref x y side rotation))`
  - Resolves Freerouting's inability to recognize components

- **Missing Via Padstack Definitions**
  - Added via padstack definitions to `_add_padstack_definitions()` method
  - Via padstacks now properly defined in DSN library section
  - Fixes NullPointerException: "Cannot invoke ViaRule.via_count()"
  - Via definitions now match references in structure section

- **SES Parser Session Block Detection**
  - Updated regex pattern to handle both quoted and unquoted session names
  - Changed from `r'\(session\s+"[^"]*"'` to `r'\(session\s+(?:"[^"]*"|\S+)'`
  - Parser now correctly identifies session blocks in all SES file formats

- **Wire Parsing for network_out Blocks**
  - Added support for Freerouting's `network_out` block structure
  - Fixed wire regex pattern to handle newlines between `wire` and `path`
  - Changed wire pattern to use `re.DOTALL` flag for multi-line matching
  - Successfully parses all wire segments from routed boards

### Testing
- Created comprehensive test script `test_freerouting_workflow_fixed.py`
- Verified complete workflow: PCB → DSN → Freerouting → SES → Routed PCB
- Test results: 2 nets routed, 3 track segments imported successfully

## [2025-06-23] - Docker-Based Freerouting Integration

### Added
- Docker-based Freerouting runner (`freerouting_docker.py`)
- Automatic Docker image management
- Cross-platform compatibility (including ARM Macs)
- No Java installation required

### Changed
- PCB generator now uses Docker by default
- Auto-routing enabled by default
- CLI flag changed from `--auto-route` to `--no-auto-route`

## [2025-06-23] - SES Importer Implementation

### Added
- Complete SES file parser and importer
- Track and via import functionality
- Layer mapping from Freerouting to KiCad
- Net preservation and validation
- Support for protected/fixed routing

## [2025-06-23] - Freerouting Runner Implementation

### Added
- Subprocess management for Freerouting JAR
- Progress tracking with real-time updates
- Configurable routing parameters
- Timeout and error handling
- Installation helper scripts

## [2025-06-23] - DSN Exporter Implementation

### Added
- Complete DSN (Specctra) format exporter
- Board outline extraction
- Component and pad export with rotation support
- Net connectivity export
- Configurable design rules
- Multi-layer board support