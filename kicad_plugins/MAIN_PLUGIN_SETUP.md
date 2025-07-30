# 💬 KiCad-Claude Chat - Main Plugin Setup

## Status: ✅ PRODUCTION READY

### 🎯 Single Plugin Command (Use This One)
```bash
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 "/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/kicad_claude_chat.py" "%I" "%O"
```

### 📁 Main Plugin File
- **Location**: `/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/kicad_claude_chat.py`
- **Purpose**: Single file for all KiCad-Claude integration - we update this one only
- **Status**: Working perfectly with circuit design discussions

### ✅ Confirmed Working Features (Tested)
- **Claude CLI Discovery**: Automatically finds Claude in NVM/Node.js environments
- **Connection Testing**: Verifies both CLI version and message sending
- **Circuit Design Chat**: Real conversations about circuit topology and components
- **Extended Timeout**: 120-second timeout for complex responses
- **Error-Free Operation**: No more "Execution error" issues
- **Professional GUI**: Clean interface with status indicators

### 🎯 User Workflow
1. Open KiCad schematic
2. Tools → Generate Bill of Materials → Select `kicad_claude_chat.py` → Generate
3. Chat interface opens with circuit context
4. Ask Claude about circuit design, components, layout, debugging, etc.

### 💬 Conversation Examples That Work
- "Help me design a circuit"
- "What components do I need for a voltage divider?"
- "How do I route high-speed signals?"
- "Suggest power supply components"
- "Debug this amplifier circuit"

### 🔧 Technical Details
- **Timeout**: 120 seconds for complex responses
- **Context**: Passes KiCad project name, component count, and net information
- **Instructions**: Explicitly constrains Claude to text-only circuit design advice
- **Error Handling**: Comprehensive error handling and recovery

### 📋 Installation Requirements
- **Claude Code**: Must be installed (`npm install -g @anthropic/claude-code`)
- **Node.js**: Plugin automatically handles NVM environments
- **KiCad Version**: Tested with KiCad 9.0

**This is our main plugin - all future updates go here!**