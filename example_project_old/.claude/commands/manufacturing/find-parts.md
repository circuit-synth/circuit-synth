---
allowed-tools: Task, WebSearch, Read, Write, Bash, Grep
description: Search for components across multiple suppliers (JLCPCB, DigiKey) with KiCad integration
argument-hint: [component specification]
---

Search for components across multiple suppliers with manufacturing and KiCad integration: **$ARGUMENTS**

## Usage Examples

```bash
# Basic component search
/find-parts 0.1uF 0603 X7R

# Supplier-specific search
/find-parts STM32F407 --source jlcpcb
/find-parts LM358 --source digikey

# Comparative search
/find-parts 3.3V regulator --compare

# With specifications
/find-parts 10k resistor 1% 0603 --min-stock 1000
```

## Search Capabilities

### Multi-Supplier Search
- **JLCPCB**: Primary PCB assembly supplier with stock checking
- **DigiKey**: Broad component selection with detailed specs  
- **Mouser**: Alternative sourcing (future)
- **Octopart**: Aggregated search across suppliers (future)

### Component Categories
- **Passives**: Resistors, capacitors, inductors with specifications
- **Active**: ICs, transistors, diodes with parametric search
- **Connectors**: Headers, USB, power connectors with pin counts
- **Mechanical**: Switches, encoders, crystals with packages
- **Power**: Regulators, converters with efficiency data

### KiCad Integration
- **Symbol Verification**: Confirms KiCad symbol exists
- **Footprint Validation**: Checks footprint compatibility  
- **Library Mapping**: Maps manufacturer parts to KiCad components
- **Circuit-Synth Ready**: Provides ready-to-use component code

## Search Parameters

### Specification Matching
```bash
# Capacitor search with full specifications
/find-parts 22uF 25V X7R 0805 --tolerance 10%

# Resistor search with power rating
/find-parts 1k 0603 1% 0.1W --temp-coeff 100ppm

# IC search with package preferences
/find-parts op-amp rail-to-rail soic-8 --supply 3.3v
```

### Availability Filtering
```bash
# Stock level requirements
/find-parts atmega328p --min-stock 100 --max-price 5.00

# Manufacturing preferences  
/find-parts ESP32 --basic-parts-only --assembly-ready

# Lead time considerations
/find-parts crystal 16mhz --max-lead-time 7days
```

### Comparison Mode
```bash
# Compare across suppliers
/find-parts stm32f103c8t6 --compare
# Shows pricing, stock, and availability across JLCPCB, DigiKey, etc.

# Alternative component suggestions
/find-parts lm2596 --alternatives
# Finds pin-compatible and functionally equivalent parts
```

## Output Format

### Single Supplier Results
```
🔍 JLCPCB Search Results for: "0.1uF 0603 X7R"

✅ Primary Recommendation: C14663
📊 Samsung Electro-Mechanics | Stock: 52,847 | Price: $0.0027@100
📋 Specs: 0.1µF ±10% X7R 25V 0603 SMD
🎯 KiCad: Device:C → Capacitor_SMD:C_0603_1608Metric ✅

📋 Circuit-Synth Code:
```python
decoupling_cap = Component(
    symbol="Device:C",
    ref="C", 
    value="0.1uF",
    footprint="Capacitor_SMD:C_0603_1608Metric"
)
# JLCPCB: C14663 | Stock: 52k+ | Basic Part
```

🔄 Alternatives Available:
- C1525: Murata equivalent, 15k stock, $0.0031
- C57112: TDK equivalent, 8k stock, $0.0025
```

### Comparison Results
```
⚖️  Multi-Supplier Comparison: "STM32F407VET6"

🥇 JLCPCB (Recommended for Assembly)
   📦 C18584 | Stock: 1,247 | Price: $8.50@10, $7.20@100  
   ⚡ Basic Part | 2-day lead time | Assembly ready

🥈 DigiKey (High Reliability)
   📦 497-STM32F407VET6-ND | Stock: 15,680 | Price: $9.45@10, $8.21@100
   ⚡ Authentic guarantee | Same-day shipping | Full datasheet

📊 Best Choice: JLCPCB for production (assembly ready + lower cost)
     DigiKey for prototyping (immediate availability + support)
```

## Integration with Agents

### Automatic Agent Routing
The command automatically delegates to appropriate specialist agents:

```bash
# Routes to stm32-mcu-finder agent
/find-parts STM32 with 3 SPI interfaces

# Routes to jlc-parts-finder agent  
/find-parts 0.1uF capacitor --source jlcpcb

# Routes to component-guru agent
/find-parts low-noise op-amp audio --compare
```

### Manufacturing Workflow Integration
```python
# Generated code includes manufacturing notes
power_reg = Component(
    symbol="Regulator_Linear:AMS1117-3.3",
    ref="U",
    footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
)
# Manufacturing: JLCPCB C6186, Basic Part, $0.12@100
# Alternative: C347222 if primary out of stock
# Assembly: Wave soldering compatible, no special requirements
```

## Advanced Features

### Parametric Search
```bash
# Complex specifications
/find-parts op-amp "gbw > 10MHz" "vos < 1mV" soic-8 --automotive

# Power component search
/find-parts buck-converter "12V to 3.3V" "efficiency > 90%" --sync-rectifier
```

### Supply Chain Intelligence  
```bash
# Risk assessment
/find-parts critical-component --supply-chain-analysis
# Shows: lifecycle status, alternative sources, risk factors

# Volume pricing
/find-parts production-component --volume 10000
# Shows: price breaks, MOQ requirements, lead times
```

### Design Rule Integration
```bash
# DFM-aware search
/find-parts resistor-array --hand-assembly --0603-max

# Thermal considerations
/find-parts power-mosfet --thermal-analysis --heatsink-required
```

This command serves as a unified entry point for all component sourcing needs, automatically routing to the most appropriate search method and providing manufacturing-ready results with full KiCad integration.