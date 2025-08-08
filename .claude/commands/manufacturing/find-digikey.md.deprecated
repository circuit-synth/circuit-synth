# Find DigiKey Components

**Command**: `/find-digikey <component_description>`

**Purpose**: Search DigiKey's extensive catalog for components with real-time pricing, availability, and KiCad compatibility verification.

## Usage Examples

```bash
# Find specific components
/find-digikey 0.1uF 0603 X7R capacitor
/find-digikey STM32F407VGT6
/find-digikey LM358 op-amp SOIC-8

# Find with requirements
/find-digikey 10k resistor 1% 0603
/find-digikey 3.3V regulator 1A LDO
/find-digikey USB-C connector through-hole

# Find alternatives
/find-digikey alternatives for AMS1117-3.3
/find-digikey replacement for discontinued TL072
```

## Search Capabilities

### Component Categories
- **Passives**: Resistors, capacitors, inductors with full specifications
- **Semiconductors**: Diodes, transistors, MOSFETs, ICs
- **Connectors**: USB, headers, terminal blocks, RF connectors
- **Power**: Regulators, references, power management ICs
- **Microcontrollers**: STM32, ESP32, PIC, AVR, Nordic
- **Sensors**: Temperature, pressure, motion, optical
- **Discrete**: LEDs, crystals, switches, relays

### Search Parameters
- **Specifications**: Value, tolerance, voltage, current ratings
- **Package**: SMD sizes (0402-2512), through-hole, modules
- **Temperature**: Operating range, temperature coefficient
- **Brand**: Manufacturer preferences and alternatives

### Pricing Information
- **Price Breaks**: Volume discounts from 1 to 10,000+ pieces
- **Stock Levels**: Real-time availability
- **Lead Times**: In-stock vs. factory order
- **Minimum Order**: Cut tape, full reel, or minimum quantities

## Output Format

```
🔍 DigiKey Search Results for: "0.1uF 0603 X7R capacitor"

✅ 399-1096-1-ND - Best Match
📦 KEMET C0603C104K3RACTU
📊 Stock: 234,879 units | MOQ: 1 (Cut Tape)
💰 Pricing: $0.10@1 | $0.024@100 | $0.012@1000
⚡ Specs: 0.1µF ±10% 25V X7R 0603

🎯 KiCad Integration:
Symbol: "Device:C" ✅ Verified
Footprint: "Capacitor_SMD:C_0603_1608Metric" ✅ Available

📋 Circuit-Synth Code:
```python
cap = Component(
    symbol="Device:C",
    ref="C",
    value="0.1uF",
    footprint="Capacitor_SMD:C_0603_1608Metric",
    properties={
        "Manufacturer": "KEMET",
        "MPN": "C0603C104K3RACTU",
        "DigiKey_PN": "399-1096-1-ND",
        "Unit_Price": "$0.024@100"
    }
)
```

🔄 Alternative Options:
1. 399-1280-1-ND: Murata GRM188R71E104KA01D | 189k stock | $0.023@100
2. 490-1532-1-ND: Samsung CL10B104KB8NNNC | 156k stock | $0.021@100
3. 311-1341-1-ND: Yageo CC0603KRX7R9BB104 | 98k stock | $0.019@100

📊 Price Break Analysis:
| Qty    | Price/Unit | Total   | Savings |
|--------|------------|---------|---------|
| 1-9    | $0.100     | $0.10   | -       |
| 10-99  | $0.024     | $0.24   | 76%     |
| 100+   | $0.019     | $1.90   | 81%     |
| 1000+  | $0.012     | $12.00  | 88%     |

🔗 Datasheet: https://api.kemet.com/component-docs/C0603C104K3RACTU
```

## Search Implementation

