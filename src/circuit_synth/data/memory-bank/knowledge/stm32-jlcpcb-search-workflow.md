# STM32 + JLCPCB Search Workflow Guide

## The Right Way to Find STM32 Components

When a user asks for "STM32 with X SPIs available on JLCPCB", follow this **systematic approach**:

### Step 1: Use MODM-Devices Search First
```python
# Search for STM32s with specific peripheral requirements
from circuit_synth.component_info.microcontrollers import search_by_peripherals

results = search_by_peripherals(["SPI"], family="stm32", max_results=10)
```

### Step 2: Filter for Peripheral Count
- Look for MCUs that have **multiple instances** of the required peripheral
- For "3 SPIs": Find MCUs with SPI1, SPI2, SPI3 (or more)
- Check the `peripherals` list in each `MCUSearchResult`

### Step 3: Cross-Reference with JLCPCB
```python
from circuit_synth.manufacturing.jlcpcb import search_jlc_components_web

# For each promising STM32, check JLCPCB availability
for result in promising_mcus:
    jlc_results = search_jlc_components_web(result.part_number)
    if jlc_results and jlc_results[0].get('stock', 0) > 1000:
        # Good availability - include in recommendations
```

### Step 4: Verify KiCad Integration
- Check that `result.kicad_symbol` and `result.kicad_footprint` are populated
- Use `/find-symbol` command if needed to verify symbol availability

## Example Complete Workflow

```python
# 1. Search for STM32s with SPI peripherals
spi_mcus = search_by_peripherals(["SPI"], family="stm32", max_results=15)

# 2. Filter for 3+ SPI instances
three_spi_mcus = []
for mcu in spi_mcus:
    spi_count = sum(1 for p in mcu.peripherals if "SPI" in p)
    if spi_count >= 3:
        three_spi_mcus.append(mcu)

# 3. Check JLCPCB availability for each
recommendations = []
for mcu in three_spi_mcus:
    jlc_results = search_jlc_components_web(mcu.part_number)
    if jlc_results:
        stock = jlc_results[0].get('stock', 0)
        price = jlc_results[0].get('price', 0)
        if stock > 1000:  # Good availability
            mcu.jlc_stock = stock
            mcu.jlc_price = price
            recommendations.append(mcu)

# 4. Present best options
recommendations.sort(key=lambda x: x.jlc_stock, reverse=True)
```

## Key Success Factors

1. **Don't overthink it**: Use our existing modm-devices integration first
2. **Sequential approach**: MCU search → availability check → KiCad verification
3. **Practical filtering**: Focus on stock levels > 1000 units for production viability
4. **Complete results**: Always provide circuit-synth code and manufacturing details

## Common Mistakes to Avoid

❌ **Don't start with JLCPCB search**: Their search is less precise for technical specs
❌ **Don't ignore peripheral counts**: "3 SPIs" means exactly that - count them
❌ **Don't skip KiCad verification**: Ensure symbols/footprints exist
❌ **Don't provide incomplete answers**: Always include stock, price, and code

## Template Response Format

```
🎯 **STM32G431CBT6** - Perfect match found!
📊 Stock: 83,737 units | Price: $2.50@100pcs | LCSC: C529092
✅ 3 SPIs: SPI1, SPI2, SPI3 
📦 LQFP-48 package | 128KB Flash, 32KB RAM

📋 Ready Circuit-Synth Code:
stm32g431 = Component(
    symbol="MCU_ST_STM32G4:STM32G431CBTx",
    ref="U",
    footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
)
```

This workflow ensures accurate, complete, and actionable results for users.