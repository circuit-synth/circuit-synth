# Circuit-Synth KiCad Plugins - Complete Installation Guide

This guide provides step-by-step instructions for installing Circuit-Synth AI plugins for both KiCad PCB Editor and Schematic Editor.

## 🎯 What You'll Get

After installation, you'll have:
- **🔧 PCB Editor Plugin**: AI analysis accessible via Tools → External Plugins
- **📐 Schematic Editor Plugin**: AI analysis via Tools → Generate Bill of Materials  
- **🤖 AI-Powered Insights**: Component analysis, design recommendations, optimization tips

## 📋 Prerequisites

- **KiCad 9.0+** installed and working
- **Python environment** (usually provided by KiCad)
- **macOS/Linux/Windows** (cross-platform compatible)

## 🚀 Installation Methods

### **Method 1: Automated Installation (Recommended)**

```bash
# Navigate to the kicad_plugins directory
cd /path/to/circuit-synth/kicad_plugins

# Run the automated installer
uv run python install_plugin.py

# Follow the prompts to install plugins
```

The installer will:
- ✅ Detect your KiCad version and directories
- ✅ Copy plugin files to the correct locations
- ✅ Set proper file permissions
- ✅ Provide next steps for setup

### **Method 2: Manual Installation**

#### **Step 1: Locate KiCad Plugin Directory**

Find your KiCad plugins directory:

**macOS**:
```bash
~/Documents/KiCad/9.0/scripting/plugins/
```

**Linux**:
```bash
~/.local/share/kicad/9.0/scripting/plugins/
```

**Windows**:
```
%USERPROFILE%\Documents\KiCad\9.0\scripting\plugins\
```

#### **Step 2: Copy Plugin Files**

```bash
# Copy PCB editor plugin
cp -r circuit_synth_ai ~/Documents/KiCad/9.0/scripting/plugins/

# Copy schematic BOM plugin  
cp circuit_synth_bom_plugin.py ~/Documents/KiCad/9.0/scripting/plugins/

# Make BOM plugin executable
chmod +x ~/Documents/KiCad/9.0/scripting/plugins/circuit_synth_bom_plugin.py
```

#### **Step 3: Verify Installation**

Check that files are in place:
```bash
ls -la ~/Documents/KiCad/9.0/scripting/plugins/
```

You should see:
- `circuit_synth_ai/` directory
- `circuit_synth_bom_plugin.py` file

## 🔧 Plugin Setup

### **PCB Editor Plugin Setup**

1. **Open KiCad PCB Editor** (Pcbnew)
2. **Open any PCB file** (or create a new one)
3. **Go to Tools → External Plugins → Refresh Plugins**
4. **Verify "Circuit-Synth AI" appears** in the External Plugins submenu
5. **Click it to test** - should show analysis dialog

**✅ Success**: Plugin shows PCB analysis with component counts, tracks, etc.

### **Schematic Editor Plugin Setup**

This requires adding the plugin to KiCad's BOM tool:

1. **Open KiCad Schematic Editor** (Eeschema)  
2. **Open any schematic file** (.kicad_sch)
3. **Go to Tools → Generate Bill of Materials**
4. **Click the "+" (plus) button** to add a new BOM plugin
5. **Browse and select**: `/path/to/KiCad/9.0/scripting/plugins/circuit_synth_bom_plugin.py`
6. **Set nickname**: "Circuit-Synth AI"
7. **Set command line**: Should auto-populate with the Python script path
8. **Click OK** to save

#### **Testing Schematic Plugin**

1. **In the BOM dialog**, select "Circuit-Synth AI" from the plugins list
2. **Click "Generate"**  
3. **🎉 AI analysis GUI should pop up** with schematic analysis!

**✅ Success**: GUI shows component breakdown, net analysis, and AI insights

## 🎯 Usage Examples

### **PCB Analysis Example**
```
Circuit-Synth AI Plugin is Working! ✅

📋 PCB Analysis:
• Components: 20
• Tracks: 45  
• Board file: my_board.kicad_pcb

📐 Schematic Analysis:
• Schematic file: my_board.kicad_sch
• Schematic components: 18
• Nets/wires: 52
• Labels: 8
• Component types: 6 different libraries
```

