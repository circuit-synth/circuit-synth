# Claude Code Integration Setup Guide

Complete guide to set up real AI assistance in KiCad through Claude Code integration.

## 🎯 Overview

The Circuit-Synth KiCad plugins now feature **direct integration with Claude Code**, providing real AI assistance for circuit design directly within KiCad. This integration enables:

- **Real-time AI conversations** about your circuit designs
- **Context-aware analysis** of your PCB and schematic data
- **Professional design recommendations** from Claude
- **Interactive problem-solving** for circuit issues
- **Conversation history and export** for documentation

## 📋 Prerequisites

### 1. **Claude CLI Installation**

First, install the Claude Code CLI tool:

**macOS (Homebrew):**
```bash
# If you don't have Homebrew, install it first
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Claude CLI
brew install claude-cli
```

**Alternative Installation:**
```bash
# Direct download (check latest release)
curl -L https://github.com/anthropics/claude-cli/releases/latest/download/claude-cli-macos -o claude
chmod +x claude
sudo mv claude /usr/local/bin/
```

**Windows:**
```powershell
# Using Chocolatey
choco install claude-cli

# Or download directly from GitHub releases
# https://github.com/anthropics/claude-cli/releases
```

**Linux:**
```bash
# Download and install
curl -L https://github.com/anthropics/claude-cli/releases/latest/download/claude-cli-linux -o claude
chmod +x claude
sudo mv claude /usr/local/bin/
```

### 2. **Claude API Key Setup**

You need a Claude API key from Anthropic:

