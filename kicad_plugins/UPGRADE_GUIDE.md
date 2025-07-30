# Upgrade Guide: Claude Code Integration

**🚀 New Feature**: Your KiCad plugins now include direct Claude AI integration for real circuit design assistance!

## 🎯 What's New

### **Real AI Assistant**
- **Direct Claude Integration**: Chat with Claude AI about your actual circuit designs
- **Context-Aware Analysis**: AI understands your components, nets, and layout
- **Professional Advice**: Get genuine design recommendations and troubleshooting help
- **Conversation History**: Save and export AI conversations for documentation

### **Enhanced Interfaces**
- **PCB Editor**: Upgraded to include Claude chat interface
- **Schematic Editor**: New Claude-integrated plugin with modern GUI
- **Smart Context**: AI automatically analyzes your current design

## 🔄 Upgrading Your Installation

### **Step 1: Install New Plugins**

**Run the enhanced installer:**
```bash
cd kicad_plugins/
uv run python install_claude_plugins.py
```

**Verify everything installed correctly:**
```bash
uv run python verify_installation.py
```

### **Step 2: Set Up Claude CLI (Required for AI features)**

**Install Claude CLI:**
```bash
# macOS (Homebrew)
brew install claude-cli

# Or download directly from GitHub releases
```

**Configure API Key:**
```bash
# Get your API key from https://console.anthropic.com
claude configure set api_key YOUR_API_KEY_HERE
```

**Test Claude:**
```bash
claude "Hello, are you working?"
```

### **Step 3: Configure KiCad BOM Plugins**

**For Schematic Editor AI:**
1. Open KiCad Schematic Editor
2. Go to: **Tools → Generate Bill of Materials**
3. Click **"+"** to add plugins
4. Add these plugins from your KiCad scripting directory:

**🤖 Claude-Integrated Plugin (Recommended):**
- **File**: `circuit_synth_claude_schematic_plugin.py`
- **Nickname**: "Circuit-Synth AI Claude Chat"
- **Command**: `python3 "%I" "%O"`

**📱 Enhanced Chat Plugin:**
- **File**: `circuit_synth_chat_plugin.py`
- **Nickname**: "Circuit-Synth AI Enhanced Chat"
- **Command**: `python3 "%I" "%O"`

5. **Save** the configuration

### **Step 4: Set Up Hotkeys**

**Configure Quick Access:**
1. Go to: **Preferences → Hotkeys**
2. Search: **"Generate Legacy Bill of Materials"**
3. Assign: **`Ctrl+Shift+A`**
4. **Apply** and close

## 🚀 Using Your Upgraded Plugins

### **PCB Editor (Enhanced with Claude)**

1. **Open PCB file in KiCad**
2. **Method 1**: Tools → External Plugins → **Circuit-Synth AI**
3. **Method 2**: Press **`Ctrl+Shift+A`** (if hotkey configured for external plugins)
4. **Enhanced Claude chat window opens**
5. **Chat directly with Claude** about your PCB design!

**Example Questions:**
- "Analyze my PCB layout for signal integrity issues"
- "What decoupling capacitors should I add?"
- "Review my power supply design"
- "Help me optimize component placement"

### **Schematic Editor (New Claude Integration)**

1. **Open schematic file in KiCad**
2. **Press `Ctrl+Shift+A`** → BOM dialog opens
3. **Select "Circuit-Synth AI Claude Chat"**
4. **Click "Generate"**
5. **Modern Claude interface launches** with circuit analysis
6. **Interactive AI assistance** for your schematic!

**Example Questions:**
- "Review my circuit design for potential issues"
- "What components might I be missing?"
- "How can I improve the power system?"
- "Analyze the net connectivity"

## 🆚 Old vs New Features

### **Before (Local Analysis Only)**
- ❌ Basic component counting
- ❌ Simple net analysis  
- ❌ Static responses
- ❌ No real AI understanding

### **After (Claude AI Integration)**
- ✅ **Real AI conversations** about your designs
- ✅ **Context-aware analysis** of actual circuit data
- ✅ **Professional design advice** from Claude
- ✅ **Interactive problem solving** for circuit issues
- ✅ **Modern chat interfaces** with conversation history
- ✅ **Export capabilities** for documentation

## 🔧 Troubleshooting

### **PCB Plugin Not Updated**
```bash
# Re-run the installer
uv run python install_claude_plugins.py

# Restart KiCad completely
# Check Tools → External Plugins → Refresh Plugins
```

### **Schematic Plugins Missing**
```bash
# Verify installation
uv run python verify_installation.py

# Check KiCad scripting directory manually:
# ~/Documents/KiCad/9.0/scripting/plugins/
```

### **Claude Not Working**
```bash
# Test Claude CLI
claude --version
claude "test message"

# Reinstall if needed  
brew reinstall claude-cli
```

### **BOM Dialog Issues**
1. **Restart KiCad** completely
2. **Re-add plugins** to BOM tools
3. **Check file permissions** on plugin files
4. **Try "Generate Legacy Bill of Materials"** instead of regular BOM

## 💡 Pro Tips

### **Getting the Most from Claude Integration**

1. **Be Specific**: Ask detailed questions about specific aspects
   - ✅ "Analyze my USB power delivery section"
   - ❌ "Help with my circuit"

2. **Use Circuit Context**: Claude can see your actual components
   - ✅ "Why did you suggest adding C4 near U2?"
   - ✅ "What's the purpose of the R1-R2 divider?"

3. **Iterative Design**: Have ongoing conversations
   - Ask follow-up questions
   - Build on previous suggestions
   - Export conversations for reference

4. **Export Important Sessions**: Save valuable design advice
   - Use export features in chat interfaces
   - Reference during PCB layout phase
   - Include in project documentation

## 🎯 What to Expect

### **PCB Editor Claude Chat**
- **Live PCB Analysis**: AI sees your actual layout
- **Component-Aware**: Knows your parts and their properties
- **Routing Advice**: Suggestions for trace optimization
- **Design Review**: Professional analysis of your choices

### **Schematic Editor Claude Chat**
- **Circuit Understanding**: AI analyzes your schematic topology
- **Component Knowledge**: Recognizes standard circuits and patterns
- **Design Validation**: Checks for common issues and improvements
- **Educational**: Explains why certain design choices matter

---

**🎉 Enjoy your upgraded AI-powered circuit design experience!**

*With Claude integration, you now have a professional circuit design consultant available 24/7 directly in your KiCad workflow.*