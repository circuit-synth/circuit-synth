# KiCad Plugin Architecture Decision

## Date: 2025-07-30

## Context
Need to integrate Claude AI assistance into KiCad schematic design workflow.

## Decision: BOM Tool "Backdoor" Method

### Chosen Approach
Use KiCad's BOM (Bill of Materials) tool as entry point for schematic plugins.

### Rationale
1. **KiCad Limitation**: No native schematic plugin API (unlike PCB editor)
2. **BOM Tool Access**: BOM tool can execute Python scripts with netlist input
3. **Netlist Contains Everything**: Full schematic data available in XML format
4. **User Experience**: Simple hotkey access via BOM tool

### Technical Implementation
```
KiCad Schematic → Tools → Generate BOM → Select Plugin → Python Script Executes
```

### Plugin Command Format
```bash
/path/to/python3 "/path/to/plugin.py" "%I" "%O"
# %I = Input netlist XML file
# %O = Output file path
```

### Architecture Benefits
- ✅ **Complete Circuit Context**: Access to all components, nets, connections
- ✅ **Hotkey Integration**: Can assign keyboard shortcuts
- ✅ **No KiCad Modifications**: Works with standard KiCad installation
- ✅ **Cross-Platform**: Works on macOS, Linux, Windows

### Architecture Challenges
- ❌ **Command Line Corruption**: Long file paths get line breaks inserted
- ❌ **Environment Issues**: KiCad's Python environment differs from system
- ❌ **GUI Threading**: Need careful handling of blocking operations

### Solutions Implemented
1. **Short Filenames**: Use short plugin names to avoid line break corruption
2. **Full Paths**: Use absolute paths for Claude CLI to bypass PATH issues  
3. **Multiple Methods**: Try different connection approaches automatically
4. **Robust Error Handling**: Graceful fallbacks when connections fail

## Alternative Approaches Considered

### PCB Plugin API
- Available but only works in PCB editor
- Cannot access schematic-level information
- Used for PCB-specific features

### External Tools
- Separate applications outside KiCad
- No direct circuit context access
- Poor user experience (context switching)

## Conclusion
The BOM backdoor method provides the best balance of functionality and integration, despite some technical challenges that we've successfully addressed.