1. **Get API Key**: Visit [console.anthropic.com](https://console.anthropic.com)
2. **Create Account**: Sign up or log in
3. **Generate Key**: Go to API Keys section and create a new key
4. **Configure CLI**: Set up your API key

```bash
# Set API key (replace with your actual key)
claude configure set api_key your_api_key_here

# Or set as environment variable
export ANTHROPIC_API_KEY=your_api_key_here
```

### 3. **Verify Installation**

Test that Claude CLI is working:

```bash
# Check version
claude --version

# Test basic functionality
claude --message "Hello Claude, are you working?"
```

If this works, you're ready for KiCad integration!

## 🚀 KiCad Plugin Setup

### **Method 1: Automated Installation**

```bash
cd kicad_plugins/
uv run python install_plugin.py
```

This installs all plugins including Claude integration support.

### **Method 2: Manual Installation**

1. **Copy Claude Bridge**:
   ```bash
   cp claude_bridge.py ~/Documents/KiCad/9.0/scripting/plugins/
   ```

2. **Copy Enhanced PCB Plugin**:
   ```bash
   cp -r circuit_synth_ai ~/Documents/KiCad/9.0/scripting/plugins/
   ```

3. **Copy Claude Schematic Plugin**:
   ```bash
   cp circuit_synth_claude_schematic_plugin.py ~/Documents/KiCad/9.0/scripting/plugins/
   ```

4. **Set Permissions** (Linux/macOS):
   ```bash
   chmod +x ~/Documents/KiCad/9.0/scripting/plugins/circuit_synth_claude_schematic_plugin.py
   chmod +x ~/Documents/KiCad/9.0/scripting/plugins/claude_bridge.py
   ```

### **Method 3: Add Claude Schematic Plugin to BOM Tools**

1. **Open KiCad Schematic Editor**
2. **Tools → Generate Bill of Materials**
3. **Click "+" to add plugin**
4. **Browse to**: `circuit_synth_claude_schematic_plugin.py`
5. **Nickname**: "Circuit-Synth AI Claude Chat"
6. **Command line**: `python3 "%I" "%O"`
7. **Save configuration**

## ⌨️ Hotkey Setup for Instant Access

Configure hotkeys for lightning-fast AI assistance:

### **Schematic Editor Hotkey**

1. **KiCad → Preferences → Hotkeys**
2. **Search**: "Generate Legacy Bill of Materials"
3. **Assign**: `Ctrl+Shift+A` (recommended)
4. **Apply and close**

### **PCB Editor Hotkey**

1. **KiCad → Preferences → Hotkeys**
2. **Search**: "External Plugins"
3. **Assign**: `Ctrl+Shift+A` (recommended)
4. **Apply and close**

## 🎯 Using Claude Integration

### **PCB Editor Claude Chat**

1. **Open PCB file in KiCad**
2. **Press `Ctrl+Shift+A`** OR **Tools → External Plugins → Circuit-Synth AI**
3. **Enhanced Claude chat window opens**
4. **Chat directly with Claude** about your PCB design
5. **Get real-time analysis and recommendations**

**Features:**
- **Live PCB analysis** with component and routing data
- **Interactive chat** with conversation history
- **Quick action buttons** for common analysis tasks
- **Professional UI** with rich text formatting
- **Export capabilities** for documentation

### **Schematic Editor Claude Chat**

1. **Open schematic file in KiCad**
2. **Press `Ctrl+Shift+A`** OR **Tools → Generate Legacy Bill of Materials**
3. **Select "Circuit-Synth AI Claude Chat"**
4. **Press "Generate"**
5. **Enhanced Claude interface launches**
6. **Interactive AI assistance** for your schematic

**Features:**
- **Comprehensive circuit analysis** from netlist data
- **Component-aware conversations** with library knowledge
- **Net connectivity analysis** and optimization suggestions
- **Modern GUI** with quick action grid
- **Conversation export** in multiple formats

## 💡 Example Conversations

### **PCB Analysis Example**

```
You: Analyze my PCB layout for signal integrity issues

Claude: Looking at your PCB design, I can see several areas for improvement:

🔍 **Component Analysis**: 20 components detected including high-speed digital ICs
📐 **Layout Observations**: 
- Traces near high-frequency components could benefit from better routing
- Consider adding ground planes for better signal return paths
- Some decoupling capacitors appear to be placed optimally

⚡ **Signal Integrity Recommendations**:
1. Keep high-speed clock traces short and direct
2. Add guard traces around sensitive analog signals  
3. Ensure proper via stitching between ground planes
4. Consider controlled impedance for differential pairs

Would you like me to analyze any specific aspect in more detail?
```

### **Schematic Analysis Example**

```
You: Review my power supply design

Claude: I've analyzed your power system and here's my assessment:

🔋 **Power Components Found**:
- U2: AMS1117-3.3 (Linear regulator)
- Multiple decoupling capacitors (good!)
- Input filtering present

💡 **Analysis**:
✅ **Strengths**:
- Proper input/output decoupling on regulator
- Good capacitor selection (10µF + 100nF combination)
- Clean power distribution topology

⚠️ **Recommendations**:
1. Consider adding a ferrite bead on the input for EMI filtering
2. Verify thermal considerations for the linear regulator under full load
3. Add test points for voltage monitoring during debug

Would you like me to suggest specific component values or analyze the thermal design?
```

## 🔧 Advanced Configuration

### **Custom Claude Prompts**

You can customize how Claude analyzes your circuits by modifying the context preparation in `claude_bridge.py`:

```python
def _prepare_message_with_context(self, message: str) -> str:
    # Add custom analysis instructions
    custom_instructions = """
    Focus on:
    - Manufacturing considerations
    - Cost optimization
    - Thermal analysis
    - EMI/EMC compliance
    """
    # ... rest of method
```

### **Debug Mode**

Enable debug logging to troubleshoot Claude integration:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### **Offline Mode**

If Claude is unavailable, the plugins gracefully fall back to local analysis:

- **PCB Plugin**: Shows basic board statistics and component analysis
- **Schematic Plugin**: Provides component breakdown and net analysis
- **Status Indicators**: Clear indication when Claude is unavailable

## 🐛 Troubleshooting

### **Claude CLI Not Found**

```bash
# Verify installation
which claude
claude --version

# If not found, reinstall
brew reinstall claude-cli  # macOS
```

### **API Key Issues**

```bash
# Reconfigure API key
claude configure set api_key your_new_api_key

# Test API connection
claude --message "test connection"
```

### **Plugin Not Appearing**

1. **Check file permissions**: Ensure plugins are executable
2. **Verify paths**: Confirm plugins are in correct KiCad directory
3. **Restart KiCad**: Full restart after installation
4. **Check KiCad version**: Requires KiCad 9.0+

### **Connection Timeouts**

```python
# In claude_bridge.py, increase timeout
result = subprocess.run([...], timeout=60)  # Increase from 30
```

### **Memory Issues**

For large circuits, the plugins automatically optimize context:
- **Component Limiting**: Shows first 5 components per library
- **Net Filtering**: Focuses on high-fanout nets
- **Context Chunking**: Breaks large designs into sections

## 📊 Performance Tips

### **For Large Designs**

1. **Use Quick Actions**: Pre-configured prompts are faster
2. **Focus Questions**: Ask about specific subsystems
3. **Export Conversations**: Save important analyses for reference
4. **Context Refresh**: Update context when design changes significantly

### **Best Practices**

1. **Specific Questions**: "Analyze my power supply" vs "Help me"
2. **Iterative Design**: Ask follow-up questions to dive deeper
3. **Export Insights**: Save valuable recommendations
4. **Regular Updates**: Refresh context after major design changes

## 🚀 What's Next?

The Claude integration enables:

- **Real-time design feedback** as you work
- **Professional-grade analysis** from AI assistant
- **Learning acceleration** through interactive guidance
- **Documentation generation** via conversation export
- **Design optimization** through AI insights

**🎯 Result**: Professional AI-powered circuit design assistance directly integrated into your KiCad workflow!

---

*This integration represents a breakthrough in CAD tool AI assistance, bringing the power of large language models directly into the circuit design process.*