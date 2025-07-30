# 🔧 CLEAN KICAD PLUGIN SETUP - COPY EXACTLY

## ❌ The Problem
Your command line has invisible line breaks that are corrupting the paths:
```
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Cu   rrent/bin/python3
```
Notice the spaces in "Cu   rrent" - this breaks the command.

## ✅ EXACT COMMAND LINES TO USE

### 1. Quick Test Plugin (Test This First)
```
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 "/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/quick_test_plugin.py" "%I" "%O"
```

### 2. Simple Circuit Analysis Plugin (Reliable)
```
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 "/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/circuit_synth_simple.py" "%I" "%O"
```

### 3. Claude-Integrated Plugin (Advanced)
```
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 "/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/circuit_synth_claude_schematic_plugin.py" "%I" "%O"
```

## 📋 SETUP INSTRUCTIONS

1. **Open KiCad Schematic Editor**
2. **Tools → Generate Bill of Materials**
3. **Click "+" to add plugin**
4. **COPY THE EXACT COMMAND LINE ABOVE** (no line breaks!)
5. **Set Plugin Name**: `Circuit-Synth AI Test` (or whatever you prefer)
6. **Test with any schematic**

## ⚠️ CRITICAL: NO LINE BREAKS
- The command must be **ONE CONTINUOUS LINE**
- Do not press Enter in the middle of the command
- Copy the entire command at once
- If it wraps visually in the dialog, that's OK - just don't add manual breaks

## 🎯 Expected Results

**Quick Test Plugin**: Shows "SUCCESS!" window
**Simple Plugin**: Shows circuit analysis with component breakdown  
**Claude Plugin**: Opens full Claude AI chat interface

All plugins should create an output file automatically, preventing the "Failed to create file" error.