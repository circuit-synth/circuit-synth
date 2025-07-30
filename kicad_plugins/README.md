# Circuit-Synth KiCad Plugins

AI-powered KiCad plugins that provide intelligent circuit design assistance for both PCB and schematic editors.

## 🚀 Overview

This directory contains **working KiCad plugins** that bring AI-powered circuit analysis directly into KiCad:

### 📋 **PCB Editor Plugin** 
- **Location**: Tools → External Plugins → "Circuit-Synth AI"
- **Features**: PCB analysis, component counting, schematic integration
- **Status**: ✅ Fully working with KiCad 9

### 📐 **Schematic Editor Plugin**
- **Location**: Tools → Generate Bill of Materials → "Circuit-Synth AI" 
- **Features**: Component analysis, net analysis, AI design insights
- **Method**: Uses BOM tool "backdoor" approach (genius solution!)
- **Status**: ✅ Fully working with KiCad 9

## 📦 Plugin Files

```
kicad_plugins/
├── README.md                              # This file
├── INSTALL.md                             # Complete installation guide
├── 
├── circuit_synth_ai/                      # PCB Editor Plugin
│   ├── __init__.py                        # Main plugin registration
│   ├── schematic_utils.py                 # Schematic analysis utilities
│   ├── ui/main_dialog.py                  # User interface components
│   └── resources/icon.png                 # Plugin icon
│
├── circuit_synth_bom_plugin.py            # Schematic Editor BOM "Backdoor" Plugin
├── circuit_synth_schematic_analyzer.py   # Standalone schematic analysis tool
│
└── install_plugin.py                     # Automated installer script
```

## ⚡ Quick Install

### **Automated Installation**
```bash
cd kicad_plugins/
uv run python install_plugin.py
```

### **Manual Installation**
1. **Copy PCB plugin**: `cp -r circuit_synth_ai ~/Documents/KiCad/9.0/scripting/plugins/`
2. **Copy BOM plugin**: `cp circuit_synth_bom_plugin.py ~/Documents/KiCad/9.0/scripting/plugins/`
3. **Restart KiCad**
4. **Add BOM plugin**: In schematic editor → Tools → Generate Bill of Materials → Add plugin

## 🎯 How to Use

### **PCB Editor Plugin**
1. Open KiCad PCB Editor
2. Open a PCB file  
3. Tools → External Plugins → Refresh Plugins
4. Click "Circuit-Synth AI"
5. Get comprehensive PCB + schematic analysis!

### **Schematic Editor Plugin**  
1. Open KiCad Schematic Editor
2. Open a schematic file
3. Tools → Generate Bill of Materials
4. Select "Circuit-Synth AI" from plugins list
5. Click "Generate" → AI analysis GUI appears!

## ✨ Features

### **PCB Analysis**
- Component counting and analysis
- Track and via analysis  
- Board size and complexity assessment
- Associated schematic integration

### **Schematic Analysis**
- Component type breakdown
- Net connectivity analysis
- Design complexity assessment
- AI-powered design recommendations
- Library usage statistics

### **AI Insights**
- Design complexity evaluation
- Component placement suggestions
- Power supply optimization tips
- Signal integrity recommendations

## 🔧 Advanced Tools

### **Standalone Schematic Analyzer**
```bash
# Analyze single schematic
uv run python circuit_synth_schematic_analyzer.py file.kicad_sch

# Analyze entire project
uv run python circuit_synth_schematic_analyzer.py --project ./project_dir

# Verbose output with details
uv run python circuit_synth_schematic_analyzer.py --verbose file.kicad_sch
```

## 🎉 Innovation: BOM "Backdoor" Method

The schematic plugin uses a **breakthrough approach** discovered on KiCad forums:

- **Problem**: KiCad's schematic editor doesn't support ActionPlugins
- **Solution**: Use BOM tool as "backdoor" to run Python analysis
- **Result**: Full AI analysis directly in schematic editor!

**Credit**: BlackCoffee on KiCad forums for the BOM backdoor technique

## 🛠️ Development

### **Plugin Architecture**
- **PCB Plugin**: Uses `pcbnew.ActionPlugin` framework
- **Schematic Plugin**: Uses BOM tool XML netlist parsing
- **Shared Utils**: Common analysis functions and utilities

### **Extending Plugins**
- Add new analysis algorithms in `schematic_utils.py`
- Enhance UI in `ui/main_dialog.py`  
- Integrate external AI services for advanced analysis

## 📋 Requirements

- **KiCad 9.0+** (tested with KiCad 9.0)
- **Python 3.8+** with wxPython (provided by KiCad)
- **tkinter** for BOM plugin GUI (usually included with Python)

## 🐛 Troubleshooting

### **Plugin Not Appearing**
- Run "Refresh Plugins" in PCB editor
- Check file permissions are correct
- Verify KiCad version is 9.0+

### **BOM Plugin Issues**  
- Ensure Python script is executable
- Check BOM plugin was added with correct path
- Verify tkinter is available in KiCad's Python

### **Import Errors**
- Plugins are designed to fail gracefully
- Check KiCad's scripting console for error messages

## 🔗 Links

- **Main Project**: [Circuit-Synth Framework](https://github.com/circuit-synth/circuit-synth)
- **Installation Guide**: [INSTALL.md](./INSTALL.md)
- **KiCad Forums**: [BOM Backdoor Discussion](https://forum.kicad.info/t/plugins-for-schematic-editor/51292)

---

**🎯 Result**: Professional AI-powered circuit design assistance directly integrated into both KiCad editors!