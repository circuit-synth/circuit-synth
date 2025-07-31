# Circuit-Synth KiCad BOM Plugins

This directory contains BOM (Bill of Materials) plugins for KiCad Schematic Editor that provide AI-powered circuit analysis through Claude Code integration.

## 🚀 What This Provides

Instead of generating a traditional BOM, these plugins provide:
- **Real-time Claude AI chat** for circuit design assistance
- **Circuit context awareness** - Claude knows your schematic details
- **Professional analysis** with quick action buttons
- **Interactive conversation** with export capabilities

## 📂 Files

- `circuit_synth_bom_plugin.py` - Main Claude AI chat plugin
- `claude_bridge.py` - Claude Code integration bridge
- `README.md` - This file

## 🔧 Installation

### Automatic Installation (Recommended)
```bash
cd /path/to/circuit-synth
python install_kicad_plugins.py
```

### Manual Installation
1. Copy both `.py` files to your KiCad scripting plugins directory:
   - **macOS**: `~/Documents/KiCad/9.0/scripting/plugins/`
   - **Linux**: `~/.config/kicad/9.0/scripting/plugins/`
   - **Windows**: `~/Documents/KiCad/9.0/scripting/plugins/`

## 📖 Usage

### In KiCad Schematic Editor:
1. Open your schematic design
2. Go to **Tools** → **Generate Bill of Materials**
3. Click **Add Plugin** and select `circuit_synth_bom_plugin.py`
4. Click **Generate** → Claude AI chat interface opens!

### Quick Actions Available:
- **🔍 Analyze Circuit** - Comprehensive circuit analysis
- **🔧 Component Review** - Missing parts and issues
- **⚡ Power Analysis** - Power system check
- **🕸️ Net Analysis** - Connectivity analysis
- **💡 Optimization Tips** - Design recommendations
- **🐛 Find Issues** - Problem identification
- **📊 Generate Report** - Detailed analysis
- **💾 Export Chat** - Save conversation history

## 🛠️ Requirements

- **KiCad 9.0+** (may work with 8.x)
- **Python 3.8+** with tkinter
- **Claude CLI** for AI functionality: https://claude.ai/code

## 🚨 Troubleshooting

### Plugin Not Showing Up
- Restart KiCad after installation
- Check file permissions (should be readable)
- Verify plugin directory path in KiCad settings

### Claude Connection Issues
- Install Claude CLI: `npm install -g @anthropic-ai/claude-cli`
- Verify Claude CLI works: `claude --version`
- Check network connectivity

### GUI Issues
- Ensure tkinter is installed: `python -c "import tkinter"`
- Try running plugin manually to see error messages

## 🎯 Why Use BOM Plugin Method?

KiCad's Schematic Editor doesn't support ActionPlugins like the PCB Editor does. The BOM plugin system provides a "backdoor" method to:
1. Access schematic netlist data
2. Launch AI analysis tools
3. Provide circuit-aware assistance

This is a standard approach used by many KiCad schematic analysis plugins.

## 🔄 Updates

To update the plugins:
1. Pull latest circuit-synth repository
2. Run `python install_kicad_plugins.py` again
3. Restart KiCad

## 💡 Tips

- Use **quick action buttons** for common analysis tasks
- Export chat history for documentation
- Ask specific questions about your circuit design
- Claude understands your component types and connectivity

---

**This plugin turns KiCad's BOM tool into a powerful AI circuit analysis assistant!** 🚀