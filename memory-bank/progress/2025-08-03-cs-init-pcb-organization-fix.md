# cs-init-pcb Organization Fix

## Summary
Fixed `cs-init-pcb` command to organize KiCad files in separate `kicad/` directory, preventing file clutter in project root.

## Key Changes
- Added `organize_kicad_files()` function to move all KiCad files to `kicad/` directory
- Updated `find_kicad_files()` to handle multiple schematics and file types (`.net`, `.json`, `.bak`)
- Modified project structure to show organized layout in documentation
- Updated generated templates to reference correct file paths

## Impact
Users now get clean project structure:
```
project/
├── kicad/             # All KiCad design files
├── circuit-synth/     # Python circuit files  
├── memory-bank/       # Documentation
└── .claude/           # AI assistant
```

## Testing
Verified with test project containing multiple KiCad files - all files correctly moved to `kicad/` directory.

## Commit
Committed as: `3995b92` - Fix cs-init-pcb to organize KiCad files in separate kicad/ directory