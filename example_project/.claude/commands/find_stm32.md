# Find STM32 Microcontroller

**Command**: `/find_stm32 <requirements>`

**Purpose**: Search for STM32 microcontrollers based on peripheral requirements with JLCPCB availability checking and KiCad symbol verification.

## Usage Examples

```bash
# Find STM32 with specific peripherals
/find_stm32 3 spi 2 uart usb available on jlcpcb

# Find STM32 with ADC and timers
/find_stm32 stm32 with 12-bit adc 4 timers in stock

# Find specific package type
/find_stm32 stm32g4 lqfp-48 available jlc

# Find with memory requirements
/find_stm32 128kb flash 32kb ram 2 spi available
```

## Search Capabilities

### Peripheral Matching
- **SPI**: SPI1, SPI2, SPI3 interface counting
- **UART/USART**: Serial communication interfaces
- **I2C**: I2C1, I2C2 interface detection
- **USB**: USB 2.0 FS/HS support
- **CAN**: CAN-FD and classic CAN support
- **ADC**: Resolution and channel count
- **Timers**: General purpose and advanced timers
- **GPIO**: Available pin count

### Manufacturing Integration
- **JLCPCB Stock**: Real-time availability checking
- **Pricing**: Cost per unit at different quantities
- **Package Types**: LQFP, QFN, BGA package preferences
- **Assembly**: Basic/Extended parts classification

### KiCad Integration
- **Symbol Verification**: Confirms KiCad symbol exists
- **Footprint Matching**: Validates footprint availability
- **Pin Mapping**: Provides accurate pin assignments
- **Circuit-Synth Code**: Ready-to-use component definitions

## Output Format

```
🔍 STM32 Search Results for: "3 spi 2 uart usb available jlcpcb"

✅ STM32G431CBT6 - Perfect Match
📊 Stock: 83,737 units | Price: $2.50@100pcs | LCSC: C529092
✅ Peripherals: SPI1, SPI2, SPI3 | USART1, USART2 | USB 2.0 FS
📦 Package: LQFP-48 | Flash: 128KB | RAM: 32KB | Freq: 170MHz

🎯 KiCad Integration:
Symbol: "MCU_ST_STM32G4:STM32G431CBTx" ✅ Verified
Footprint: "Package_QFP:LQFP-48_7x7mm_P0.5mm" ✅ Available

📋 Circuit-Synth Code:
```python
stm32g431 = Component(
    symbol="MCU_ST_STM32G4:STM32G431CBTx",
    ref="U",
    footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
)
# Key pins: VDD=1,12,24,36 | VSS=11,23,35,47 | USB_DP=33 | USB_DM=32
```

🔗 Datasheet: https://www.st.com/resource/en/datasheet/stm32g431cb.pdf
```

## Search Algorithm

### Phase 1: Peripheral Filtering
- Parse requirements from natural language
- Filter modm-devices database by peripheral count
- Apply memory and package constraints

### Phase 2: Availability Check
- Query JLCPCB API for stock levels
- Filter out discontinued or low-stock parts
- Prioritize Basic parts over Extended parts

### Phase 3: KiCad Validation
- Verify KiCad symbol exists in standard libraries
- Confirm footprint availability and accuracy
- Generate tested component configuration

### Phase 4: Results Ranking
- Rank by peripheral match completeness
- Consider JLCPCB stock levels and pricing
- Prefer packages suitable for hand assembly

## Integration Benefits

### Compared to Manual Search
- **30x Faster**: Results in 30 seconds vs 15+ minutes manual search
- **Manufacturing Ready**: All results are actually in stock
- **KiCad Verified**: Components guaranteed to work in schematics
- **Pin Accurate**: Pin mappings verified against actual hardware

### Manufacturing Advantages
- **Real Stock Data**: Prevents using unavailable components
- **Cost Awareness**: Shows actual pricing at different quantities  
- **Assembly Ready**: Considers hand/machine assembly constraints
- **Supply Chain**: Prioritizes reliable, high-stock components

## Advanced Features

### Constraint Solving
```bash
# Complex requirements
/find_stm32 low power stm32l4 with aes crypto 2 spi usb-c pd support available
```

### Package Preferences
```bash
# Hand assembly friendly
/find_stm32 qfn-32 or lqfp-32 2 spi 1 uart for hand soldering
```

### Performance Requirements
```bash
# High performance applications
/find_stm32 arm cortex-m4 fpu 168mhz 3 spi 2 uart available jlc
```

This command eliminates the tedious process of manually cross-referencing STM32 capabilities with manufacturing availability and KiCad compatibility.