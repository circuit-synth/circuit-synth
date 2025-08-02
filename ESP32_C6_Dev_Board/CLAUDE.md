# CLAUDE.md

Project-specific guidance for Claude Code when working with this converted circuit-synth project.

## 🚀 Project Overview

This project was **converted from an existing KiCad design** to circuit-synth format.

**Important**: The generated circuit-synth code may need manual review and adjustments:
- Component symbols and footprints may need updating
- Net connections should be verified against the original design
- Component values and references should be checked

## ⚡ Available Tools

### **Slash Commands**
- `/find-symbol STM32` - Search KiCad symbol libraries
- `/find-footprint LQFP` - Search KiCad footprint libraries
- `/analyze-design` - Analyze circuit designs

### **Specialized Agents**
- **circuit-synth** - Circuit code generation and KiCad integration  
- **simulation-expert** - SPICE simulation and validation
- **jlc-parts-finder** - JLCPCB component availability
- **orchestrator** - Master coordinator for complex projects

## 🔧 Essential Commands

```bash
# Test the converted circuit
uv run python circuit-synth/main.py

# Validate circuit-synth installation
uv run python -c "from circuit_synth import *; print('✅ Ready!')"
```

## 🎯 Conversion Review Checklist

When reviewing the converted circuit-synth code:

1. **Component Verification**:
   - Check that symbols match KiCad standard libraries
   - Verify footprints are correct for your components
   - Update component values if missing

2. **Net Connection Review**:
   - Ensure all component pins are properly connected
   - Verify net names match your design intent
   - Check for missing or incorrect connections

3. **Symbol/Footprint Updates**:
   - Use `/find-symbol` and `/find-footprint` commands
   - Replace generic symbols with specific part numbers
   - Ensure manufacturability with JLCPCB-available components

## 🚀 Getting Help

Ask for specific improvements:
```
👤 "Review this converted circuit and suggest improvements"
👤 "Find JLCPCB alternatives for components not in stock"  
👤 "Add proper decoupling capacitors to this design"
👤 "Simulate this power supply circuit for stability"
```

---

**This converted project is ready for AI-powered circuit design with Claude Code!** 🎛️
