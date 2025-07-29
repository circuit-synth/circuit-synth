---
allowed-tools: Task
description: Interactive component selection wizard that finds JLCPCB parts and generates ready-to-use circuit-synth code
argument-hint: [component description]
---

Launch an interactive component selection wizard for: **$ARGUMENTS**

**What this wizard does:**
1. **Understands your needs** - Describe what you want in plain English
2. **Searches JLCPCB** - Finds available components with stock and pricing  
3. **Verifies KiCad compatibility** - Ensures symbols and footprints exist
4. **Generates ready code** - Provides complete circuit-synth Component definitions
5. **Suggests alternatives** - Shows multiple options with trade-offs

**Usage Examples:**
- `/component-wizard microcontroller for IoT project with WiFi` 
- `/component-wizard voltage regulator 5V to 3.3V high efficiency`
- `/component-wizard operational amplifier low noise audio application`
- `/component-wizard USB-C connector for power and data`
- `/component-wizard 10K resistor 0603 package`

**Interactive Process:**

The wizard will guide you through:

1. **Requirements Clarification:**
   - Electrical specifications (voltage, current, frequency, etc.)
   - Package preferences (size constraints, assembly capabilities)
   - Special requirements (temperature range, precision, etc.)

2. **Component Search & Analysis:**
   - Real-time JLCPCB inventory check
   - Stock availability and pricing analysis
   - KiCad symbol/footprint verification

3. **Recommendation with Trade-offs:**
   ```
   🎯 Primary Recommendation: STM32G431CBT6
   ✅ Stock: 83,737 units | Score: 0.95/1.0 | Price: $2.50 @ 100pcs
   📦 Package: LQFP-48 (7x7mm) | Library: Basic (optimal for assembly)
   🔧 KiCad: MCU_ST_STM32G4:STM32G431CBT6 ✅ Verified
   
   Alternative Options:
   🔸 STM32G471CBT6 - Higher performance, $2.75, 45K units
   🔸 STM32G030C8T6 - Lower cost, $1.20, 54K units
   ```

4. **Ready Circuit-Synth Code:**
   ```python
   # STM32G431CBT6 - 83,737 units in stock
   # LCSC: C123456 | Price: $2.50 @ 100pcs | Score: 0.95/1.0
   mcu = Component(
       symbol="MCU_ST_STM32G4:STM32G431CBT6",
       ref="U1", 
       footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
   )
   ```

**Advanced Features:**

- **Package Constraints:** "Must fit in 5x5mm area"
- **Performance Requirements:** "Need 100MHz+ CPU with USB"  
- **Cost Optimization:** "Cheapest option with >1000 units stock"
- **Alternative Analysis:** "Show 3 options at different price points"
- **Inventory Alerts:** "Warn if stock <5000 units"

**Smart Recommendations:**

The wizard provides intelligent suggestions based on:
- **Manufacturability:** High stock levels, basic/preferred parts
- **Design Integration:** Verified KiCad symbols and footprints
- **Cost Effectiveness:** Best value across quantity breaks
- **Assembly Compatibility:** JLCPCB assembly capabilities
- **Project Context:** Typical requirements for your application

**Output Formats:**

Choose from multiple output formats:
- **Circuit-Synth Code** - Ready to paste into your design
- **Component Table** - Comparison of alternatives with specs
- **BOM Entry** - LCSC part numbers with pricing for ordering
- **Design Notes** - Recommendations and considerations

This wizard makes component selection effortless - just describe what you need and get production-ready components with all the integration details handled automatically.