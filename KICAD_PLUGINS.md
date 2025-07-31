# Circuit-Synth KiCad Plugins

Easy installation of AI-powered plugins for KiCad PCB Editor and Schematic Editor.

## 🚀 Quick Installation

### Method 1: After Installing Circuit-Synth Package
```bash
pip install circuit-synth
install-kicad-plugins
```

### Method 2: From Repository  
```bash
git clone <circuit-synth-repo>
cd circuit-synth
python3 install_kicad_plugins.py
```

### Method 3: Direct Download
```bash
curl -O https://raw.githubusercontent.com/circuit-synth/circuit-synth/main/install_kicad_plugins.py
python3 install_kicad_plugins.py
```

## 🎯 What Gets Installed

### PCB Editor Plugin
- **Name**: Circuit-Synth AI (Simple)
- **Location**: Toolbar button in KiCad PCB Editor
- **Features**: Board analysis, component counting, design recommendations

### Schematic Editor Plugin  
- **Name**: Circuit-Synth BOM Plugin
- **Location**: Tools → Generate Bill of Materials
- **Features**: Full Claude AI chat interface with circuit context

## 📂 Cross-Platform Support

The installer automatically detects your platform and installs to the correct directories:

- **macOS**: `~/Documents/KiCad/9.0/`
- **Linux**: `~/.config/kicad/9.0/`  
- **Windows**: `%USERPROFILE%/Documents/KiCad/9.0/`

## 🔧 Requirements

- **KiCad 9.0+** (may work with 8.x)
- **Python 3.8+**
- **Claude CLI** for AI features: https://claude.ai/code

## 📖 Usage

### PCB Editor
1. Open KiCad PCB Editor with a board file
2. Look for **"Circuit-Synth AI (Simple)"** toolbar button
3. Click to analyze your PCB and get design insights

### Schematic Editor
1. Open KiCad Schematic Editor with a schematic
2. Go to **Tools → Generate Bill of Materials**
3. Add Plugin: Select `circuit_synth_bom_plugin.py`
4. Click **Generate** → Full Claude AI chat interface opens!

## ✨ Features

### PCB Analysis
- Component counting and categorization
- Track and via analysis
- Design complexity assessment
- Quick recommendations

### AI Chat (Schematic)
- **🔍 Analyze Circuit** - Comprehensive analysis
- **🔧 Component Review** - Missing parts detection  
- **⚡ Power Analysis** - Power system verification
- **🕸️ Net Analysis** - Connectivity analysis
- **💡 Optimization Tips** - Design improvements
- **🐛 Find Issues** - Problem identification
- **📊 Generate Report** - Detailed documentation
- **💾 Export Chat** - Save conversations

## 🚨 Troubleshooting

### Plugin Not Appearing
- Restart KiCad after installation
- Check KiCad → Preferences → Plugin paths
- Verify file permissions (should be readable)

### Claude Connection Issues
- Install Claude CLI: `npm install -g @anthropic-ai/claude-cli`
- Test: `claude --version`
- Check internet connection

### Installation Issues
- Run installer with `python3` (not `python`)
- Ensure you have write permissions to KiCad directories
- Try running installer as administrator (Windows)

## 🔄 Updates

To update plugins:
```bash
install-kicad-plugins  # If installed via pip
# OR
python3 install_kicad_plugins.py  # From repository
```

## 💡 Why These Plugins?

- **PCB Plugin**: Uses KiCad's ActionPlugin system for toolbar integration
- **Schematic Plugin**: Uses BOM tool "backdoor" since ActionPlugins aren't supported in Schematic Editor
- **Cross-Platform**: Works on macOS, Linux, and Windows
- **Easy Installation**: One command installs everything
- **AI Integration**: Real Claude Code assistance for circuit design

---

**Transform your KiCad workflow with AI-powered circuit analysis!** 🚀