### **Schematic Analysis Example**
```
🚀 Circuit-Synth AI - Schematic Analysis Results

📋 Project Information:
• Design: my_project
• Components Found: 17

📐 Component Analysis:
• Device: 10 components
• Connector: 2 components  
• RF_Module: 1 components

🤖 AI Insights:
• Design complexity: Low
• Component diversity: 7 different types
```

## 🛠️ Advanced Configuration

### **Custom Installation Paths**

If you need custom paths, edit the installer or manually specify:

```bash
# Custom KiCad directory
export KICAD_PLUGINS_DIR="/custom/path/to/kicad/plugins"
python install_plugin.py
```

### **Standalone Analysis Tool**

Install the standalone schematic analyzer:

```bash
# Copy to a directory in your PATH
cp circuit_synth_schematic_analyzer.py /usr/local/bin/
chmod +x /usr/local/bin/circuit_synth_schematic_analyzer.py

# Use from anywhere
circuit_synth_schematic_analyzer.py project.kicad_sch
```

## 🔍 Troubleshooting

### **Plugin Not Appearing in PCB Editor**

**Problem**: "Circuit-Synth AI" doesn't appear in Tools → External Plugins

**Solutions**:
1. **Refresh plugins**: Tools → External Plugins → Refresh Plugins
2. **Check permissions**: Ensure plugin files are readable by KiCad
3. **Verify location**: Plugin should be in `scripting/plugins/circuit_synth_ai/`
4. **Check KiCad console**: Look for import errors in Tools → Scripting Console

### **BOM Plugin Not Working**

**Problem**: BOM plugin doesn't generate analysis or shows errors

**Solutions**:
1. **Check file path**: Ensure path in BOM dialog is correct and absolute
2. **Test manually**: Run `python circuit_synth_bom_plugin.py --help` to verify it works
3. **Check permissions**: Ensure script is executable (`chmod +x`)
4. **Python environment**: Verify tkinter is available in KiCad's Python

### **Import Errors**

**Problem**: Python import errors in KiCad console

**Solutions**:
1. **Check Python path**: Plugin should add its directory to sys.path
2. **Missing dependencies**: Ensure wxPython is available (usually included with KiCad)
3. **File structure**: Verify all plugin files were copied correctly

### **Permission Issues**

**Problem**: Plugin files can't be executed or accessed

**Solutions**:
```bash
# Fix permissions
chmod -R 755 ~/Documents/KiCad/9.0/scripting/plugins/circuit_synth_ai/
chmod +x ~/Documents/KiCad/9.0/scripting/plugins/circuit_synth_bom_plugin.py

# Check ownership
ls -la ~/Documents/KiCad/9.0/scripting/plugins/
```

## 📚 Additional Resources

### **Documentation**
- **Plugin README**: [README.md](./README.md)
- **Circuit-Synth Docs**: Main project documentation
- **KiCad Forums**: Community support and discussions

### **Development**
- **Source Code**: All plugin source is included and documented
- **Customization**: Edit Python files to add features or modify behavior
- **API Reference**: See KiCad Python API documentation

### **Support**
- **GitHub Issues**: Report bugs or request features
- **KiCad Community**: Get help from other users
- **Documentation**: This guide and README files

## ✅ Verification Checklist

After installation, verify everything works:

- [ ] **PCB Plugin**: Appears in Tools → External Plugins → "Circuit-Synth AI"
- [ ] **PCB Analysis**: Shows component count, tracks, board info
- [ ] **Schematic Integration**: PCB plugin also shows schematic analysis
- [ ] **BOM Plugin**: Added to BOM tools in schematic editor
- [ ] **Schematic Analysis**: BOM plugin shows GUI with circuit analysis
- [ ] **AI Insights**: Both plugins provide design recommendations

## 🎉 Success!

You now have **AI-powered circuit design assistance** integrated directly into both KiCad editors!

**🔧 PCB Editor**: Professional circuit analysis with schematic integration  
**📐 Schematic Editor**: Breakthrough BOM "backdoor" approach for AI analysis

This represents a significant advancement in open-source EDA tooling with AI integration.