# Dynamic Example Updates Architecture

## Core Concept: Production-Ready Examples

Update circuit examples based on real-time component availability and verified KiCad compatibility.

## Key Questions to Explore

### 1. Update Frequency & Dynamics
- **Daily Updates**: Automated script runs daily to update examples with current stock
- **Simple Caching**: Python library checks daily for new examples
- **Fast Fallback**: Use bundled examples if website unavailable

### 2. Component Selection Priority Order
1. **Stock Level**: Must be in stock (>100 units preferred)
2. **Pin Count**: Moderate complexity (32-100 pins ideal for learning)
3. **Package Type**: Easy to solder packages prioritized:
   - LQFP > TQFP > QFN > BGA (avoid BGA completely)
   - 0.5mm pitch preferred over 0.4mm
4. **Functional Equivalents**: Handle substitutions (NCP1117 ↔ AMS1117)

Note: JLCPCB stock is global (no regional variations)

### 3. KiCad Footprint Validation
- **Current Check**: Parse KiCad libraries for footprint existence
- **Future Enhancement**: How to source/generate missing footprints?
- **Version Compatibility**: Different KiCad versions have different libraries
- **Custom Footprints**: When to create vs when to substitute?

### 4. Hosting Architecture
```
Website: examples.circuit-synth.io
├── /examples/
│   ├── power/01_basic_ldo_3v3.py          # Updated with in-stock parts
│   ├── microcontrollers/01_esp32.py       # Current ESP32-S3 variant in stock
│   └── [all examples...]
├── /metadata/
│   ├── component_availability.json        # JLCPCB stock levels
│   ├── kicad_compatibility.json          # Verified footprint availability
│   └── last_updated.json                 # Update timestamps
└── /api/
    ├── /check_availability/{component}    # Real-time stock check
    └── /get_examples/{domain}             # Fetch latest examples
```

### 5. Python Library Integration
```python
# Simple API in circuit-synth library
from circuit_synth.examples import get_latest_examples

# Downloads fresh examples from website
examples = get_latest_examples("power")  # Gets latest LDO with in-stock parts
examples = get_latest_examples("all")    # Full download for offline use
```

### 6. Fallback Strategy
- **Website Down**: Use bundled examples as fallback
- **API Limits**: Cache responses locally with TTL
- **No Stock**: Provide alternatives or warn user about availability