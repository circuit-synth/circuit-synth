# Find Electronic Components

**Command**: `/find-parts <component_description> [--source <supplier>]`

**Purpose**: Universal component search across multiple suppliers with real-time pricing, availability, and KiCad compatibility verification.

## Usage Examples

```bash
# Search all suppliers (default)
/find-parts "0.1uF 0603 X7R capacitor"
/find-parts "STM32F407VGT6"
/find-parts "3.3V 1A regulator"

# Search specific supplier
/find-parts "10k resistor 1%" --source jlcpcb
/find-parts "LM358 op-amp" --source digikey
/find-parts "ESP32-S3" --source all

# Compare suppliers
/find-parts "AMS1117-3.3" --compare
/find-parts "USB-C connector" --source "jlcpcb,digikey"
```

## Supported Suppliers

### Currently Available
- **jlcpcb**: Best for PCB assembly, basic parts, integrated manufacturing
- **digikey**: Extensive catalog (8M+ parts), no minimums, fast shipping

### Coming Soon
- **mouser**: Wide selection, global distribution
- **lcsc**: JLCPCB's parent company, broader selection
- **arrow**: Enterprise focus, long-term availability
- **newark**: Element14/Farnell network
- **rs-components**: European/Asian markets
- **octopart**: Meta-search across all suppliers

## Search Parameters

### Component Types
All standard electronic components:
- Passives (resistors, capacitors, inductors)
- Semiconductors (diodes, transistors, ICs)
- Connectors (USB, headers, terminals)
- Microcontrollers (STM32, ESP32, PIC, AVR)
- Power (regulators, references, PMICs)
- Sensors (temperature, pressure, motion)
- Discrete (crystals, LEDs, switches)

### Source Options
- `--source all` (default): Search all available suppliers
- `--source jlcpcb`: JLCPCB only
- `--source digikey`: DigiKey only
- `--source "jlcpcb,digikey"`: Multiple specific suppliers
- `--compare`: Side-by-side comparison across all sources

### Filters
- `--min-stock <number>`: Minimum stock quantity
- `--max-price <price>`: Maximum unit price
- `--package <type>`: Specific package (0603, SOIC-8, etc.)
- `--in-stock`: Only show in-stock items

## Output Format

### Single Supplier Result
```
🔍 Component Search Results

Source: DigiKey
✅ 399-1096-1-ND - KEMET C0603C104K3RACTU
📊 Stock: 234,879 | MOQ: 1 | Price: $0.024@100
⚡ Specs: 0.1µF ±10% 25V X7R 0603
🎯 KiCad: Device:C | Capacitor_SMD:C_0603_1608Metric ✅

Source: JLCPCB  
✅ C14663 - Samsung CL10B104KB8NNNC
📊 Stock: 52,847 | Basic Part | Price: $0.0027@100
⚡ Specs: 0.1µF ±10% 25V X7R 0603
🎯 KiCad: Device:C | Capacitor_SMD:C_0603_1608Metric ✅
```

### Comparison View
```
📊 Component Comparison: 0.1µF 0603 X7R Capacitor

| Supplier | Part Number    | Stock    | 1pc    | 100pc  | 1000pc | Type      |
|----------|---------------|----------|--------|--------|--------|-----------|
| JLCPCB   | C14663        | 52,847   | $0.010 | $0.003 | $0.002 | Basic     |
| DigiKey  | 399-1096-1-ND | 234,879  | $0.100 | $0.024 | $0.012 | Standard  |
| Mouser   | 80-C0603C104K | 156,234  | $0.110 | $0.028 | $0.015 | Standard  |

💡 Recommendation: Use JLCPCB C14663 for production (lowest cost, basic part)
                   Use DigiKey for prototyping (cut tape available)
```

### Circuit-Synth Integration
```python
# Auto-generated component with best availability/price
cap = Component(
    symbol="Device:C",
    ref="C",
    value="0.1uF",
    footprint="Capacitor_SMD:C_0603_1608Metric",
    properties={
        # Primary source (best value)
        "JLCPCB_PN": "C14663",
        "JLCPCB_Stock": "52,847",
        # Alternative source
        "DigiKey_PN": "399-1096-1-ND", 
        "DigiKey_Stock": "234,879",
        # Selected for BOM
        "Manufacturer": "Samsung",
        "MPN": "CL10B104KB8NNNC",
        "Unit_Price": "$0.003@100"
    }
)
```

## Search Implementation

