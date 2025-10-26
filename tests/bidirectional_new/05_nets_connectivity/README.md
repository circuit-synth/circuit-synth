# Test 05: Nets & Connectivity - Connection Integrity

**Priority:** P1 (Core Functionality)
**Category:** Foundation
**Tests:** 8 total
**Status:** In Development

## Overview

Tests net creation, connectivity preservation, and electrical connections through bidirectional sync.

This test suite validates that:
- Nets (electrical connections) created correctly in Python
- Net connections extracted from KiCad accurately
- Connection integrity preserved through round-trip
- Multi-node nets (3+ connections) handled properly
- No spurious connections or missing nets
- Net names preserved when specified

## Test Cases

### Test 5.1: Generate Single Net to KiCad
**What:** Python circuit with VCC and GND nets generates correctly
**Validates:** Basic net creation and routing

### Test 5.2: Import Nets from KiCad
**What:** KiCad project with connected components imports nets correctly
**Validates:** Net extraction and naming

### Test 5.3: Multi-Node Net Preservation
**What:** Net connected to 3+ component pins preserved
**Validates:** Complex net topology handling

### Test 5.4: Net Round-Trip Stability
**What:** Net connections survive full round-trip cycle
**Validates:** Connection integrity maintained

### Test 5.5: Multiple Nets Independence
**What:** Multiple independent nets don't interfere
**Validates:** Net isolation and independence

### Test 5.6: Named Nets Preservation
**What:** Custom net names (VCC, GND, SIGNAL) preserved
**Validates:** Net naming convention support

### Test 5.7: Unconnected Components
**What:** Components without nets handled properly
**Validates:** Partial circuit support

### Test 5.8: Net Connectivity Verification
**What:** Net connectivity matches schematic connections
**Validates:** Electrical correctness

## Related Tests

- **Previous:** 04_multiple_components
- **Parallel:** 03_position_preservation (position + connectivity)
