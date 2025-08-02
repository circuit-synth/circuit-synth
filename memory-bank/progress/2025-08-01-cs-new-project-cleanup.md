# CS New Project Cleanup

## Summary
Cleaned up cs-new-project to create minimal project structure by removing kicad_plugins directory creation and moving plugin setup to separate cs-setup-kicad-plugins command.

## Key Changes
- Removed kicad_plugins directory from new projects to minimize clutter
- Created separate cs-setup-kicad-plugins command for optional KiCad integration
- Fixed netlist file locations (.net to KiCad folder, .json to circuit-synth folder)
- Updated logging to use ~/.circuit-synth/logs instead of polluting project directories

## Impact
Projects now have cleaner structure with only essential files, and KiCad plugins are installed separately when needed.