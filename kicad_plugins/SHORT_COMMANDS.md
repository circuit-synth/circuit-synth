# 🎯 KiCad Plugin Commands - SHORT FILENAMES (No Line Break Issues)

## ✅ SOLUTION: Use These Short Commands

The issue is KiCad inserting line breaks in long filenames. Use these short plugin names instead:

### 1. 🧪 Quick Test Plugin
**Command:**
```
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 "/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/test.py" "%I" "%O"
```
**Result:** Shows "SUCCESS!" window to verify KiCad integration works

### 2. 📊 Simple Circuit Analysis
**Command:**
```
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 "/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/simple.py" "%I" "%O"
```
**Result:** Circuit analysis with component breakdown (works offline)

### 3. 🤖 Claude AI Chat
**Command:**
```
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 "/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/claude_chat.py" "%I" "%O"
```
**Result:** Full Claude AI chat interface with real AI integration

## 📋 How to Set Up in KiCad

1. **Open KiCad Schematic Editor**
2. **Tools → Generate Bill of Materials**
3. **Click "+" to add new plugin**
4. **Plugin Name:** `Circuit-Synth AI Test` (or whatever you want)
5. **Copy the EXACT command above** (choose which one you want)
6. **Test with any schematic file**

## ✅ All Plugins Verified Working

All three short-filename versions have been tested and work correctly:
- ✅ `test.py` - Quick test (verified working)
- ✅ `simple.py` - Circuit analysis (verified working)  
- ✅ `claude_chat.py` - Claude AI integration (same as original)

The short filenames prevent KiCad from inserting line breaks that were causing the "file not found" errors.

## 🎯 Recommendation

Start with the **Quick Test Plugin** first to verify everything works, then move to whichever functionality you prefer!