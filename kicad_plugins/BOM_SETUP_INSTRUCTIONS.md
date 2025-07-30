# KiCad BOM Plugin Setup Instructions

## 🎯 Correct Plugin Paths and Commands

You're using the right Python path! Here are the correct configurations for each plugin:

### **🤖 Claude-Integrated Plugin (Recommended)**

**Plugin Setup:**
1. **Tools → Generate Bill of Materials**
2. **Click "+" to add plugin**
3. **Plugin Info:**
   - **Name/Nickname**: `Circuit-Synth AI Claude Chat`
   - **Plugin Path**: `/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/circuit_synth_claude_schematic_plugin.py`
   - **Command Line**: 
     ```
     /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 "/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/circuit_synth_claude_schematic_plugin.py" "%I" "%O"
     ```

**✅ This gives you:**
- Real Claude AI chat interface
- Context-aware circuit analysis
- Modern GUI with conversation history
- Export capabilities

---

### **📱 Enhanced Chat Plugin (Alternative)**

**Plugin Setup:**
- **Name/Nickname**: `Circuit-Synth AI Enhanced Chat`
- **Plugin Path**: `/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/circuit_synth_chat_plugin.py`
- **Command Line**: 
  ```
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 "/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/circuit_synth_chat_plugin.py" "%I" "%O"
  ```

**✅ This gives you:**
- Enhanced chat interface (no Claude integration)
- Simulated AI responses with circuit analysis
- Modern GUI with quick actions

---

### **📊 Basic Analysis Plugin (What you currently have)**

**Plugin Setup:**
- **Name/Nickname**: `Circuit-Synth AI Basic`
- **Plugin Path**: `/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/circuit_synth_bom_plugin.py`
- **Command Line**: 
  ```
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 "/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/circuit_synth_bom_plugin.py" "%I" "%O"
  ```

**✅ This gives you:**
- Basic circuit analysis
- Simple GUI with component breakdown
- No AI integration

---

## 🚀 Recommended Setup

**For the best experience, set up the Claude-integrated plugin:**

1. **Remove** the current basic plugin from BOM tools
2. **Add** the Claude-integrated plugin using the path above
3. **Test** by pressing your hotkey (`Ctrl+Shift+A`) in schematic editor
4. **Select** "Circuit-Synth AI Claude Chat" from the list
5. **Click "Generate"** → Full Claude AI interface opens!

## 🔧 Troubleshooting Your Current Setup

**If the basic plugin isn't working:**

1. **Check File Permissions:**
   ```bash
   ls -la /Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/circuit_synth_bom_plugin.py
   
   # Should show executable permissions (-rwxr-xr-x)
   # If not, fix with:
   chmod +x /Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/circuit_synth_bom_plugin.py
   ```

2. **Test Plugin Directly:**
   ```bash
   # Create a test netlist file
   cd /tmp
   echo '<?xml version="1.0"?><export><design><source>test.kicad_sch</source></design><components></components><nets></nets></export>' > test.xml
   
   # Test the plugin
   /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 "/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/circuit_synth_bom_plugin.py" test.xml output.txt
   ```

3. **Check KiCad Error Console:**
   - In KiCad: **Tools → Scripting Console**
   - Look for any error messages when running the plugin

## 🎯 Upgrade Recommendation

**Instead of troubleshooting the basic plugin, I recommend upgrading to the Claude-integrated version:**

1. **The Claude plugin includes everything** the basic plugin does, plus real AI
2. **Better user interface** with modern chat-style interaction
3. **Professional analysis** with context awareness
4. **Future-proof** with ongoing AI improvements

**Quick upgrade:**
```bash
cd /Users/shanemattner/Desktop/Circuit_Synth2/submodules/circuit-synth/kicad_plugins
uv run python install_claude_plugins.py
uv run python verify_installation.py
```

Then set up the Claude plugin in KiCad BOM tools using the paths above.

## 💡 Pro Tips

1. **Use the Claude plugin** as your primary tool
2. **Keep the basic plugin** as a backup (no internet required)
3. **Set up both** with different nicknames so you can choose
4. **Use hotkeys** for instant access (`Ctrl+Shift+A`)

---

**🎯 Your current path is correct - just upgrade to the Claude version for the best experience!**