### Python Integration
```python
from circuit_synth.manufacturing.digikey import search_digikey_components

# Quick search
results = search_digikey_components(
    keyword="0.1uF 0603 X7R",
    max_results=10,
    in_stock_only=True
)

# Detailed search with component object
from circuit_synth.manufacturing.digikey import DigiKeyComponentSearch

searcher = DigiKeyComponentSearch()
components = searcher.search_components(
    keyword="STM32F407",
    max_results=5,
    in_stock_only=True
)

# Get full details
for comp in components:
    details = searcher.get_component_details(comp.digikey_part_number)
    alternatives = searcher.find_alternatives(comp, max_results=3)
```

### Advanced Features

#### Find Alternatives
```python
# Find drop-in replacements
def find_component_alternatives(original_part):
    searcher = DigiKeyComponentSearch()
    
    # Get original component details
    original = searcher.get_component_details(original_part)
    
    # Find alternatives with same specs
    alternatives = searcher.find_alternatives(
        reference_component=original,
        max_results=10
    )
    
    return alternatives
```

#### Price Optimization
```python
# Analyze price breaks for BOM optimization
def optimize_bom_pricing(components, target_quantity):
    total_cost = 0
    optimized_bom = []
    
    for comp in components:
        # Find best price break
        best_price = find_best_price_break(comp, target_quantity)
        
        # Check for alternative with better pricing
        alternatives = searcher.find_alternatives(comp)
        for alt in alternatives:
            alt_price = find_best_price_break(alt, target_quantity)
            if alt_price < best_price:
                comp = alt
                best_price = alt_price
        
        optimized_bom.append({
            "component": comp,
            "unit_price": best_price,
            "total": best_price * target_quantity
        })
        total_cost += best_price * target_quantity
    
    return optimized_bom, total_cost
```

## Integration Benefits

### Compared to Manual Search
- **10x Faster**: API search vs. manual website navigation
- **Complete Data**: All specs, pricing, and availability in one call
- **KiCad Ready**: Pre-verified symbols and footprints
- **Automated Alternatives**: Instant replacement suggestions

### Design Advantages
- **Real Availability**: Live stock data prevents using out-of-stock parts
- **Price Transparency**: See all price breaks upfront
- **Quality Parts**: Only authorized distributors, no counterfeits
- **Technical Docs**: Direct links to datasheets and app notes

### Manufacturing Benefits
- **No Minimums**: Most parts available in single quantities
- **Fast Shipping**: Same-day shipping for in-stock items
- **Traceability**: Date/lot codes for all components
- **Global Availability**: Ships worldwide

## Configuration

### API Setup
```bash
# Configure DigiKey API credentials
python -m circuit_synth.manufacturing.digikey.config_manager

# Test connection
python -m circuit_synth.manufacturing.digikey.test_connection
```

### Environment Variables
```bash
export DIGIKEY_CLIENT_ID="your_client_id"
export DIGIKEY_CLIENT_SECRET="your_client_secret"
export DIGIKEY_CLIENT_SANDBOX="False"  # Use production API
```

### Cache Management
```python
from circuit_synth.manufacturing.digikey import DigiKeyCache

cache = DigiKeyCache()

# View cache statistics
stats = cache.get_cache_stats()
print(f"Cache size: {stats['total_size_mb']:.2f} MB")
print(f"Cached searches: {stats['search_cache']['valid_files']}")

# Clear old cache if needed
cache.clear_cache("search")  # Clear search cache
cache.clear_cache("product")  # Clear product cache
```

## Common Use Cases

### 1. Finding Decoupling Capacitors
```bash
/find-digikey 0.1uF 0603 X7R 16V ceramic capacitor
```

### 2. Sourcing Power Regulators
```bash
/find-digikey 3.3V 1A LDO regulator SOT-223
```

### 3. Selecting Pull-up Resistors  
```bash
/find-digikey 10k resistor 5% 0603 
```

### 4. Finding Connectors
```bash
/find-digikey USB-C receptacle SMD 16-pin
```

### 5. Microcontroller Selection
```bash
/find-digikey STM32F4 100-pin LQFP ARM Cortex-M4
```

This command provides instant access to DigiKey's 8+ million component catalog with real-time pricing and availability, making component selection fast and reliable.