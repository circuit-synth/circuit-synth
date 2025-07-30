# Circuit-Synth AI Schematic Plugin Installation

This guide shows how to install the Circuit-Synth AI plugin for KiCad's **Schematic Editor** using the brilliant "BOM backdoor" method discovered by BlackCoffee on the KiCad forums.

## 🎯 The "BOM Backdoor" Method

Since KiCad's schematic editor doesn't support ActionPlugins like the PCB editor, we use a clever workaround:

- **KiCad's BOM tool** can run any Python script
- **The BOM tool passes schematic data** (as XML netlist) to the script
- **Our script analyzes the schematic** and shows AI insights instead of generating a BOM
- **Result**: AI-powered schematic analysis directly from the schematic editor!

## 📦 Installation Steps

### Step 1: Copy the Plugin
The plugin is already copied to:
```
~/Documents/KiCad/9.0/scripting/plugins/circuit_synth_bom_plugin.py
```

### Step 2: Add to KiCad's BOM Tools
1. **Open KiCad Schematic Editor**
2. **Open any schematic file** (.kicad_sch)
3. **Go to Tools → Generate Bill of Materials**
4. **Click the "+" button** to add a new BOM plugin
5. **Browse to**: `/Users/shanemattner/Documents/KiCad/9.0/scripting/plugins/circuit_synth_bom_plugin.py`
6. **Give it a name**: "Circuit-Synth AI Analysis"
7. **Click OK**

### Step 3: Configure the Plugin
- **Nickname**: `Circuit-Synth AI`
- **Command line**: The path should auto-populate
- **Output file**: Can be anything (e.g., `analysis_output.txt`)

## 🚀 How to Use

### From Schematic Editor:
1. **Open your schematic** in KiCad Schematic Editor
2. **Tools → Generate Bill of Materials**
3. **Select "Circuit-Synth AI Analysis"** from the plugin list
4. **Click "Generate"**
5. **A GUI window will pop up** with AI-powered schematic analysis!

### What You'll See:
- **Component count and analysis**
- **Component types breakdown** 
- **Net analysis and connections**
- **AI-powered design insights**
- **Optimization recommendations**

## ✨ Features

- 📊 **Component Analysis**: Counts, types, libraries used
- 🔗 **Net Analysis**: Connection mapping and complexity
- 🤖 **AI Insights**: Design complexity assessment
- 💡 **Recommendations**: Suggestions for improvement
- 🎨 **GUI Interface**: Easy-to-read analysis results
- 📝 **Report Generation**: Creates summary file

## 🔧 Advanced Usage

### Command Line Testing:
```bash
# Test with a KiCad netlist XML file
python circuit_synth_bom_plugin.py netlist.xml output.txt
```

### Customization:
- Edit the plugin file to add more AI analysis features
- Modify the GUI layout or analysis algorithms
- Integrate with external AI services

## 🎉 Result

You now have **AI-powered circuit analysis directly in KiCad's Schematic Editor**! 

This bypasses the limitation that eeschema doesn't support ActionPlugins by using the BOM tool as a "backdoor" to run our analysis code.

## 🙏 Credits

- **BlackCoffee** on KiCad forums for discovering the BOM backdoor method
- **KiCad community** for the innovative workarounds
- **Circuit-Synth project** for the AI analysis implementation