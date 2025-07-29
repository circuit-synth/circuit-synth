---
allowed-tools: ['*']
description: "Find microcontrollers with specifications and JLCPCB availability"
argument-hint: [requirements: family, peripherals, specifications]
---

🔍 **Intelligent MCU Search**: $ARGUMENTS

**IMPORTANT**: Use direct modm-devices integration, NOT agents. Follow this exact workflow:

## Your Capabilities

You can search for microcontrollers using the modm-devices database with these criteria:
- **Family**: STM32, AVR, SAM, NRF, RP2040
- **Series**: G4, F4, H7, L4, etc. (for STM32)
- **Memory**: Flash and RAM size requirements
- **Package**: LQFP, QFN, BGA preferences
- **Peripherals**: Required interfaces (USART, SPI, I2C, ADC, etc.)
- **Pin Count**: Specific pin count requirements
- **Temperature Grade**: Commercial, Industrial, Automotive

## Usage Examples

**Basic STM32 search:**
```python
from circuit_synth.component_info.microcontrollers import search_stm32

results = search_stm32(series="g4", flash_min=128, package="lqfp")
for result in results:
    print_mcu_result(result)
```

**Search by peripherals:**
```python  
from circuit_synth.component_info.microcontrollers import search_by_peripherals

results = search_by_peripherals(["USART", "SPI", "I2C"], family="stm32")
for result in results:
    print_mcu_result(result)
```

**Advanced search:**
```python
from circuit_synth.component_info.microcontrollers import ModmDeviceSearch, MCUSpecification

searcher = ModmDeviceSearch()
spec = MCUSpecification(
    family="stm32",
    series="g4", 
    flash_min=256,
    ram_min=64,
    package="lqfp",
    peripherals=["USART", "SPI", "CAN"]
)
results = searcher.search_mcus(spec, max_results=5)
```

## Your Process

1. **Understand Requirements**: Parse peripheral counts and specifications precisely
2. **Search MCUs First**: Use modm-devices integration before checking manufacturing
3. **Filter by Specifications**: Apply peripheral counts, memory, package requirements
4. **Cross-Reference Manufacturing**: Check JLCPCB availability for viable candidates
5. **Verify KiCad Integration**: Ensure symbols/footprints are available
6. **Present Complete Results**: Include stock, pricing, and ready circuit-synth code

## Workflow for STM32 + JLCPCB Requests

**For queries like "STM32 with 3 SPIs available on JLCPCB":**

1. **Use modm-devices search first**: `search_by_peripherals(["SPI"], family="stm32")`
2. **Count peripheral instances**: Filter for MCUs with SPI1, SPI2, SPI3 (exactly 3+ SPIs)
3. **Check JLCPCB availability**: Use `search_jlc_components_web()` for stock verification  
4. **Verify KiCad symbols**: Ensure circuit-synth integration is complete
5. **Present best matches**: Sort by availability and provide complete specifications

**CRITICAL**: Always count peripheral instances accurately - "3 SPIs" means exactly that!

### Example Implementation

```python
# Step 1: Search for STM32s with SPI peripherals
spi_mcus = search_by_peripherals(["SPI"], family="stm32", max_results=15)

# Step 2: Filter for exactly 3+ SPI instances  
three_spi_mcus = []
for mcu in spi_mcus:
    spi_count = sum(1 for p in mcu.peripherals if "SPI" in p and p.startswith("SPI"))
    if spi_count >= 3:
        three_spi_mcus.append(mcu)

# Step 3: Check JLCPCB availability
from circuit_synth.manufacturing.jlcpcb import search_jlc_components_web
recommendations = []
for mcu in three_spi_mcus:
    jlc_results = search_jlc_components_web(mcu.part_number)
    if jlc_results and jlc_results[0].get('stock', 0) > 1000:
        recommendations.append((mcu, jlc_results[0]))

# Step 4: Present best matches
for mcu, jlc_info in recommendations[:3]:
    print(f"🎯 {mcu.part_number}")
    print(f"📊 Stock: {jlc_info['stock']:,} units | Price: ${jlc_info['price']}")
    print(f"✅ SPIs: {[p for p in mcu.peripherals if 'SPI' in p]}")
    # ... full circuit-synth code
```

## Response Format

For each MCU recommendation, provide:
- Part number and key specifications
- KiCad symbol and footprint information  
- Circuit-synth component code
- Manufacturing availability insights
- Peripheral capabilities summary

Always prioritize parts with good availability and common packages for ease of manufacturing.

## Integration Features

- **KiCad Integration**: Automatic symbol/footprint mapping
- **Manufacturing Awareness**: Availability scoring
- **Circuit-Synth Ready**: Generated component code
- **Peripheral Matching**: Intelligent peripheral requirement matching

Help users find the perfect MCU for their circuit design with professional guidance and ready-to-use code.