# Component Search Skill

Fast JLCPCB component search with caching for sourcing parts.

## Quick Start

Just ask naturally:
- "find a 10k resistor on JLCPCB"
- "search for AMS1117-3.3"
- "is C8281 available?"
- "how much does a USB-C connector cost?"

Claude will automatically invoke this skill and search JLCPCB's catalog.

## What This Skill Does

**Component Search:**
- Searches JLCPCB catalog for components
- Finds by manufacturer part number (e.g., "AMS1117-3.3")
- Finds by generic description (e.g., "10k resistor 0603")
- Finds by LCSC part number (e.g., "C8281")

**Pricing & Availability:**
- Real-time stock levels
- Pricing at quantity breaks (1, 10, 100+)
- Basic vs Extended part classification
- In-stock filtering

**Smart Recommendations:**
- Ranks by availability (prefers in-stock)
- Ranks by price (cheapest first)
- Prefers Basic parts (no setup fee)
- Filters by package type when specified

## Example Usage

### Finding a Generic Component
```
You: "find a 10k resistor on JLCPCB"

Claude (via skill):
Found 10k resistors on JLCPCB:

1. C25804 - 10kΩ 0603 ±1% (Basic Part)
   Stock: 157,420
   Price: $0.0008 (qty 1), $0.0006 (qty 100)

2. C25744 - 10kΩ 0805 ±1% (Basic Part)
   Stock: 89,341
   Price: $0.001 (qty 1), $0.0007 (qty 100)

Recommended: C25804 (0603 size, cheapest, high stock)
```

### Finding a Specific Part
```
You: "search JLCPCB for AMS1117-3.3"

Claude (via skill):
Found AMS1117-3.3 voltage regulator:

C6186 - AMS1117-3.3 (SOT-223)
Manufacturer: Advanced Monolithic Systems
Stock: 12,450
Price: $0.0485 (qty 1), $0.0262 (qty 100)
Type: Basic Part

Perfect for 3.3V LDO regulation up to 1A.
```

### Checking Stock
```
You: "is C8281 available on JLCPCB?"

Claude (via skill):
C8281 - AMS1117-3.3 (SOT-223)
✓ In Stock: 12,450 units
Price: $0.0485 (qty 1)
Type: Basic Part (no setup fee)

Ready to manufacture!
```

## Common Components

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
- Limited selection (~1000 parts)
- Lower MOQ (often 5 units)
- Recommended for prototypes

**Extended Parts:**
- $3 setup fee per unique part
- Full LCSC catalog (~500K parts)
- May have higher MOQ
- Use when Basic parts don't fit requirements

This skill automatically prioritizes Basic parts.

## Caching

- **Cache Hit**: <1 second (instant results)
- **Cache Miss**: 3-10 seconds (web scraping JLCPCB)
- **Cache TTL**: 7 days for stock/price data
- **Cache Location**: `~/.circuit_synth/jlcpcb_cache.json`

The cache dramatically speeds up repeated searches.

## Performance

- Symbol search: <1 second (cached)
- Symbol search: 3-10 seconds (uncached)
- Token usage: ~300 tokens per search
- Target cache hit rate: 70%+

## Invocation

This skill is **automatically invoked** when you mention:
- "JLCPCB", "LCSC", "C-number" (e.g., C8281)
- "find", "search", "available", "in stock"
- "price", "cost", "how much"
- Component types: "resistor", "capacitor", "regulator", etc.

No need to explicitly call it - just ask naturally!

## Limitations

- Requires internet connection (unless cache hit)
- Stock/price data may be up to 7 days old if cached
- Web scraping may break if JLCPCB site changes
- No access to extended specifications (datasheets, parametric search)

## Related

- See `SKILL.md` for complete technical details
- Uses circuit-synth's existing JLCPCB integration code
- Complements `kicad-integration` skill for complete design workflow

## Example Workflow

**Designing a circuit with known-good parts:**
1. "find 10k resistor on JLCPCB" → component-search skill → Returns: C25804
2. "find symbol for resistor" → kicad-integration skill → Returns: Device:R
3. Use C25804 in circuit with Device:R symbol
4. Generate circuit knowing all parts are available and manufacturable

This ensures your design uses only verified, in-stock components.
