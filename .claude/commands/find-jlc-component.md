---
allowed-tools: Task
description: Find available components from JLCPCB with KiCad symbol compatibility
argument-hint: [component type] [optional: package preference]
---

Find available components from JLCPCB and verify KiCad symbol availability for: **$ARGUMENTS**

**Usage Examples:**
- `/find-jlc-component STM32G4` - Find available STM32G4 microcontrollers
- `/find-jlc-component LM358 SOIC` - Find LM358 op-amps in SOIC package
- `/find-jlc-component USB-C` - Find USB-C connectors with high availability
- `/find-jlc-component voltage regulator SOT23` - Find SOT23 voltage regulators

**What this command does:**
1. **Search JLCPCB** for components matching your criteria
2. **Check stock levels** and pricing information  
3. **Verify KiCad symbols** are available for the components
4. **Provide recommendations** with both manufacturability and design feasibility
5. **Suggest alternatives** if primary choice has low stock

**Output includes:**
- Component part numbers with stock quantities
- JLCPCB pricing and availability status
- Matching KiCad symbols and footprints
- Manufacturability score (0-1 scale)
- Design-ready component recommendations

**For circuit-synth integration:**
```python
# Use the recommended components directly in your circuit
from circuit_synth import Component

# Example output shows: STM32G431CBT6 available with MCU_ST_STM32G4 symbol
mcu = Component(
    symbol="MCU_ST_STM32G4:STM32G431CBT6",
    ref="U1", 
    footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
)
```

This command bridges the gap between component availability and circuit design, ensuring your chosen parts are both manufacturable and supported in KiCad.