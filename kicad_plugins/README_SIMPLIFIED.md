# Circuit-Synth KiCad Plugins - Simplified Structure

## 🎯 **SIMPLIFIED: Only 2 Plugin Files**

After cleanup, this directory now contains only the essential, working plugins:

### **Final Clean Structure:**
```
kicad_plugins/
├── circuit_synth_bom_plugin.py        # ✅ Schematic analysis (BOM method)
├── circuit_synth_pcb_bom_bridge.py    # ✅ PCB analysis (ActionPlugin)
├── install_plugin.py                  # ✅ Installation script  
├── images/                            # ✅ Screenshots for documentation
│   ├── pcb_plugin_screenshot.png
│   └── schematic_plugin_screenshot.png
└── README_SIMPLIFIED.md               # This file
```

### **Files Removed in This Cleanup:**
- ❌ `fix_kicad_integration.py` (debugging script)
- ❌ `quick_test_plugin.py` (testing script)
- ❌ `test_claude_integration.py` (16KB testing script)
- ❌ `test_plugin_functionality.py` (9KB testing script)
- ❌ `troubleshoot_bom_error.py` (11KB debugging script)
- ❌ `verify_installation.py` (testing script)

**Previous cleanup removed:** 15+ redundant plugin files and 2 directories  
**This cleanup removed:** 6 testing/debugging scripts

**Directory is now clean and production-ready!**

## 🚀 **Usage Instructions**

### **For Schematic Editor (Recommended):**
1. In KiCad Schematic Editor: `Tools → Generate Bill of Materials`
2. Add plugin: `circuit_synth_bom_plugin.py`
3. Command: `/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 "/path/to/circuit_synth_bom_plugin.py" "%I" "%O"`
4. Assign hotkey: `Ctrl+Shift+A` for quick access

### **For PCB Editor:**
1. In KiCad PCB Editor: `Tools → External Plugins → Circuit-Synth PCB Bridge`
2. Or use the plugin menu after installation

## 🔧 **Technical Details**

### **Schematic Plugin (`circuit_synth_bom_plugin.py`):**
- **Method:** BOM "backdoor" approach  
- **Size:** 8.4KB (compact, focused)
- **Features:** XML netlist parsing, tkinter GUI, circuit analysis
- **Unicode:** Fixed with UTF-8 encoding wrapper
- **Reliability:** High - proven working approach

### **PCB Plugin (`circuit_synth_pcb_bom_bridge.py`):**
- **Method:** ActionPlugin with BOM bridge
- **Size:** 9.2KB (compact, focused)  
- **Features:** PCB data extraction, launches schematic plugin
- **Unicode:** Fixed with UTF-8 encoding wrapper
- **Reliability:** High - simple bridge approach

## 🎯 **Why This Simplification?**

### **Problems Solved:**
- ❌ **Plugin proliferation** - 20+ files doing similar things
- ❌ **User confusion** - Multiple similar menu entries
- ❌ **Maintenance burden** - Bug fixes needed in multiple places
- ❌ **Quality inconsistency** - Some plugins had Unicode issues
- ❌ **Installation complexity** - Multiple installation methods

### **Benefits Achieved:**
- ✅ **Single source of truth** - One plugin per function
- ✅ **Reliable operation** - Only tested, working plugins kept
- ✅ **Easy maintenance** - Changes only need to be made once
- ✅ **Clear user experience** - Simple, obvious choices
- ✅ **Consistent quality** - Both plugins have same robustness standards

## 📋 **Installation**

Use the single installation script:
```bash
python3 kicad_plugins/install_plugin.py
```

This will:
1. Detect your KiCad installation
2. Copy both plugins to the correct directory
3. Set proper permissions
4. Provide usage instructions

## 🐛 **Troubleshooting**

### **Unicode Errors:**
Both plugins now include UTF-8 encoding fixes. If you still see Unicode errors:
1. Check your system locale: `locale`
2. Ensure KiCad is using UTF-8 encoding
3. Try the safe plugin alternative if needed

### **Plugin Not Found:**
1. Verify files are in: `~/Documents/KiCad/9.0/scripting/plugins/`
2. Check file permissions: `chmod +x plugin_file.py`
3. Restart KiCad after installation

## 🎯 **Future Development**

This simplified structure makes future development much easier:
- **Single plugin maintenance** - Changes go to one place
- **Clear architecture** - BOM method for schematic, ActionPlugin for PCB  
- **Extensible design** - Easy to add features without duplication
- **Quality control** - New features tested once, work everywhere

**This is the new canonical plugin structure for Circuit-Synth KiCad integration.**