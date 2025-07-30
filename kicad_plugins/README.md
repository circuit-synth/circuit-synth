# Circuit-Synth KiCad Plugins

AI-powered KiCad plugins that provide intelligent circuit design assistance for both PCB and schematic editors.

## 🚀 Overview

This directory contains **working KiCad plugins** that bring AI-powered circuit analysis directly into KiCad:

### 📋 **PCB Editor Plugin** 
- **Location**: Tools → External Plugins → "Circuit-Synth AI"
- **Features**: PCB analysis, component counting, schematic integration
- **Status**: ✅ Fully working with KiCad 9

![PCB Plugin Screenshot](images/pcb_plugin_screenshot.png)
*PCB Editor plugin showing comprehensive circuit analysis with both PCB and schematic data*

### 📐 **Schematic Editor Plugin**
- **Location**: Tools → Generate Bill of Materials → "Circuit-Synth AI" 
- **Features**: Component analysis, net analysis, AI design insights
- **Method**: Uses BOM tool "backdoor" approach (genius solution!)
- **Status**: ✅ Fully working with KiCad 9

![Schematic Plugin Screenshot](images/schematic_plugin_screenshot.png)
*Schematic Editor plugin using the BOM "backdoor" method to provide detailed circuit analysis*

### 🚀 **Enhanced Chat Plugin** *(New!)*
- **Location**: Tools → Generate Legacy Bill of Materials → "Circuit-Synth AI Chat"
- **Features**: Full AI chat interface, conversation history, export capabilities
- **Hotkey Support**: `Ctrl+Shift+A` for instant access
- **Status**: ✅ Production-ready with comprehensive GUI

*The enhanced chat plugin provides an interactive AI assistant with real-time conversation, quick action buttons, and complete analysis export capabilities.*

### 🤖 **Claude Code Integration** *(Latest!)*
- **Real AI Assistant**: Direct integration with Claude Code for genuine AI help
- **Context-Aware**: Analyzes your actual circuit data for relevant suggestions
- **Both Editors**: Available in both PCB and schematic editors
- **Professional UI**: Modern chat interfaces with conversation history
- **Export Capabilities**: Save AI conversations for documentation

*Bridge your KiCad workflow directly to Claude AI for real-time circuit design assistance.*

## 📦 Plugin Files

```
kicad_plugins/
├── README.md                              # This file
├── INSTALL.md                             # Complete installation guide
├── HOTKEY_SETUP.md                        # Hotkey configuration guide
├── WORKFLOW_GUIDE.md                      # User workflow strategies
├── PLUGIN_SUMMARY.md                      # Complete implementation summary
├── images/                                # Screenshots and documentation images
│   ├── pcb_plugin_screenshot.png          # PCB editor plugin in action
│   └── schematic_plugin_screenshot.png    # Schematic editor plugin demo
│
├── circuit_synth_ai/                      # PCB Editor Plugin
│   ├── __init__.py                        # Main plugin registration
│   ├── schematic_utils.py                 # Schematic analysis utilities
│   ├── ui/main_dialog.py                  # User interface components
│   └── resources/icon.png                 # Plugin icon
│
├── circuit_synth_chat_plugin.py           # Enhanced Schematic Chat Plugin
├── circuit_synth_claude_schematic_plugin.py # Claude-Integrated Schematic Plugin
├── circuit_synth_bom_plugin.py            # Basic Schematic BOM Plugin
├── circuit_synth_schematic_analyzer.py   # Standalone schematic analysis tool
├── claude_bridge.py                       # Claude Code integration bridge
├── test_plugin_functionality.py          # Comprehensive validation tests
├── test_claude_integration.py             # Claude integration test suite
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

*As shown in the screenshot above, the plugin provides detailed analysis including component counts, track analysis, and integrated schematic data.*

### **Schematic Editor Plugin**  
1. Open KiCad Schematic Editor
2. Open a schematic file
3. Tools → Generate Bill of Materials
4. Select "Circuit-Synth AI" from plugins list
5. Click "Generate" → AI analysis GUI appears!

*The schematic plugin screenshot demonstrates the comprehensive component breakdown, library analysis, and detailed circuit information that the plugin provides.*

## ✨ Features

### **PCB Analysis** (as shown in PCB screenshot)
- Component counting and analysis (20 components detected)
- Track and via analysis (0 tracks in example)
- Board size and complexity assessment
- Associated schematic integration with full cross-reference
- **Visual Output**: Professional dialog with KiCad branding and comprehensive data

### **Schematic Analysis** (as shown in schematic screenshot)
- Component type breakdown by library (Connector, Device, Diode, RF_Module, etc.)
- Detailed component listing with values and references
- Net connectivity analysis (53 total nets detected)
- AI-powered design recommendations
- Library usage statistics with exact counts
- **Visual Output**: Professional terminal-style analysis window with scrollable results

### **Enhanced Chat Interface** (circuit_synth_chat_plugin.py)
- Full interactive AI conversation with tkinter GUI
- Real-time circuit analysis and design suggestions
- Conversation history with timestamps
- Quick action buttons for common analysis tasks
- Export capabilities for chat logs and analysis reports
- **Visual Output**: Modern chat interface with conversation threading

### **AI Insights**
- Design complexity evaluation with quantitative metrics
- Component placement suggestions based on circuit topology
- Power supply optimization tips with specific recommendations
- Signal integrity recommendations for high-speed designs

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

## 📚 Documentation

- **Installation Guide**: [INSTALL.md](./INSTALL.md) - Complete installation instructions
- **Claude Setup**: [CLAUDE_SETUP.md](./CLAUDE_SETUP.md) - **NEW!** Complete Claude Code integration guide
- **Hotkey Setup**: [HOTKEY_SETUP.md](./HOTKEY_SETUP.md) - Configure `Ctrl+Shift+A` hotkey access
- **User Workflows**: [WORKFLOW_GUIDE.md](./WORKFLOW_GUIDE.md) - Optimization strategies and best practices  
- **Project Summary**: [PLUGIN_SUMMARY.md](./PLUGIN_SUMMARY.md) - Complete technical implementation details

## 🔗 Links

- **Main Project**: [Circuit-Synth Framework](https://github.com/circuit-synth/circuit-synth)
- **KiCad Forums**: [BOM Backdoor Discussion](https://forum.kicad.info/t/plugins-for-schematic-editor/51292)
- **Screenshots**: [images/](./images/) - Plugin demonstration screenshots

---

**🎯 Result**: Professional AI-powered circuit design assistance directly integrated into both KiCad editors!