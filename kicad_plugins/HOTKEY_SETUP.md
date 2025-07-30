# KiCad Hotkey Setup for Circuit-Synth AI Plugins

This guide shows how to set up custom keyboard shortcuts to quickly launch Circuit-Synth AI plugins.

## 🎯 Goal

Set up hotkeys to launch:
- **PCB Plugin**: Instant access from PCB editor
- **Schematic Chat Plugin**: Quick AI chat from schematic editor  
- **Analysis Tools**: Fast circuit analysis workflow

## ⌨️ KiCad Hotkey Configuration

### **Method 1: Built-in Hotkey Editor (Recommended)**

1. **Open KiCad Schematic Editor**
2. **Go to Preferences → Hotkeys**
3. **Search for relevant commands**:
   - Search: "Generate Legacy Bill of Materials" ← **This is the exact command!**
   - Search: "External Plugins" (for PCB editor)
4. **Assign custom hotkeys**:
   - **Recommended**: `Ctrl+Shift+A` for AI Assistant (Legacy BOM)
   - **Alternative**: `Ctrl+Alt+C` for Chat Interface
   - **Alternative**: `F12` for Quick Analysis

### **Method 2: Direct Hotkey File Edit**

KiCad stores hotkeys in configuration files:

**macOS**:
```
~/Library/Preferences/kicad/9.0/user.hotkeys
```

**Linux**:
```
~/.config/kicad/9.0/user.hotkeys
```

**Windows**:
```
%APPDATA%\kicad\9.0\user.hotkeys
```

#### **Custom Hotkey Entries**

Add these lines to your `user.hotkeys` file:

```ini
# Circuit-Synth AI Hotkeys
generate_legacy_bom|Ctrl+Shift+A
external_plugins|Ctrl+Alt+P
```

## 🚀 Recommended Hotkey Setup

### **For Schematic Editor**:
- **`Ctrl+Shift+A`**: Generate Legacy Bill of Materials → Launch AI Chat
- **`F11`**: Quick circuit analysis  
- **`Ctrl+Alt+R`**: Generate analysis report

### **For PCB Editor**:
- **`Ctrl+Shift+A`**: External Plugins → Circuit-Synth AI
- **`F11`**: Quick PCB analysis
- **`Ctrl+Alt+O`**: Optimization suggestions

## 📋 Plugin Setup for Hotkeys

### **Step 1: Add Chat Plugin to BOM Tools**

1. **Open KiCad Schematic Editor**
2. **Tools → Generate Legacy Bill of Materials** ← **Use the Legacy option!**
3. **Click "+" to add plugin**
4. **Browse to**: `/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/circuit_synth_chat_plugin.py`
5. **Nickname**: "Circuit-Synth AI Chat"
6. **Save configuration**

### **Step 2: Verify PCB Plugin**

1. **Open KiCad PCB Editor**
2. **Tools → External Plugins → Refresh Plugins**
3. **Verify "Circuit-Synth AI" appears**

### **Step 3: Test Hotkeys**

1. **Open a schematic**
2. **Press your assigned hotkey** (e.g., `Ctrl+Shift+A`)
3. **Legacy BOM dialog should open**
4. **Select "Circuit-Synth AI Chat"**
5. **Press "Generate" or Enter**
6. **🎉 Chat interface launches with circuit analysis!**

## 🔧 Advanced Hotkey Workflows

### **Workflow 1: Quick Analysis**
```
Ctrl+Shift+A → Enter → Get instant AI analysis
```

### **Workflow 2: Design Review**
```
1. Ctrl+Shift+A (Open AI Chat)
2. Type: "analyze my circuit"
3. Get comprehensive analysis
4. Ask follow-up questions
```

### **Workflow 3: Optimization Session**
```
1. F11 (Quick analysis)
2. Review suggestions
3. Ask specific optimization questions
4. Export recommendations
```

## 💡 Pro Tips

### **Muscle Memory Building**
- **Use consistent hotkeys** across KiCad editors
- **Practice the workflow**: Hotkey → Plugin Selection → Analysis
- **Create shortcuts for common questions**

### **Chat Interface Shortcuts**
Once the chat is open:
- **Enter**: Send message
- **Quick Action Buttons**: One-click common requests
- **Ctrl+S**: Export chat (when implemented)

### **Efficient Questions**
Train yourself to ask:
- "analyze power system"
- "optimize this design"  
- "component suggestions"
- "check connectivity"

## 🔄 Handling Schematic Refresh Limitation

Since KiCad requires reopening schematics to see changes:

### **Workflow Strategy**:
1. **Analyze first**: Use AI to understand current design
2. **Plan changes**: Get AI recommendations  
3. **Make changes**: Edit schematic manually
4. **Re-analyze**: Run AI analysis again to verify
5. **Iterate**: Repeat until optimized

### **Chat Session Approach**:
1. **Long analysis session**: Keep chat open while working
2. **Document changes**: Ask AI to track what you're doing
3. **Export session**: Save recommendations for reference
4. **Re-run after changes**: Quick analysis to verify improvements

## ⚡ Testing Your Setup

### **Quick Test Checklist**:
- [ ] **Hotkey works**: Press assigned key in schematic editor
- [ ] **BOM dialog opens**: Dialog appears quickly
- [ ] **Plugin listed**: "Circuit-Synth AI Chat" appears in list
- [ ] **Chat launches**: GUI interface opens with analysis
- [ ] **Interactive**: Can type questions and get responses
- [ ] **Actions work**: Quick action buttons function

### **Performance Test**:
- [ ] **Launch time**: Should open in < 3 seconds
- [ ] **Analysis speed**: Component analysis completes quickly
- [ ] **UI responsiveness**: Chat interface is smooth
- [ ] **Memory usage**: No performance issues

## 🛠️ Troubleshooting Hotkeys

### **Hotkey Not Working**
1. **Check KiCad version**: Ensure you're using KiCad 9.0+
2. **Verify hotkey file**: Check `user.hotkeys` file exists and has correct syntax
3. **Restart KiCad**: Hotkey changes require restart
4. **Check conflicts**: Ensure hotkey isn't already assigned

### **Plugin Not Launching**
1. **Verify plugin installation**: Check file exists and is executable
2. **Check BOM tool setup**: Ensure plugin is added to BOM generators
3. **Test manually**: Try launching from BOM dialog directly
4. **Check permissions**: Ensure plugin file is readable

### **Chat Interface Issues**
1. **Check tkinter**: Ensure GUI library is available
2. **Test standalone**: Run plugin directly from command line
3. **Check analysis data**: Verify schematic can be parsed

## 📚 Additional Resources

- **KiCad Hotkey Documentation**: Official KiCad docs on keyboard shortcuts
- **Community Hotkey Configs**: Shared configurations from KiCad community
- **Plugin Development**: How to create custom KiCad plugins
- **Circuit-Synth Docs**: Full documentation for all features

---

**🎯 Result**: Lightning-fast access to AI-powered circuit analysis with custom hotkeys!