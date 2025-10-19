---
name: component-search
description: Fast JLCPCB component search with caching for sourcing parts
allowed-tools: ["Bash", "Read", "Write"]
---

# Component Search Skill

## When to Use This Skill

Invoke this skill when the user:
- Asks about component availability: "find on JLCPCB", "is X in stock", "JLCPCB parts"
- Searches for components: "find resistor", "search for capacitor", "10k resistor"
- Needs pricing: "how much", "price for", "cost of"
- Mentions LCSC part numbers: "C12345", "LCSC C"
- Asks about alternatives: "similar to", "replacement for"

## Capabilities

### Component Search
- Search JLCPCB catalog for components
- Find by manufacturer part number (e.g., "AMS1117-3.3")
- Find by generic description (e.g., "10k resistor 0603")
- Find by LCSC part number (e.g., "C8281")

### Pricing & Availability
- Real-time stock levels
- Pricing at quantity breaks (1, 10, 100+)
- Basic vs Extended part classification
- In-stock filtering

### Smart Recommendations
- Rank by availability (prefer in-stock)
- Rank by price (cheapest first)
- Prefer Basic parts (no setup fee)
- Filter by package type (0603, 0805, SOT-223, etc.)

## Usage Examples

### Example 1: Find Generic Component
**User:** "find a 10k resistor on JLCPCB"

**Process:**
1. Use circuit-synth's FastJLCSearch
2. Search for "10k resistor" with filters
3. Rank by: Basic parts > In stock > Cheapest
4. Return top 3 matches

**Output:**
```
Found 10k resistors on JLCPCB:

1. C25804 - 10kΩ 0603 ±1% (Basic Part)
   Stock: 157,420
   Price: $0.0008 (qty 1), $0.0006 (qty 100)

2. C25744 - 10kΩ 0805 ±1% (Basic Part)
   Stock: 89,341
   Price: $0.001 (qty 1), $0.0007 (qty 100)

Recommended: C25804 (0603 size, cheapest, high stock)
```

### Example 2: Find Specific Part
**User:** "search JLCPCB for AMS1117-3.3"

**Process:**
1. Search by manufacturer part number
2. Find exact matches
3. Show alternatives if available

**Output:**
```
Found AMS1117-3.3 voltage regulator:

C6186 - AMS1117-3.3 (SOT-223)
Manufacturer: Advanced Monolithic Systems
Stock: 12,450
Price: $0.0485 (qty 1), $0.0262 (qty 100)
Type: Basic Part

Perfect for 3.3V LDO regulation up to 1A.
```

### Example 3: Check Stock
**User:** "is C8281 available on JLCPCB?"

**Process:**
1. Look up LCSC part number directly
2. Check stock status
3. Return availability

**Output:**
```
C8281 - AMS1117-3.3 (SOT-223)
✓ In Stock: 12,450 units
Price: $0.0485 (qty 1)
Type: Basic Part (no setup fee)

Ready to manufacture!
```

## Search Strategy

### Step 1: Parse Query
Extract:
- Component type (resistor, capacitor, voltage regulator)
- Value/specs (10k, 3.3V, 0603)
- Manufacturer part (if specified)
- LCSC part number (if specified)

### Step 2: Execute Search
```python
from circuit_synth.manufacturing.jlcpcb import find_component

# Example search
results = find_component(
    query="10k resistor 0603",
    max_results=5,
    prefer_basic=True,
    in_stock_only=True
)
```

### Step 3: Rank Results
Priority:
1. Exact manufacturer part match
2. Basic parts (no setup fee)
3. In stock
4. Lowest price
5. Highest stock

### Step 4: Format Output
- Show top 3 matches
- Include LCSC part number, description, stock, price
- Recommend best option with justification

## Integration with Existing Code

This skill leverages circuit-synth's JLCPCB integration:

```python
# Available functions (already in circuit-synth)
from circuit_synth.manufacturing.jlcpcb import (
    find_component,           # Smart search
    fast_jlc_search,         # Fast search
    find_cheapest_jlc,       # Price-optimized
    find_most_available_jlc, # Stock-optimized
    get_jlcpcb_cache,        # Caching
)
```

## Caching Strategy

Uses circuit-synth's `JLCPCBCache`:
- Caches search results locally
- Cache TTL: 7 days for stock/price data
- Cache stored in: `~/.circuit_synth/jlcpcb_cache.json`
- Reduces API calls and speeds up searches

## Performance

- **Cache Hit**: <1 second
- **Cache Miss**: 3-10 seconds (web scraping)
- **Token Usage**: ~300 tokens per search
- **Cache Hit Rate**: Target 70%+

## Common Component Queries

**Passives:**
- "10k resistor 0603"
- "10uF capacitor 0805"
- "LED 0603 red"

**Regulators:**
- "3.3V LDO regulator"
- "AMS1117-3.3"
- "buck converter 5V to 3.3V"

**Microcontrollers:**
- "STM32F411"
- "ESP32-C3"
- "RP2040"

**Connectors:**
- "USB-C connector"
- "pin header 2.54mm"
- "JST connector"

## Basic vs Extended Parts

**Basic Parts:**
- No setup fee ($0)
- Limited selection
- Lower MOQ (often 5 units)
- Recommended for prototypes

**Extended Parts:**
- $3 setup fee per unique part
- Full LCSC catalog
- May have higher MOQ
- Use when Basic parts don't fit

Skill prioritizes Basic parts automatically.

## Error Handling

**Component Not Found:**
```
No results for "XYZ123"
Suggestions:
- Check part number spelling
- Try generic description instead
- Search manufacturer website for alternates
```

**API Rate Limit:**
```
JLCPCB API rate limit reached.
Using cached results from [timestamp]
Note: Stock/price may be slightly outdated.
```

**Network Error:**
```
Cannot connect to JLCPCB.
Using cached results (if available).
Try again in a few moments.
```

## Limitations

- Requires internet connection (unless cache hit)
- Stock/price data may lag (up to 7 days if cached)
- Web scraping may break if JLCPCB site changes
- No access to extended specifications (datasheets, etc.)

## Related Skills

- **kicad-integration**: Use component-search → find symbol/footprint
- **circuit-patterns**: Use component-search → fill pattern with real parts

## Best Practices

### Prefer Specific Queries
✅ "10k 0603 resistor 1%"
❌ "resistor"

### Use Manufacturer Parts When Possible
✅ "AMS1117-3.3"
❌ "voltage regulator"

### Consider Package Size
✅ "0805 capacitor" (hand-solderable)
❌ "capacitor" (may get 0201 or other tiny packages)

## Example Workflow

**User wants to design a circuit:**
1. "find 10k resistor on JLCPCB" → component-search skill
2. Returns: C25804
3. "find symbol for resistor" → kicad-integration skill
4. Returns: Device:R
5. User creates circuit with known-good parts

This ensures all components are:
- Available on JLCPCB
- Have valid KiCad symbols
- Ready for manufacturing