### Python Integration
```python
from circuit_synth.manufacturing import find_parts

# Search all suppliers
results = find_parts(
    query="0.1uF 0603 X7R",
    sources=["jlcpcb", "digikey"],  # or "all"
    min_stock=1000,
    in_stock_only=True
)

# Compare results
for supplier, components in results.items():
    print(f"\n{supplier}:")
    for comp in components[:3]:
        print(f"  {comp.part_number}: ${comp.price:.3f} ({comp.stock} in stock)")
```

### Advanced Multi-Source Search
```python
from circuit_synth.manufacturing import MultiSourceSearch

searcher = MultiSourceSearch()

# Find best component across all sources
best_component = searcher.find_best(
    query="STM32F407",
    criteria={
        "min_stock": 1000,
        "max_price": 10.00,
        "package": "LQFP-100"
    },
    weight_factors={
        "price": 0.4,
        "availability": 0.3,
        "supplier_reliability": 0.3
    }
)

# Get alternatives from each source
alternatives = searcher.find_alternatives_all_sources(
    reference_part=best_component,
    max_per_source=3
)
```

## Sourcing Strategy

### Intelligent Recommendations
The system automatically recommends based on your use case:

1. **Prototyping** (1-10 units)
   - Prioritize: DigiKey, Mouser (no minimums, cut tape)
   - Consider: Fast shipping over price

2. **Small Batch** (10-100 units)
   - Compare: JLCPCB basic parts vs. DigiKey pricing
   - Consider: Assembly integration if using JLCPCB

3. **Production** (100+ units)
   - Prioritize: JLCPCB (assembly integration)
   - Backup: DigiKey/Mouser for unavailable parts
   - Consider: Price breaks and lead times

4. **High Reliability**
   - Prioritize: Authorized distributors (DigiKey, Mouser)
   - Avoid: Gray market suppliers
   - Consider: Automotive/military grade options

## Multi-Supplier Benefits

### Risk Mitigation
- **Dual Sourcing**: Always have alternatives
- **Supply Chain**: Avoid single points of failure
- **Geographic**: Different regional availability

### Cost Optimization
- **Price Comparison**: Real-time across suppliers
- **Volume Breaks**: Find best quantity pricing
- **Shipping**: Factor in shipping costs/time

### Availability Assurance
- **Stock Levels**: Live inventory data
- **Lead Times**: Know delivery schedules
- **Alternatives**: Instant replacement options

## Configuration

### API Setup for Each Supplier

#### JLCPCB
```bash
# Usually works without API key (web scraping)
export JLCPCB_API_KEY="optional_key"
```

#### DigiKey
```bash
# Required for API access
python -m circuit_synth.manufacturing.digikey.config_manager
# Or set environment variables:
export DIGIKEY_CLIENT_ID="your_id"
export DIGIKEY_CLIENT_SECRET="your_secret"
```

#### Future Suppliers
Each supplier will have its own configuration:
```bash
# Mouser (coming soon)
export MOUSER_API_KEY="your_key"

# Octopart (coming soon)  
export OCTOPART_API_KEY="your_key"
```

## Cache Management

The system caches results to improve performance:

```python
from circuit_synth.manufacturing import clear_parts_cache

# Clear all supplier caches
clear_parts_cache("all")

# Clear specific supplier cache
clear_parts_cache("digikey")

# View cache statistics
from circuit_synth.manufacturing import get_cache_stats
stats = get_cache_stats()
print(f"Total cache size: {stats['total_mb']:.1f} MB")
```

## Common Use Cases

### 1. Finding Decoupling Capacitors
```bash
/find-parts "0.1uF 0603 X7R 16V ceramic" --min-stock 10000
```

### 2. Sourcing Microcontrollers
```bash
/find-parts "STM32F4 100-pin" --source all --compare
```

### 3. Power Supply Components
```bash
/find-parts "3.3V 1A LDO SOT-223" --max-price 2.00
```

### 4. Verifying Availability Before Design
```bash
/find-parts "ESP32-S3-WROOM" --min-stock 1000 --source "jlcpcb,digikey"
```

### 5. Finding Alternatives for EOL Parts
```bash
/find-parts "alternative for TL072" --source all
```

## Future Enhancements

### Planned Features
- **BOM Optimization**: Upload entire BOM for multi-source optimization
- **Price Alerts**: Notify when components drop in price
- **Availability Tracking**: Monitor stock levels over time
- **Lead Time Estimates**: Shipping time calculations
- **Currency Conversion**: Display prices in local currency
- **Parametric Search**: Filter by electrical specifications

### Planned Suppliers
- Mouser Electronics
- LCSC
- Arrow Electronics  
- Newark/Farnell
- RS Components
- Octopart (meta-search)
- AliExpress (for hobby projects)

This unified command provides a single interface for all component sourcing needs, making it easy to find the best parts regardless of supplier.