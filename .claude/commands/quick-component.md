---
allowed-tools: Task
description: Instantly find and generate circuit-synth code for any component with one command
argument-hint: [component search]
---

Instantly find and generate ready-to-use circuit-synth code for: **$ARGUMENTS**

**Super Fast Component Finding:**

This command gives you immediate results in one step:
1. Searches JLCPCB for high-availability components
2. Verifies KiCad symbol/footprint compatibility  
3. Generates ready-to-paste circuit-synth code
4. Shows stock levels and manufacturability score

**One-Line Examples:**
- `/quick-component STM32G4` → Get best STM32G4 with code
- `/quick-component 10K 0603` → Get 10K resistor in 0603 package  
- `/quick-component USB-C` → Get USB-C connector ready to use
- `/quick-component LM358` → Get dual op-amp with connections
- `/quick-component AMS1117` → Get 3.3V regulator circuit

**Instant Output Format:**
```
🎯 STM32G431CBT6 - 83,737 units in stock | Score: 0.95/1.0
💰 $2.50 @ 100pcs | ✅ Basic part (optimal for assembly)

📋 Ready Circuit-Synth Code:
mcu = Component(
    symbol="MCU_ST_STM32G4:STM32G431CBT6",
    ref="U1",
    footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
)
```

**Smart Features:**
- **Highest Stock First** - Always recommends most available parts
- **KiCad Verified** - Only shows components with confirmed symbols
- **Production Ready** - Focuses on basic/preferred parts when possible
- **Copy-Paste Ready** - Code works immediately in your circuits

**Perfect For:**
- ⚡ Rapid prototyping - Get components fast
- 🎯 Production designs - High-availability parts only  
- 🔧 Learning - See proper circuit-synth syntax
- 📋 BOM planning - Real stock levels and pricing

**Time Saver:**
Instead of manually searching JLCPCB, then finding KiCad symbols, then writing Component code - get everything in one command that takes seconds instead of minutes!